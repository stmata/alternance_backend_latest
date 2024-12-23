from sklearn.metrics.pairwise import cosine_similarity
from app.services import blob_service, user_data_manager_service, datamanager_service
from app.helpers import prompt_helpers
from dotenv import load_dotenv
from sklearn.cluster import KMeans
from app.services.semantic_clustering.embedding_service import OpenAIEmbeddingService
from app.services.semantic_clustering.data_preprocessing_service import TextPreprocessor
from collections import Counter
from llama_index.core.response_synthesizers import TreeSummarize
import asyncio
from app.logFile import logger


load_dotenv()

class Predict:
    """
    A class for making predictions using pre-trained clustering and supervised models.
    """
    def __init__(self):
        """
        Initialize the Predict class with necessary services and attributes.
        """
        self.emb = OpenAIEmbeddingService()
        self.clean = TextPreprocessor(language='french')
        self.model_data = {}
        self.job_data_df = None
        self.cluster_centers = None
        self.paragraph_embeddings = None
        self.labels = None
        self.kmeans_loaded = None
    
    def normalize_level(self,level: str) -> str:
        return level.strip().title()

    def load_model(self, platform: str, region: str):
        """
        Load model data for a specific platform and region.

        Args:
            platform (str): The platform name (e.g., 'linkedin', 'indeed').
            region (str): The region name (e.g., 'hauts_de_france', 'ile_de_france').

        Raises:
            ValueError: If the model data cannot be retrieved.
        """
        try:
            # Retrieve model data either locally or from Azure
            self.model_data = blob_service.retrieve_model_data(platform, region)
            
            # Extract necessary data from the retrieved model_data
            self.kmeans_loaded = self.model_data['kmeans_model']
            self.cluster_centers = self.model_data['cluster_centers']
            self.paragraph_embeddings = self.model_data['paragraph_embeddings']
            self.labels = self.model_data['labels']
            self.job_data_df = self.model_data['data_cleaned']

            # Create and fit KMeans model on existing embeddings
            self.kmeans_loaded = KMeans(n_clusters=len(self.cluster_centers), random_state=42)
            self.kmeans_loaded.fit(self.paragraph_embeddings)

        except Exception as e:
            logger.exception(f"Error loading model data for {platform} - {region}")
            raise ValueError(f"Error loading model data for {platform} - {region}: {str(e)}")

    
    def extract_bilingual_content(self, markdown_text):
        """
        Extracts English and French content from the provided markdown text.

        Args:
            markdown_text (str): The markdown text containing bilingual content.

        Returns:
            dict: A dictionary containing English and French content for each section.
        """
        # Initialize variables to store English and French content
        english_content = ""
        french_content = ""

        # Split the text by sections based on the headers
        sections = markdown_text.split("### ")

        for section in sections:
            if section.startswith("English Version"):
                # Extract English content after removing the section title
                english_content = section.split("English Version\n", 1)[1].strip()
            elif section.startswith("Version Française"):
                # Extract French content after removing the section title
                french_content = section.split("Version Française\n", 1)[1].strip()

        return {
            "english": english_content,
            "french": french_content
        }
    


    async def get_cover_lette_missing_and_matching_skills(self, job_description: str, cleaned_summary: str):
        """
        Generates a bilingual cover letter and identifies both missing and matching skills using TreeSummarize.

        Args:
            job_description (str): The job description text.
            cleaned_summary (str): The candidate summary text.

        Returns:
            dict: A dictionary with 'cover_letter', 'missing_skills', and 'matching_skills', each in both English and French.
        """
        summarizer = TreeSummarize(verbose=True)

        # Prompt for the cover letter
        cover_letter_prompt = prompt_helpers.cover_letter_prompt()
        # Generate the cover letter
        cover_letter_input = f"{cleaned_summary}\n{job_description}"
        cover_letter_response = await summarizer.aget_response(cover_letter_prompt, [cover_letter_input])
        
        # Prompt for identifying missing skills
        missing_skills_prompt = prompt_helpers.missing_skills_prompt()
        # Identify missing skills
        missing_skills_input = f"{cleaned_summary}\n{job_description}"
        missing_skills_response = await summarizer.aget_response(missing_skills_prompt, [missing_skills_input])

        # Prompt for identifying matching skills
        matching_skills_prompt = prompt_helpers.matching_skills_prompt()
        # Identify missing skills
        matching_skills_input = f"{cleaned_summary}\n{job_description}"
        matching_skills_response = await summarizer.aget_response(matching_skills_prompt, [matching_skills_input])

        # Extracting bilingual content from responses
        cover_letter = self.extract_bilingual_content(cover_letter_response)
        missing_skills = self.extract_bilingual_content(missing_skills_response)
        matching_skills = self.extract_bilingual_content(matching_skills_response)

        return {
            "cover_letter_en": cover_letter.get("english", ""),
            "cover_letter_fr": cover_letter.get("french", ""),
            "missing_skills_en": missing_skills.get("english", ""),
            "missing_skills_fr": missing_skills.get("french", ""),
            "matching_skills_en": matching_skills.get("english", ""),
            "matching_skills_fr": matching_skills.get("french", "")
        }

    
    async def predict_cluster(self, text_summary: str, platform: str, region: str,  user_id: str, typedeSummary: str, filename: str = None, education_level: str = None, city_for_filter: str = None):
        """
            Predict the cluster for a given text using loaded models and store the results.

            Args:
                text_summary (str): The input text to classify.
                platform (str): The platform name.
                region (str): The region name (e.g., 'france'). For this version, region is always 'france', with 'Location' column containing cities and 'Region' column categorizing into 'ile_de_france', 'hauts_de_france', or 'Others' for other regions.
                user_id (str): The string representation of the user's ObjectId for storing results.
                typedeSummary (str): The type of summary (e.g., 'cv' or 'prompt').
                filename (str, optional): The name of the file associated with the summary, if applicable.
                education_level (str): The education level (e.g., 'Bac+2', 'Bac+3', 'Bac+4', 'Master').
                city_for_filter (str): The city filter for prediction ('ile_de_france', 'hauts_de_france', or 'others').

            Returns:
                dict: A dictionary containing prediction results, similar job listings, and other related data.

            Raises:
                ValueError: If there's an error in generating embeddings or making predictions.
        """


        # Load the model and data if not already loaded
        self.load_model(platform, region)

        # Clean the text and generate embeddings
        cleaned_text = self.clean.clean_text(text_summary)
        summarized_embedding = self.emb.get_openai_embeddings([cleaned_text])

        if summarized_embedding is None or summarized_embedding.size == 0:
            raise ValueError("Error generating embeddings.")

        # Store results for each supervised model
        model_results = {}
        model_probabilities = {}
        cluster_job_matches = {}

        for model_name, model in self.model_data['supervised_models'].items():
            predicted_cluster = int(model.predict(summarized_embedding)[0])
            model_results[model_name] = predicted_cluster

            # Check if the model supports predict_proba
            if hasattr(model, "predict_proba"):
                probabilities = model.predict_proba(summarized_embedding)[0]
                probability = probabilities[predicted_cluster]
                model_probabilities[model_name] = probability
            else:
                model_probabilities[model_name] = None

        # Determine the majority cluster
        cluster_votes = Counter(model_results.values())
        majority_cluster = cluster_votes.most_common(1)[0][0]

        # Find job listings matching the majority cluster
        cluster_job_matches = self.job_data_df[self.job_data_df['cluster'] == majority_cluster].to_dict(orient='records')

        # Calculate cosine similarities between the summary and job embeddings
        similarities = cosine_similarity(summarized_embedding, self.paragraph_embeddings)[0]
        self.job_data_df['Similarity (%)'] = (similarities * 100).round(2)

        # Sort job listings by descending similarity
        sorted_job_data = self.job_data_df.sort_values(by='Similarity (%)', ascending=False)
        top_similar_jobs = sorted_job_data[
            (sorted_job_data['cluster'] == majority_cluster)
        ].to_dict(orient='records')

        tasks = []
        # Iterate over the top similar jobs
        for job in top_similar_jobs:
            # Append the asynchronous task for generating cover letter and missing skills
            tasks.append(self.get_cover_lette_missing_and_matching_skills(job['cleaned_summary'], cleaned_text))

        # Execute the asynchronous tasks concurrently
        cover_letters_and_skills = await asyncio.gather(*tasks)

        # Add the results of the cover letter and missing skills to each job
        for job, results in zip(top_similar_jobs, cover_letters_and_skills):
            job["cover_letter_en"] = results.get("cover_letter_en", "") 
            job["cover_letter_fr"] = results.get("cover_letter_fr", "")  
            job["missing_skills_en"] = results.get("missing_skills_en", "")
            job["missing_skills_fr"] = results.get("missing_skills_fr", "")
            job["matching_skills_en"] = results.get("matching_skills_en", "")
            job["matching_skills_fr"] = results.get("matching_skills_fr", "")

        # # Filter jobs to include only those with a similarity percentage of 70 or higher
        # filtered_top_similar_jobs = [job for job in top_similar_jobs if job['Similarity (%)'] >= 70]

        # Filter to keep only the top 10 jobs
        filtered_top_similar_jobs = top_similar_jobs[:20]

        if education_level:
            LEVEL_HIERARCHY = {
                'Bac+2': 0,
                'Bac+3': 1,
                'Bac+4': 2,
                'Master': 3
            }
        
            # Get the index of the specified education level
            specified_level_index = LEVEL_HIERARCHY.get(self.normalize_level(education_level), None)

            if specified_level_index is not None:
                # Filtrer les emplois en fonction du niveau d'éducation spécifié
                filtered_top_similar_jobs = [
                    job for job in filtered_top_similar_jobs
                    if job.get('Level') == 'No level Required' or
                    LEVEL_HIERARCHY.get(self.normalize_level(job.get('Level', '')), float('inf')) <= specified_level_index
                ]
        if city_for_filter:
            filtered_top_similar_jobs = [
                job for job in filtered_top_similar_jobs
                if job.get('Region') == city_for_filter 
            ]

        # Initialize `filtered_top_similar_jobs` based on the condition
        if not filtered_top_similar_jobs:
            filtered_top_similar_jobs = top_similar_jobs[:10]
            logger.error(f"No predictions found for user {user_id}. Skipping database update.")
        else:
            logger.info(f"Successfully added prediction results for user {user_id}")

        # Common block to add prediction results to the database
        try:
            with datamanager_service() as mongodb_manager:
                user_data_manager = user_data_manager_service(mongodb_manager)
                user_data_manager.add_prediction_result(
                    user_id,
                    platform,
                    region,
                    filtered_top_similar_jobs, 
                    typedeSummary,
                    filename,
                    text_summary,
                    city_for_filter,
                    education_level
                )   
        except Exception as e:
            logger.exception(f"Failed to add prediction results for user {user_id} due to {str(e)}")

        # Construct the final response
        return {
            "Majority": majority_cluster,
            #"supervised_model_results": model_results,
            #"model_probabilities": {name: f"{prob * 100:.2f}%" if prob is not None else "N/A" for name, prob in model_probabilities.items()},
            #"supervised_model_jobs": cluster_job_matches,
            "top_similar_jobs": filtered_top_similar_jobs
        }

