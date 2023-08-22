import logging
import os, sys
import pandas as pd
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from domain_detection.exception import CustomException
from dotenv import find_dotenv, load_dotenv
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)




class AstraDBConnector:
    def __init__(self):
        try:
            # Set your Astra DB credentials
            self.username = os.getenv("ASTRA_USERNAME")
            self.password = os.getenv("ASTRA_PASSWORD")
            self.keyspace = os.getenv("KEYSPACE")
            self.secure_bundle_path = os.getenv("SECURE_CONNECTION_BUNDLE_PATH")

            # Establish a connection to the Cassandra cluster
            self.cluster = None
            self.session = None
            self.connect()

        except Exception as e:
            raise CustomException(e, sys)

    def connect(self):
        if self.cluster is None:
            auth_provider = PlainTextAuthProvider(username=self.username, password=self.password)
            cloud_config = {
                'secure_connect_bundle': self.secure_bundle_path,
            }
            self.cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
            self.session = self.cluster.connect(self.keyspace)
            logging.info("We are connected with astra db")


    def execute_query(self, query):
        result = self.session.execute(query)
        return result

    def close_connection(self):
        if self.cluster is not None:
            self.session.shutdown()
            self.cluster.shutdown()
            self.cluster = None
            self.session = None

    def fetch_data(self, query):
        try:
            # Execute the query and get the result
            result = self.execute_query(query)

            # Convert result to a DataFrame
            df = pd.DataFrame(result)

            return df
        except Exception as e:
            raise CustomException(e, sys)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close_connection()
        # If there was an exception within the 'with' block, handle it here (if needed).
        if exc_type is not None:
            # You can log the exception or perform any other cleanup/handling as required.
            logging.error("An exception occurred within the 'with' block:")
            logging.error(f"Exception type: {exc_type}")
            logging.error(f"Exception value: {exc_value}")
            logging.error(f"Traceback: {traceback}")
