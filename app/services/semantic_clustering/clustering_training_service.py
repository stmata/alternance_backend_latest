from dotenv import load_dotenv
import numpy as np
import pandas as pd
from io import StringIO
from kneed import KneeLocator
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_distances
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from app.services.semantic_clustering.embedding_service import OpenAIEmbeddingService
from app.services.semantic_clustering.data_preprocessing_service import TextPreprocessor
from app.services import blob_service
from app.services import email_service
from app.logFile import logger

load_dotenv()


class ClusteringService:
    """Service for performing clustering on job data from multiple platforms and regions."""

    def __init__(self):
        """
        Initialize the ClusteringService with necessary services and models.

        Args:
            blob_service: Service for interacting with Azure Blob Storage.
            embedding_service: Service for generating embeddings.
            data_preprocessing_service: Service for data preprocessing.

        Attributes:
            blob_service: The Azure Blob Storage service.
            emb: The embedding service.
            clean: The data preprocessing service.
            supervised_models (dict): A dictionary of supervised machine learning models.
            platforms (list): List of platforms to process.
            regions (list): List of regions to process.
        """
        self.clean = TextPreprocessor()
        self.emb = OpenAIEmbeddingService()
        self.supervised_models = {
            "RandomForest": RandomForestClassifier(n_estimators=100, random_state=50, class_weight='balanced'),
            "SVM": SVC(kernel='linear', random_state=50, class_weight='balanced'),
            "LogisticRegression": LogisticRegression(random_state=50, class_weight='balanced'),
            "KNN": KNeighborsClassifier(n_neighbors=5),
            "GradientBoosting": GradientBoostingClassifier(random_state=50)
        }
        self.platforms =["apec", "linkedin", "indeed", "jungle", "hellowork"]
        #self.platforms =["apec", "indeed", "jungle", "hellowork"]
        self.regions = ["france"]   

    def process_clustering(self):
        """
        Perform clustering on CSV files based on platforms and regions.

        This method retrieves CSV files from Azure Blob Storage, processes the data to clean it,
        generates embeddings, and applies KMeans clustering. It also trains and evaluates supervised
        models on the clustered data.

        Returns:
            dict: A dictionary containing the results of the clustering process, including
                messages about the completion of the process, the best model used, and model scores.
        """
        try:
            results = {}
            # To track the overall process status
            success = True
            
            for platform in self.platforms:
                for region in self.regions:
                    logger.info(f"Processing {platform} - {region}...")
                    csv_path = f"temp/summarize/{platform}/{region}.csv"
                               
                    try:
                        # Download CSV content from Azure Blob Storage
                        csv_content = blob_service.get_csv_content(csv_path)
                    except Exception as e:
                        logger.exception(f"Error retrieving file {csv_path}")
                        success = False
                        continue

                    # Convert bytes to StringIO for pandas to read
                    csv_file = StringIO(csv_content)

                    # Read data from the CSV
                    df = pd.read_csv(csv_file)
                    if "Summary" not in df.columns:
                        success = False
                        logger.error(f"'Summary' column not found in file {csv_path}")
                        continue

                    logger.info('Start cleaning')
                    # Clean and preprocess the data
                    data_cleaned = df.dropna(subset=['Summary']).reset_index(drop=True)
                    data_cleaned['cleaned_summary'] = data_cleaned['Summary'].apply(self.clean.clean_text)
                    paragraphs = data_cleaned['cleaned_summary'].tolist()
                    
                    # Generate embeddings for paragraphs
                    paragraph_embeddings = self.emb.get_openai_embeddings(paragraphs)
                    
                    # Determine the optimal number of clusters using WCSS
                    wcss = []
                    max_clusters = min(10, len(paragraphs))
                    for i in range(1, max_clusters + 1):
                        kmeans = KMeans(n_clusters=i, random_state=50)
                        kmeans.fit(paragraph_embeddings)
                        cluster_centers = kmeans.cluster_centers_
                        distances = cosine_distances(paragraph_embeddings, cluster_centers)
                        min_distances = np.min(distances, axis=1)
                        wcss.append(sum(min_distances**2))
                    
                    logger.info(f"cluster_centers : {cluster_centers}")

                    # Use the elbow method to determine the optimal number of clusters
                    knee_locator = KneeLocator(range(1, max_clusters + 1), wcss, curve='convex', direction='decreasing')
                    optimal_clusters = knee_locator.knee if knee_locator.knee else 3
                    logger.info(f"optimal_clusters : {optimal_clusters}")
                    kmeans = KMeans(n_clusters=optimal_clusters, random_state=50)
                    kmeans.fit(paragraph_embeddings)
                    logger.info(f"Optimal clusters for {platform} - {region}: {optimal_clusters}")

                    # Assign labels to the data
                    data_cleaned['cluster'] = kmeans.labels_
                    
                    # Split the data for training and testing
                    X, y = paragraph_embeddings, data_cleaned['cluster'].values
                    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=50)
                    model_scores = {}

                    # Train and evaluate supervised models
                    for model_name, model in self.supervised_models.items():
                        model.fit(X_train, y_train)
                        y_pred = model.predict(X_test)
                        accuracy = accuracy_score(y_test, y_pred)
                        model_scores[model_name] = accuracy

                    best_model_name = max(model_scores, key=model_scores.get)

                    # Prepare data for saving to Azure Blob Storage
                    model_data = {
                        'kmeans_model': kmeans,
                        'cluster_centers': kmeans.cluster_centers_,
                        'paragraph_embeddings': paragraph_embeddings,
                        'labels': kmeans.labels_,
                        'data_cleaned': data_cleaned,
                        'supervised_models': self.supervised_models
                    }
                    # Save all model data to Azure Blob Storage
                    blob_service.save_model_data(platform, region, model_data)

                    results[f"{platform}_{region}"] = {
                        "message": f"Clustering completed with {optimal_clusters} clusters for {platform} - {region}.",
                        "best_model": best_model_name,
                        "model_scores": model_scores
                    }
            
            # Send notification with clustering results
            #email_service.send_clustering_notification(results, success)

            return results

        except Exception as e:
            logger.exception("error during clustering")
            return {"error": str(e)}


