from io import BytesIO
import os
import csv
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError
from dotenv import load_dotenv
import joblib
import numpy as np
import pandas as pd
from app.logFile import logger

load_dotenv()
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = "alternanceproduction" 


class BlobService:
    """
    A service class for interacting with Azure Blob Storage.
    """

    def __init__(self):
        """
        Initialize the BlobService with Azure Blob Storage client.
        """
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
            self.container_client = self.blob_service_client.get_container_client(CONTAINER_NAME)
            self.ensure_container_exists()
        except AzureError as e:
            logger.exception("Error initializing BlobService")
            raise

    def ensure_container_exists(self):
        """
        Ensure that the specified container exists, create it if it doesn't.
        """
        try:
            if not self.container_client.exists():
                self.container_client.create_container()
                logger.info(f"Container '{CONTAINER_NAME}' created.")
            else:
                logger.info(f"Container '{CONTAINER_NAME}' already exists.")
        except AzureError as e:
            logger.exception("Error ensuring container exists")
            raise

    def delete_blob(self, blob_path: str):
        """
        Delete a file (blob) from Azure Blob Storage.

        Args:
            blob_path (str): The path of the blob to delete.

        Raises:
            Exception: If an error occurs during deletion.
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            blob_client.delete_blob()
            logger.info(f"Blob {blob_path} deleted successfully.")
        except AzureError as e:
            logger.exception(f"Error deleting blob {blob_path}")
            raise
        except Exception as e:
            logger.exception("Unexpected error deleting blob")

    def upload_file(self, file_path: str, blob_path: str):
        """
        Upload a file to Azure Blob Storage.

        Args:
            file_path (str): The local path of the file to upload.
            blob_path (str): The destination path in the blob storage.

        Raises:
            Exception: If there's an error during the upload process.
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            logger.info(f"Uploaded {file_path} to {blob_path}.")
        except AzureError as e:
            logger.exception(f"Error uploading file {file_path} to blob storage")
            raise
        except IOError as e:
            logger.exception(f"Error reading file {file_path}")
            raise

    def download_file(self, blob_path: str, download_path: str):
        """
        Download a file from Azure Blob Storage.

        Args:
            blob_path (str): The path of the blob to download.
            download_path (str): The local path to save the downloaded file.

        Raises:
            Exception: If there's an error during the download process.
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            with open(download_path, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
            logger.info(f"Downloaded {blob_path} to {download_path}.")
        except AzureError as e:
            logger.exception(f"Error downloading file {blob_path} from blob storage")
            raise
        except IOError as e:
            logger.exception(f"Error writing to file {download_path}")
            raise
    
    def get_csv_content(self, blob_path: str) -> str:
        """
        Retrieve the content of a CSV file from Azure Blob Storage as a string.

        Args:
            blob_path (str): The path of the blob (CSV file) in the storage.

        Returns:
            str: The content of the CSV file as a string.
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            csv_data = blob_client.download_blob().readall()
            return csv_data.decode('utf-8') 
        except AzureError as e:
            logger.exception(f"Error retrieving CSV content from blob {blob_path}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error retrieving CSV content")

    def save_to_csv(self, job_posts, filename: str, site_name: str, is_summarize: bool = False):
        """
        Save job postings to a CSV file and upload it to blob storage.

        Args:
            job_posts (list): List of job postings to save.
            filename (str): Name of the CSV file.
            site_name (str): Name of the job site.
            is_summarize (bool): Indicates whether to save the file in the 'summarize' directory.
        """
        # Determine the blob path based on the is_summarize parameter
        blob_path = f"temp/summarize/{site_name}/{filename}" if is_summarize else f"firstscraping/{site_name}/{filename}"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = list(job_posts[0].keys()) if job_posts else []
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for job in job_posts:
                    writer.writerow(job)

            self.upload_file(filename, blob_path)
        except IOError as e:
            logger.exception("Error writing to CSV file")
        except Exception as e:
            logger.exception("Error uploading to blob storage")
        finally:
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except OSError as e:
                    logger.exception("Error removing temporary file")


    def upload_blob_from_bytes(self, data: bytes, blob_path: str):
        """
        Upload bytes data to Azure Blob Storage.

        Args:
            data (bytes): The bytes data to upload.
            blob_path (str): The destination path in the blob storage.

        Raises:
            Exception: If there's an error during the upload process.
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            blob_client.upload_blob(data, overwrite=True)
            logger.info(f"Uploaded data to {blob_path}.")
        except AzureError as e:
            logger.exception(f"Error uploading data to blob storage")
            raise

    def download_blob_to_bytes(self, blob_path: str) -> bytes:
        """
        Download a blob from Azure Blob Storage as bytes.

        Args:
            blob_path (str): The path of the blob to download.

        Returns:
            bytes: The content of the blob as bytes.

        Raises:
            Exception: If there's an error during the download process.
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            return blob_client.download_blob().readall()
        except AzureError as e:
            logger.exception(f"Error downloading blob {blob_path} from storage")
            raise
    

    def test_delete_blob(self, blob_path: str):
        """
        Delete a file locally.

        Args:
            blob_path (str): The path of the file to delete.

        Raises:
            Exception: If an error occurs during deletion.
        """
        try:
            # Check if the file exists
            if os.path.exists(blob_path):
                os.remove(blob_path)  # Delete the file
                logger.info(f"File {blob_path} deleted successfully.")
            else:
                logger.warning(f"File {blob_path} does not exist.")
        except Exception as e:
            logger.exception(f"Unexpected error deleting file")
            raise
    
    ##
    def save_model_data(self, platform: str, region: str, model_data: dict):
        """
        Save model data to Azure Blob Storage using joblib.

        Args:
            platform (str): The platform name (e.g., 'linkedin', 'indeed').
            region (str): The region name (e.g., 'hauts_de_france', 'ile_de_france').
            model_data (dict): A dictionary containing model data to save.

        Raises:
            Exception: If there's an error during the save process.
        """
        try:
            base_path = f"temp/clustering_results/{platform}/{region}"

            # Save KMeans model
            kmeans_blob = f"{base_path}/kmeans_model.pkl"
            kmeans_buffer = BytesIO() 
            joblib.dump(model_data['kmeans_model'], kmeans_buffer) 
            kmeans_buffer.seek(0)  
            self.upload_blob_from_bytes(kmeans_buffer, kmeans_blob)  

            # Save numpy arrays
            for array_name in ['cluster_centers', 'paragraph_embeddings', 'labels']:
                array_blob = f"{base_path}/{array_name}.npy"
                array_buffer = BytesIO()  
                np.save(array_buffer, model_data[array_name]) 
                array_buffer.seek(0)  
                self.upload_blob_from_bytes(array_buffer, array_blob)  

            # Save cleaned data CSV
            csv_blob = f"{base_path}/{platform}_{region}.csv"
            csv_buffer = BytesIO() 
            model_data['data_cleaned'].to_csv(csv_buffer, index=False) 
            csv_buffer.seek(0)  
            self.upload_blob_from_bytes(csv_buffer, csv_blob) 

            # Save supervised models
            for model_name, model in model_data['supervised_models'].items():
                model_blob = f"{base_path}/{model_name}_model.pkl"
                model_buffer = BytesIO()  
                joblib.dump(model, model_buffer)  
                model_buffer.seek(0)  
                self.upload_blob_from_bytes(model_buffer, model_blob)  

            logger.info(f"Model data saved for {platform} - {region}")
        except Exception as e:
            logger.exception(f"Error saving model data for {platform} - {region}")
            raise


    def retrieve_model_data(self, platform: str, region: str):
        """
        Retrieve model data from Azure Blob Storage using joblib.

        Args:
            platform (str): The platform name (e.g., 'linkedin', 'indeed').
            region (str): The region name (e.g., 'hauts_de_france', 'ile_de_france').

        Returns:
            dict: A dictionary containing the retrieved model data.

        Raises:
            Exception: If there's an error during the retrieval process.
        """
        try:
            base_path = f"clustering_results/{platform}/{region}"
            model_data = {}

            # Retrieve KMeans model
            kmeans_blob = f"{base_path}/kmeans_model.pkl"
            kmeans_bytes = self.download_blob_to_bytes(kmeans_blob)
            model_data['kmeans_model'] = joblib.load(BytesIO(kmeans_bytes))

            # Retrieve numpy arrays
            for array_name in ['cluster_centers', 'paragraph_embeddings', 'labels']:
                array_blob = f"{base_path}/{array_name}.npy"
                array_bytes = self.download_blob_to_bytes(array_blob)
                model_data[array_name] = np.load(BytesIO(array_bytes))

            # Retrieve cleaned data CSV
            csv_blob = f"{base_path}/{platform}_{region}.csv"
            csv_bytes = self.download_blob_to_bytes(csv_blob)
            model_data['data_cleaned'] = pd.read_csv(BytesIO(csv_bytes))

            # Retrieve supervised models
            model_data['supervised_models'] = {}
            for model_name in ['RandomForest', 'SVM', 'LogisticRegression', 'KNN', 'GradientBoosting']:
                model_blob = f"{base_path}/{model_name}_model.pkl"
                model_bytes = self.download_blob_to_bytes(model_blob)
                model_data['supervised_models'][model_name] = joblib.load(BytesIO(model_bytes))

            logger.info(f"Model data retrieved for {platform} - {region}")
            return model_data
        except Exception as e:
            logger.exception(f"Error retrieving model data for {platform} - {region}")
            raise

    
    def finalize_summarize_process(self, platform, region):
        """
        Finalize the summarize process by moving the temporary files to the final destination.
        """
        temp_path = f"temp/summarize/{platform}/{region}.csv"
        final_path = f"summarize/{platform}/{region}.csv"

        try:
            csv_content = self.download_blob_to_bytes(temp_path)

            if not csv_content:
                logger.error(f"Failed to retrieve content for {temp_path}. Cannot finalize.")
                return False

            # Move the temporary file to the final destination
            self.upload_blob_from_bytes(csv_content, final_path)
            logger.info(f"Summarized file moved from {temp_path} to {final_path}")

            # Delete the temporary file
            self.delete_blob(temp_path)
            logger.info(f"Temporary file {temp_path} deleted")
            return True
        except Exception as e:
            logger.exception(f"Error finalizing summarize process for {platform} - {region}")
            return False
    
    def finalize_model_data_transfer(self, platform: str, region: str):
        """
        Transfer model data from temporary Azure storage to final destination in Azure.
        Similar to finalize_summarize_process but for model data.

        Args:
            platform (str): The platform name (e.g., 'linkedin', 'indeed').
            region (str): The region name (e.g., 'hauts_de_france', 'ile_de_france').

        Returns:
            bool: True if the process was successful, False otherwise.
        """
        try:
            # Define paths
            temp_base_path = f"temp/clustering_results/{platform}/{region}"
            final_base_path = f"clustering_results/{platform}/{region}"

            # Files to transfer
            files = {
                'kmeans_model.pkl': 'kmeans_model.pkl',
                'cluster_centers.npy': 'cluster_centers.npy',
                'paragraph_embeddings.npy': 'paragraph_embeddings.npy',
                'labels.npy': 'labels.npy',
                f'{platform}_{region}.csv': f'{platform}_{region}.csv'
            }

            # Add supervised models to the files dict
            for model_name in ['RandomForest', 'SVM', 'LogisticRegression', 'KNN', 'GradientBoosting']:
                model_file = f'{model_name}_model.pkl'
                files[model_file] = model_file

            # Transfer each file
            for temp_file, final_file in files.items():
                temp_path = f"{temp_base_path}/{temp_file}"
                final_path = f"{final_base_path}/{final_file}"

                # Download content from temp location
                try:
                    file_content = self.download_blob_to_bytes(temp_path)
                    
                    # Upload to final location
                    self.upload_blob_from_bytes(file_content, final_path)
                    logger.info(f"Transferred {temp_file} to final location")

                    # Delete temp file
                    self.delete_blob(temp_path)
                    logger.info(f"Deleted temporary file {temp_path}")

                except Exception as e:
                    logger.error(f"Error processing file {temp_file}: {str(e)}")
                    continue

            logger.info(f"Model data transfer completed for {platform} - {region}")
            return True

        except Exception as e:
            logger.exception(f"Error finalizing model data transfer for {platform} - {region}")
            return False