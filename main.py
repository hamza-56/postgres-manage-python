import sys
import time
import logging
import subprocess

import configparser

from flask import Flask

from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash


STAGE_CONFIG_FILE = 'staging_config.toml'
PROD_CONFIG_FILE = 'prod_config.toml'

users = {
    'john': generate_password_hash('hello'),
    'susan': generate_password_hash('bye')
}

app = Flask(__name__)
auth = HTTPBasicAuth()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username


def execute(cmd):
    try:
        retcode = subprocess.call(cmd, shell=True)
        if retcode == 0:
            print('Child returned success', retcode, file=sys.stderr)
            return True
        elif retcode < 0:
            print('Child was terminated by signal', -retcode, file=sys.stderr)
        else:
            print('Child returned', retcode, file=sys.stderr)
    except OSError as e:
        print('Execution failed:', e, file=sys.stderr)
    return False


def start_cloud_sql_proxy(instance_connection_name):
    sql_proxy_process = subprocess.Popen(
        ['./cloud_sql_proxy',
         f'-instances={instance_connection_name}=tcp:5432'],
        stdout=subprocess.PIPE
    )
    time.sleep(5)  # wait for cloud sql proxy to start
    return sql_proxy_process


def run_script(config_file, cmd):
    config = configparser.ConfigParser()
    logger.info(f'Reading config file {config_file}')
    config.read(config_file)

    use_cloudsql_proxy = config.getboolean('postgresql', 'use_cloudsql_proxy')

    success = False

    if use_cloudsql_proxy:
        instance_connection_name = config.get('postgresql', 'instance_connection_name')
        logger.info(f'Starting cloud sql proxy {instance_connection_name}')
        cloud_sql_proxy_process = start_cloud_sql_proxy(instance_connection_name)

    success = execute(cmd)

    if use_cloudsql_proxy:
        logger.info(f'Stopping cloud sql proxy {instance_connection_name}')
        cloud_sql_proxy_process.kill()

    return success


def mirror_prod_to_staging():
    backup_success = run_script(PROD_CONFIG_FILE,
                               f'python manage_postgres_db.py --action backup --configfile {PROD_CONFIG_FILE} --verbose true')
    if backup_success:
        return run_script(STAGE_CONFIG_FILE,
                          f'python manage_postgres_db.py --action restore --date $(date +%Y%m%d) --configfile {STAGE_CONFIG_FILE} --verbose true')


@app.route('/')
@auth.login_required
def index():
    if mirror_prod_to_staging():
        return 'Complete :)'
    return 'Failed :('


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
