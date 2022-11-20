#!/usr/bin/env sh

source ./env/bin/activate

python manage_postgres_db.py --action backup --configfile prod_config.toml --verbose true
python manage_postgres_db.py --action restore --date $(date +%Y%m%d) --configfile staging_config.toml --verbose true
