import logging
logger = logging.getLogger(__name__)

import json

import boto3
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig

from django.db.backends.postgresql import base
from django.db import DEFAULT_DB_ALIAS

from psycopg2 import OperationalError
from ec2_metadata import ec2_metadata


class DatabaseCredentials:
    def __init__(self):
        logger.debug("init secrets manager database credentials")
        session = boto3.session.Session()
        secret_client = session.client('secretsmanager', region_name=ec2_metadata.region)
        rds_client = session.client('rds', region_name=ec2_metadata.region)
        sts_client = session.client('sts', region_name=ec2_metadata.region)
        account_id = sts_client.get_caller_identity()['Account']
        rds_arn = f"arn:aws:rds:{ec2_metadata.region}:{account_id}:db:roombaht"
        self.rds_instance = rds_client \
            .describe_db_instances(DBInstanceIdentifier=rds_arn)['DBInstances'][0]
        cache_config = SecretCacheConfig()
        self.cache_secrets_manager = SecretCache(config=cache_config, client=secret_client)

        self.secret_id=self.rds_instance['MasterUserSecret']['SecretArn']

    def get_conn_params_from_secrets_manager(self, conn_params):
        secret_json = self.cache_secrets_manager.get_secret_string(self.secret_id)
        secret_dict = json.loads(secret_json)
        conn_params['user'] = secret_dict["username"]
        conn_params['password'] = secret_dict["password"]
        conn_params['host'] = self.rds_instance['Endpoint']['Address']

    def refresh_now(self):
        self.cache_secrets_manager.refresh_secret_now(self.secret_id)

databasecredentials=DatabaseCredentials()

class DatabaseWrapper(base.DatabaseWrapper):
    def get_new_connection(self, conn_params):
        try:
            databasecredentials.get_conn_params_from_secrets_manager(conn_params)
            conn = super().get_new_connection(conn_params)
            return conn
        except OperationalError as exp:
            error_code=exp.args[0]
            if error_code!='28P01':
                logger.error("unexpected operational error %s!!", error_code)
                raise exp

            logger.info("Authentication error. Going to refresh secret and try again.")
            databasecredentials.refresh_now()
            databasecredentials.get_conn_params_from_secrets_manager(conn_params)
            conn = super().get_new_connection(conn_params)
            logger.info("Successfully refreshed secret and established new database connection.")
            return conn
