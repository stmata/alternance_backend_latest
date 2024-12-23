"""
This module initializes various services for data management, email handling, and analysis.

It imports and instantiates the following services:
- BlobService: A service for managing blob storage operations.
- EmailService: A service for handling email communications.
- DataAnalysisService: A service for performing data analysis tasks.
- UserDataManager: A service for managing user data.
- MongoDBManager: A service for interacting with a MongoDB database.

Instances of these services are created for use throughout the application.

Attributes:
    blob_service (BlobService): An instance of the blob storage service.
    email_service (EmailService): An instance of the email handling service.
    user_data_manager_service (UserDataManager): An instance of the user data management service.
    data_analysis_service (DataAnalysisService): An instance of the data analysis service.
    datamanager_service (MongoDBManager): An instance of the MongoDB management service.
"""

from .blob_service import BlobService
from .email_service import EmailService
from .data_analysis_service import DataAnalysisService
from .user_data_manager_service import UserDataManager
from .datamanager_service import MongoDBManager

blob_service = BlobService()
email_service = EmailService()

user_data_manager_service = UserDataManager
data_analysis_service = DataAnalysisService
datamanager_service = MongoDBManager