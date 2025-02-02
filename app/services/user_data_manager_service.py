from bson import ObjectId
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pymongo import errors

class UserDataManager:
    """
    A class to manage user data operations in MongoDB.

    This class provides methods to interact with user data, including
    adding users, managing liked posts, and handling prediction results.

    Attributes:
        mongodb_manager: An instance of MongoDBManager for database operations.
        users_collection: A MongoDB collection for user data.
    """

    def __init__(self, mongodb_manager):
        """
        Initialize the UserDataManager.

        Args:
            mongodb_manager: An instance of MongoDBManager.
        """
        self.mongodb_manager = mongodb_manager
        self.job_seeker_profiles = self.mongodb_manager.get_collection('job_seeker_profiles')

    def add_cv_resume(self, user_id: str, cv_resume_content: str) -> str:
        """
        Add or update the cv_resume field for a given user if the content is different.

        Args:
            user_id (str): The string representation of the user's ObjectId.
            cv_resume_content (str): The content of the CV resume.

        Returns:
            str: A message indicating the result ('cv_identical' if the content is the same).

        Raises:
            Exception: If the database operation fails.
        """
        try:
            # Check if the user already has a cv_resume and if it's the same content
            user = self.job_seeker_profiles.find_one({"_id": ObjectId(user_id)}, {"cv_resume": 1})
            
            if user and "cv_resume" in user:
                if user["cv_resume"] == cv_resume_content:
                    return "cv_identical"  # Return this instead of raising an exception
            
            # Update or add the cv_resume if the content is different
            self.job_seeker_profiles.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"cv_resume": cv_resume_content}}
            )
            return "cv_updated"
        
        except errors.PyMongoError as e:
            raise Exception(f"Failed to add CV resume: {str(e)}")

    
    def get_cv_resume(self, user_id: str) -> Optional[str]:
        """
        Retrieve the cv_resume field for a given user.

        Args:
            user_id (str): The string representation of the user's ObjectId.

        Returns:
            Optional[str]: The content of the CV resume, or None if not found.

        Raises:
            Exception: If the database operation fails.
        """
        try:
            user = self.job_seeker_profiles.find_one({"_id": ObjectId(user_id)}, {"cv_resume": 1})
            return user.get("cv_resume") if user and "cv_resume" in user else None
        except errors.PyMongoError as e:
            raise Exception(f"Failed to retrieve CV resume : {str(e)}")


    
    def get_or_create_user(self, email: str) -> str:
        """
        Retrieve an existing user's ID by email, or create a new user if none exists.

        Args:
            email (str): The email address of the user.

        Returns:
            str: The string representation of the user's ObjectId.
        """
        try:
            # Check if the user already exists
            email = email.lower()
            existing_user = self.job_seeker_profiles.find_one({"email": email})
            
            if existing_user:
                # If the user exists, return their _id
                return str(existing_user['_id'])
            
            # If the user does not exist, create a new user
            user_data = {
                "_id": ObjectId(),
                "email": email,
                "liked_posts": [],
                "results_prediction": []
            }
            result = self.job_seeker_profiles.insert_one(user_data)
            
            # Return the ObjectId of the new user
            return str(result.inserted_id)

        except errors.PyMongoError as e:
            # Log the error and re-raise it or handle it as appropriate
            raise Exception(f"Database error occurred: {str(e)}")


    def add_liked_post(self, user_id: str, job_post: Dict) -> None:
        """
        Add a liked post to a user's list of liked posts.

        Args:
            user_id (str): The string representation of the user's ObjectId.
            job_post (Dict): A dictionary containing job post information.
        """
        try:
            liked_post = {
            "Company": job_post.get("Company", ""),
            "Title": job_post.get("Title", ""),
            "Location": job_post.get("Location",""),
            "Publication Date": job_post.get("Publication Date",""),
            "Url": job_post.get("Url", ""),
            "Summary": job_post.get("Summary", ""),
            "Summary_fr": job_post.get("Summary_fr", ""),
            "added_date": datetime.now(timezone.utc).strftime('%Y-%m-%d à %H:%M')
            }
        
            self.job_seeker_profiles.update_one(
            {"_id": ObjectId(user_id)},
            {"$push": {"liked_posts": liked_post}}
            )

        except errors.PyMongoError as e:
            raise Exception(f"Failed to add liked post: {str(e)}")

    def remove_liked_post(self, user_id: str, job_post_url: str) -> str:
        """
        Remove a liked post from a user's list of liked posts.

        Args:
            user_id (str): The string representation of the user's ObjectId.
            job_post_url (str): The URL of the job post to be removed.

        Returns:
            str: A message indicating the result of the operation.
        """
        try:
            # Check if the post exists before attempting to remove it
            user = self.job_seeker_profiles.find_one({"_id": ObjectId(user_id)}, {"liked_posts": 1})
            
            if user and "liked_posts" in user:
                # Check if the URL exists in the liked_posts
                liked_post = next((post for post in user["liked_posts"] if post.get("Url") == job_post_url), None)
                if not liked_post:
                    return "No liked post found with the specified URL."

            # Remove the liked post
            result = self.job_seeker_profiles.update_one(
                {"_id": ObjectId(user_id)},
                {"$pull": {"liked_posts": {"Url": job_post_url}}}
            )

            if result.modified_count == 0:
                return "No liked post found with the specified URL."

            return "Liked post removed successfully."

        except errors.PyMongoError as e:
            raise Exception(f"Failed to remove liked post: {str(e)}")


    
    def add_prediction_result(self, user_id: str,platform: str, region: str, prediction_results: List[Dict], summary_type: str, filename: str = None, text_summary: str = None, city_for_filter :str = None,education_level: str = None) -> None:
        """
        Add prediction results to a user's list of prediction results.

        Args:
            user_id (str): The string representation of the user's ObjectId.
            platform (str): The platform name from which the predictions originate.
            region (str): The region associated with the predictions.
            prediction_results (List[Dict]): A list of dictionaries containing the prediction results.
            filename (str, optional): The name of the file (if provided). Defaults to None.
            text_summary (str, optional): The summarized text (if provided). Defaults to None.  
            summary_type (str): The type of summary (e.g., 'cv' or 'prompt').

        Raises:
            Exception: If a similar prediction exists or database operation fails.
        """
        try:
            # Step 1: Check if the user already has a similar prediction
            user_data = self.job_seeker_profiles.find_one({"_id": ObjectId(user_id)}, {"results_prediction": 1})
            city_mapping = {
                "ile_de_france": "Île-de-France",
                "hauts_de_france": "Hauts-de-France",
                "alpes_cote_dazur": "Côte d'Azur",
                "Others": "Autres régions"
            }
    
            if city_for_filter in city_mapping:
                city_for_filter = city_mapping[city_for_filter]
            # check if a prediction is similar based on filename or summary type.
            if user_data and "results_prediction" in user_data:
                for prediction in user_data["results_prediction"]:
                    if filename is not None:
                        if prediction.get("filename") == filename and prediction.get("platform") == platform and prediction.get("region") == region :
                            raise Exception("A similar prediction already exists based on the current criteria.")
                    if text_summary is not None:
                        if prediction.get("textSummary") == text_summary and prediction.get("platform") == platform and prediction.get("region") == region :
                            raise Exception("A similar prediction already exists based on the current criteria.")
                    
            # Create the result structure for insertion
            result = {
                "predict_jobs": [{
                    "Url": job.get("Url", ""), 
                    "Company": job.get("Company", ""),
                    "Title": job.get("Title", ""),
                    "Location": job.get("Location", ""),
                    "Publication Date": job.get("Publication Date", ""),
                    "Summary": job.get("Summary", ""),
                    "Summary_fr": job.get("Summary_fr", ""),
                    "cover_letter_en": job.get("cover_letter_en", ""),
                    "cover_letter_fr": job.get("cover_letter_fr", ""),
                    "missing_skills_en": job.get("missing_skills_en", ""),
                    "missing_skills_fr": job.get("missing_skills_fr", ""),
                    "matching_skills_en": job.get("matching_skills_en", ""),
                    "matching_skills_fr": job.get("matching_skills_fr", ""),
                    "Similarity (%)": job.get("Similarity (%)", ""),
                } for job in prediction_results],
                "typedeSummary": summary_type,
                "platform" : platform,
                "region" : region,
                "city_for_filter" : city_for_filter,
                "education_level" : education_level,
                "added_date": datetime.now(timezone.utc).strftime('%Y-%m-%d à %H:%M')
            }
            if filename is not None:
                result["filename"] = filename
            
            if text_summary is not None:
                result["textSummary"] = text_summary

            self.job_seeker_profiles.update_one(
                {"_id": ObjectId(user_id)},
                {"$push": {"results_prediction": result}}
            )
        except errors.PyMongoError as e:
            raise Exception(f"Failed to add prediction result: {str(e)}")



    def get_user_liked_posts(self, user_id: str) -> List[Dict]:
        """
        Retrieve all liked posts for a given user.

        Args:
            user_id (str): The string representation of the user's ObjectId.

        Returns:
            List[Dict]: A list of dictionaries containing liked post information.
        """
        try:
            user = self.job_seeker_profiles.find_one({"_id": ObjectId(user_id)})
            return user['liked_posts'] if user else []
        except errors.PyMongoError as e:
            raise Exception(f"Failed to retrieve liked posts: {str(e)}")


    def get_user_prediction_results(self, user_id: str) -> List[Dict]:
        """
        Retrieve all prediction results for a given user.

        Args:
            user_id (str): The string representation of the user's ObjectId.

        Returns:
            List[Dict]: A list of dictionaries containing prediction result information.
        """
        try:
            user = self.job_seeker_profiles.find_one({"_id": ObjectId(user_id)})
            return user['results_prediction'] if user else []
        except errors.PyMongoError as e:
            raise Exception(f"Failed to retrieve prediction results: {str(e)}")


    def get_user_by_email(self, email: str) -> Optional[str]:
        """
        Retrieve a user's ID given their email address.

        Args:
            email (str): The email address of the user.

        Returns:
            Optional[str]: The string representation of the user's ObjectId if found, None otherwise.
        """
        try:
            user = self.job_seeker_profiles.find_one({"email": email})
            return str(user['_id']) if user else None
        except errors.PyMongoError as e:
            raise Exception(f"Failed to retrieve user by email: {str(e)}")
