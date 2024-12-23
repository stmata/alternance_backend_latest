"""
This module initializes services for training, and prediction.

It imports and instantiates the following services:
- Predict: A service for making predictions based on trained models.

Instances of these services are created for use throughout the application.

Attributes:
    predict_service (Predict): An instance of the prediction service.
"""

from .predict_service import Predict
from .clustering_training_service import ClusteringService

predict_service = Predict()
clustering_training_service = ClusteringService()