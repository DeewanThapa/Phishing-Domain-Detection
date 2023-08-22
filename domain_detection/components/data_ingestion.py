import os, sys
from pandas import DataFrame
from domain_detection.logger import logging
from domain_detection.exception import CustomException
from domain_detection.entity.config_entity import DataIngestionConfig
from domain_detection.utils.main_utils import read_yaml_file
from domain_detection.constant.training_pipeline import SCHEMA_FILE_PATH
from domain_detection.data_access.Astra_DB_Cloud import AstraDBConnector
from domain_detection.entity.artifact_entity import DataIngestionArtifact
from sklearn.model_selection import train_test_split

class DataIngestion:

    def __init__(self,data_ingestion_config:DataIngestionConfig):
        try:
            self.data_ingestion_config=data_ingestion_config
            self._schema_config = read_yaml_file(SCHEMA_FILE_PATH)
        except Exception as e:
            raise CustomException(e, sys)

    def export_data_into_feature_store(self) -> DataFrame:
        try:
            logging.info("Exporting data from AstraDB into feature store")

            # Ensure the folder exists before saving the data
            dir_path = os.path.dirname(self.data_ingestion_config.feature_store_file_path)
            os.makedirs(dir_path, exist_ok=True)

            feature_store_file_path = self.data_ingestion_config.feature_store_file_path
            query = 'SELECT * FROM domain."Phishing_Domain_Detection";'

            # Use context manager for the AstraDBConnector to ensure proper connection management
            with AstraDBConnector() as investment_data:
                dataframe = investment_data.fetch_data(query=query)

            # Save data to CSV file
            dataframe.to_csv(feature_store_file_path, index=False, header=True)

            logging.info("Data has been Exported in Feature store")
            return dataframe
        except Exception as e:
            raise CustomException(e, sys)

    def split_data_as_train_test(self, dataframe: DataFrame) -> None:
        """
        Feature store dataset will be split into train and test file
        """

        try:
            train_set, test_set = train_test_split(
                dataframe, test_size=self.data_ingestion_config.train_test_split_ratio
            )

            logging.info("Performed train test split on the dataframe")

            logging.info(
                "Exited split_data_as_train_test method of Data_Ingestion class"
            )

            dir_path = os.path.dirname(self.data_ingestion_config.training_file_path)

            os.makedirs(dir_path, exist_ok=True)

            logging.info(f"Exporting train and test file path.")

            train_set.to_csv(
                self.data_ingestion_config.training_file_path, index=False, header=True
            )

            test_set.to_csv(
                self.data_ingestion_config.testing_file_path, index=False, header=True
            )

            logging.info(f"Exported train and test file path.")
        except Exception as e:
            raise CustomException(e, sys)

    def initiate_data_ingestion(self) -> DataIngestionArtifact:
        try:
            dataframe = self.export_data_into_feature_store()

            # Check if drop_columns is provided in the configuration
            if self._schema_config["drop_columns"]:
                dataframe = dataframe.drop(self._schema_config["drop_columns"], axis=1)

            self.split_data_as_train_test(dataframe=dataframe)
            data_ingestion_artifact = DataIngestionArtifact(
                trained_file_path=self.data_ingestion_config.training_file_path,
                test_file_path=self.data_ingestion_config.testing_file_path)
            return data_ingestion_artifact
        except Exception as e:
            raise CustomException(e, sys)