# Install or update needed software
apt-get update
apt-get install -yq git supervisor python3 python3-pip python3-distutils postgresql-client
pip install --upgrade pip virtualenv

# Fetch source code
export HOME=/root

git clone -b hamza/deploy-on-gce https://github.com/hamza-56/postgres-manage-python.git /opt/app

# Install Cloud Ops Agent
sudo bash /opt/app/gce/add-google-cloud-ops-agent-repo.sh --also-install

# Account to own server process
useradd -m -d /home/pythonapp pythonapp

# Python environment setup
virtualenv -p python3 /opt/app/env
/bin/bash -c "source /opt/app/env/bin/activate"
/opt/app/env/bin/pip install -r /opt/app/requirements.txt


# Download cloud SQL proxy
curl -o /opt/app/cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
chmod +x /opt/app/cloud_sql_proxy

# Create tmp directory to store downloaded db dump
mkdir /opt/app/tmp

# Set ownership to newly created account
chown -R pythonapp:pythonapp /opt/app

# Put supervisor configuration in proper place
cp /opt/app/gce/python-app.conf /etc/supervisor/conf.d/python-app.conf

# Start service via supervisorctl
supervisorctl reread
supervisorctl update
