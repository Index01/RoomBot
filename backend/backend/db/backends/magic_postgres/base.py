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

    def get_conn_params_from_secrets_manager(self):
        secret_json = self.cache_secrets_manager.get_secret_string(self.secret_id)
        secret_dict = json.loads(secret_json)
        return {
            'user': secret_dict["username"],
            'password': secret_dict["password"],
            'host': self.rds_instance['Endpoint']['Address'],
            'port': 5432
        }

    def refresh_now(self):
        self.cache_secrets_manager.refresh_secret_now(self.secret_id)

databasecredentials=DatabaseCredentials()

class DatabaseWrapper(base.DatabaseWrapper):
    def __init__(self, settings, alias):
        self.conn_params = None
        super().__init__(settings, alias)

    def get_new_connection(self, conn_params):
        self.conn_params = databasecredentials.get_conn_params_from_secrets_manager()
        self.conn_params['database'] = conn_params['database']

        try:
            conn = super().get_new_connection(self.conn_params)
        except OperationalError as exp:
            error_msg=exp.args[0]
            if 'password authentication failed' not in error_msg:
                logger.error("Unexpected operational error %s!!", error_msg)
                raise exp

            logger.info("Authentication error. Going to refresh secret and try again.")
            databasecredentials.refresh_now()
            self.conn_params = databasecredentials.get_conn_params_from_secrets_manager()
            self.conn_params['database'] = conn_params['database']
            conn = super().get_new_connection(self.conn_params)
            logger.info("Successfully refreshed secret and established new database connection.")

        return conn
