from bson import ObjectId
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from app.helpers import prompt_helpers
from app.services.summarize_desc import summarization_service
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
        self.connection_logs = self.mongodb_manager.get_collection('connection_logs')
        self.admin_activity_logs = self.mongodb_manager.get_collection('admin_activity_logs')
        self._ALLOWED_PERIODS = {
            "daily": timedelta(days=1),
            "weekly": timedelta(weeks=1),
            "monthly": timedelta(days=30)
        }
    
    def _get_period_interval(self, period: str) -> Tuple[datetime, datetime, datetime]:
        """
        Calculate time intervals for a given period.

        Args:
            period (str): The period to calculate intervals for.

        Returns:
            Tuple[datetime, datetime, datetime]: A tuple containing (start time, end time, interval duration)

        Raises:
            ValueError: If period is not one of the allowed values.
        """
        if period not in self._ALLOWED_PERIODS:
            raise ValueError(f"period must be one of {list(self._ALLOWED_PERIODS.keys())}")

        now = datetime.now()
        interval = self._ALLOWED_PERIODS[period]
        period_start = now - interval

        return period_start, now, interval

    def _calculate_trend(self, current_count: int, previous_count: int) -> float:
        """
        Calculate the trend percentage between current and previous counts.
        The result is constrained between -100% and +100%.
        Args:
            current_count (int): Current period count
            previous_count (int): Previous period count
        Returns:
            float: Trend percentage rounded to 2 decimal places, constrained between -100% and +100%
        """
        if previous_count == 0:
            return 100.0 if current_count > 0 else 0.0

        trend = ((current_count - previous_count) / previous_count) * 100

        trend = max(-100.0, min(100.0, trend))

        return round(trend, 2)
        
    def get_active_users_trend(self, period: str, user_role: str) -> Dict[str, float]:
        """
        Retrieve the number of active users within a given period and calculate the trend.

        Args:
            period (str): The period to analyze ("daily", "weekly", "monthly").
            user_role (str): The role of the users to count ("admin" or "user").

        Returns:
            Dict[str, float]: A dictionary containing the count of users and the trend percentage.
        """
        try:
            if period not in self._ALLOWED_PERIODS:
                raise ValueError(f"Invalid period. Allowed values: {list(self._ALLOWED_PERIODS.keys())}")

            now = datetime.now(timezone.utc)
            period_duration = self._ALLOWED_PERIODS[period]
            period_start = now - period_duration
            previous_period_start = period_start - period_duration

            current_count = self.connection_logs.count_documents({
                "user_role": user_role,
                "connection_date": {"$gte": period_start, "$lt": now}
            })

            previous_count = self.connection_logs.count_documents({
                "user_role": user_role,
                "connection_date": {"$gte": previous_period_start, "$lt": period_start}
            })

            trend = self._calculate_trend(current_count, previous_count)

            return {"current_period_count": current_count, "trend_percentage": trend}

        except errors.PyMongoError as e:
            print(f"Database error while retrieving active user trend: {e}")
            return {"current_period_count": 0, "trend_percentage": 0.0}

        except ValueError as e:
            print(f"Value error: {e}")
            return {"current_period_count": 0, "trend_percentage": 0.0}
    
    def get_predictions_trends(self, period: str = "weekly") -> Dict:
        """
        Retrieve the global number of predict_jobs uses for all users and calculate trends.
        Args:
            period (str): The time period to calculate trends for ("daily", "weekly", or "monthly").
        Returns:
            Dict: A dictionary containing global counts and trends.
        """
        try:
            current_start, current_end, interval = self._get_period_interval(period)
            previous_start = current_start - interval

            current_count = 0
            previous_count = 0
            
            for user in self.job_seeker_profiles.find():
                for result in user.get("results_prediction", []):
                    if "added_date_parsed" in result:
                        added_date = result["added_date_parsed"]
                        if current_start <= added_date < current_end:
                            current_count += 1
                        elif previous_start <= added_date < current_start:
                            previous_count += 1

            trend = self._calculate_trend(current_count, previous_count)

            return {
                "current_period_count": current_count,
                "previous_period_count": previous_count,
                "trend_percentage": trend
            }

        except Exception as e:
            print(f"Error in get_predictions_trends: {e}")
            return {}

    def get_liked_posts_trends(self, period: str = "weekly") -> Dict:
        """
        Retrieve the global number of liked posts for all users and calculate trends.
        Args:
            period (str): The time period to calculate trends for ("daily", "weekly", or "monthly").
        Returns:
            Dict: A dictionary containing global counts and trends.
        """
        try:
            current_start, current_end, interval = self._get_period_interval(period)
            previous_start = current_start - interval

            current_count = 0
            previous_count = 0

            for user in self.job_seeker_profiles.find():
                current_count += len([
                    post for post in user.get("liked_posts", [])
                    if "added_date_parsed" in post and current_start <= post["added_date_parsed"] < current_end
                ])

                previous_count += len([
                    post for post in user.get("liked_posts", [])
                    if "added_date_parsed" in post and previous_start <= post["added_date_parsed"] < current_start
                ])

            trend = self._calculate_trend(current_count, previous_count)

            return {
                "current_period_count": current_count,
                "previous_period_count": previous_count,
                "trend_percentage": trend
            }

        except Exception as e:
            print(f"Error in get_liked_posts_trends: {e}")
            return {}

    async def missings_skills_user(self, email: str) -> Dict[str, List[str]]:
        """
        Retrieve all missing skills for a specific user from their results_prediction.
        Args:
            email (str): The email of the user to retrieve missing skills for.
        Returns:
            Dict[str, List[str]]: A dictionary with two keys:
                - "en": List of missing skills in English.
                - "fr": List of missing skills in French.
        """
        try:
            missing_skills_en = []
            missing_skills_fr = []

            user = self.job_seeker_profiles.find_one({"email": email})

            if not user:
                print(f"No user found with email: {email}")
                return {"en": [], "fr": []}

            for result in user.get("results_prediction", []):
                for prediction in result.get("predict_jobs", []):
                    if "missing_skills_en" in prediction:
                        missing_skills_en.extend(prediction["missing_skills_en"].split("\n"))

                    if "missing_skills_fr" in prediction:
                        missing_skills_fr.extend(prediction["missing_skills_fr"].split("\n"))
            if not missing_skills_en and not missing_skills_fr:
                return {"en": [], "fr": []}
            
            missing_skills_en = list(set(skill.strip() for skill in missing_skills_en if skill.strip()))
            missing_skills_fr = list(set(skill.strip() for skill in missing_skills_fr if skill.strip()))
            
            skills_data = {
            "raw_skills_en": missing_skills_en,
            "raw_skills_fr": missing_skills_fr
            }
            missing_skills_prompt = prompt_helpers.missing_skills_business_school_prompt()
            summary_text = await summarization_service.summarize(skills_data, missing_skills_prompt)

            summary_lines = summary_text.strip().split("\n")

            processed_skills_en = []
            processed_skills_fr = []
            current_lang = None

            for line in summary_lines:
                if line.lower().startswith("en:"):
                    current_lang = "en"
                    continue
                elif line.lower().startswith("fr:"):
                    current_lang = "fr"
                    continue
                
                if line.startswith("-"):  
                    if current_lang == "en":
                        processed_skills_en.append(line.strip())
                    elif current_lang == "fr":
                        processed_skills_fr.append(line.strip())

            return {
                "en": processed_skills_en,
                "fr": processed_skills_fr
            }

        except Exception as e:
            print(f"Error in missings_skills_user: {e}")
            return {"en": [], "fr": []}    
        
    
    def get_regions_usage(self) -> Dict[str, int]:
        """
        Retrieve the usage of regions (city_for_filter) in results_prediction.
        This provides visibility into the most used regions by aggregating data from all users.
        Returns:
            Dict[str, int]: A dictionary where keys are region names and values are their counts.
        """
        try:
            region_counts = {}

            for user in self.job_seeker_profiles.find():
                for result in user.get("results_prediction", []):
                    region = result.get("city_for_filter")
                    if region:
                        region_counts[region] = region_counts.get(region, 0) + 1

            return region_counts

        except Exception as e:
            print(f"Error in get_regions_usage: {e}")
            return {}
        
    
    def create_user(self, email: str, isAdmin: bool = False, username: str = None) -> Dict[str, bool]:
        """
        Create a new user if the email does not already exist.

        Args:
            email (str): The email address of the user.
            username (str, optional): The username of the user. If not provided, it will be generated from the email.
            isAdmin (bool, optional): Flag to determine if the user is an admin. Defaults to False.

        Returns:
            dict: A dictionary containing a success status.

        Raises:
            Exception: If a database error occurs during user creation.
        """
        try:
            # Convert email to lowercase
            email = email.lower()
            
            # Check if user already exists
            existing_user = self.job_seeker_profiles.find_one({"email": email})
            if existing_user:
                return {"status": False}

            if username is None:
                try:
                    username_part = email.split('@')[0]
                    prenom, nom = username_part.split('.')
                    nom = nom.capitalize()
                    prenom = prenom.capitalize()
                    username = f"{prenom} {nom}"

                except (ValueError, IndexError):
                    username = email.split('@')[0]

            # Determine user role
            user_role = "admin" if isAdmin else "user"

            # Prepare user data
            user_data = {
                "_id": ObjectId(),
                "email": email,
                "username": username,
                "user_role": user_role,
                "liked_posts": [],
                "results_prediction": []
            }

            # Insert user into database
            self.job_seeker_profiles.insert_one(user_data)
            return {"status": True}

        except errors.PyMongoError as e:
            raise Exception(f"Database error occurred: {str(e)}")

    def log_admin(self, email: str) -> Dict[str, Optional[str]]:
        """
        Retrieve the admin's ID if they exist in the database.

        Args:
            email (str): The email address of the admin.

        Returns:
            dict: A dictionary containing the admin's ID and a success status.
        """
        try:
            email = email.lower()
            admin = self.job_seeker_profiles.find_one({"email": email, "user_role": "admin"}, {"_id": 1})

            if admin:
                return {"_id": str(admin["_id"]), "status": True}
            return {"_id": None, "status": False}
        except errors.PyMongoError as e:
            raise Exception(f"Database error occurred: {str(e)}")

    def log_user(self, email: str) -> Dict[str, Optional[str]]:
        """
        Retrieve the user's ID if they exist in the database.

        Args:
            email (str): The email address of the user.

        Returns:
            dict: A dictionary containing the user's ID and a success status.
        """
        try:
            email = email.lower()
            user = self.job_seeker_profiles.find_one({"email": email}, {"_id": 1})

            if user:
                return {"_id": str(user["_id"]), "status": True}
            return {"_id": None, "status": False}
        except errors.PyMongoError as e:
            raise Exception(f"Database error occurred: {str(e)}")

    def get_users(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Retrieve a list of all users in the database.

        Returns:
            dict: A dictionary containing the list of users with their role, username, and email.
        """
        try:
            users = self.job_seeker_profiles.find({}, {"user_role": 1, "username": 1, "email": 1, "_id": 0})
            user_list = list(users)
            return {"users": user_list, "status": True}
        except errors.PyMongoError as e:
            raise Exception(f"Database error occurred: {str(e)}")

    def update_user(self, email: str, username: str, user_role: str) -> Dict[str, bool]:
        """
        Update a user's username and role based on their email.

        Args:
            email (str): The email address of the user to update.
            username (str): The new username.
            user_role (str): The new role of the user ("admin" or "user").

        Returns:
            dict: A dictionary containing a success status.
        """
        try:
            email = email.lower()
            result = self.job_seeker_profiles.update_one(
                {"email": email},
                {"$set": {"username": username, "user_role": user_role}}
            )
            return {"status": result.modified_count > 0}
        except errors.PyMongoError as e:
            raise Exception(f"Database error occurred: {str(e)}")
    
    def delete_user(self, email: str) -> Dict[str, str]:
        """
        Delete a user from the database by email.

        Args:
            email (str): The email of the user to delete.

        Returns:
            dict: A dictionary indicating success or failure of the operation.
        """
        try:
            result = self.job_seeker_profiles.delete_one({"email": email})

            if result.deleted_count == 1:
                return {"message": "User successfully deleted", "status": True}
            else:
                return {"message": "User not found", "status": False}

        except errors.PyMongoError as e:
            return {"message": f"Database error: {str(e)}", "status": False}
        except Exception as e:
            return {"message": f"An unexpected error occurred: {str(e)}", "status": False}

    def log_connection(self, email: str, user_role: str) -> Dict[str, bool]:
        """
        Log the user's connection in the database.

        Args:
            email (str): The email address of the user.
            user_role (str): The role of the user ("admin" or "user").

        Returns:
            dict: A dictionary containing a success status.
        """
        try:
            connection_data = {
                "_id": ObjectId(),
                "email": email.lower(),
                "user_role": user_role,
                "connection_date": datetime.now(timezone.utc)
            }
            self.connection_logs.insert_one(connection_data)
            return {"status": True}
        except errors.PyMongoError as e:
            raise Exception(f"Database error occurred: {str(e)}")
    
    def get_active_sessions(self, session_duration_minutes: int = 30) -> int:
        """
        Retrieves the number of active sessions (connections within the last N minutes).
        Args:
            session_duration_minutes (int): The duration in minutes to consider a session as active (default is 30).
        Returns:
            int: The number of active sessions.
        """
        try:
            # Calcul du seuil de temps
            threshold = datetime.now(timezone.utc) - timedelta(minutes=session_duration_minutes)
            print(threshold)
            # Compter les sessions actives
            active_sessions = self.connection_logs.count_documents({
                "connection_date": {"$gte": threshold}
            })
            return active_sessions
        except errors.PyMongoError as e:
            print(f"Database error while retrieving active sessions: {e}")
            return -1
        
    def import_users_from_excel(self, file_path: str) -> Dict[str, int]:
        """
        Import a list of users from an Excel file and save them to the database.

        Args:
            file_path (str): The path to the Excel file.

        Returns:
            dict: A dictionary containing the count of inserted and skipped users.
        """
        try:
            df = pd.read_excel(file_path, header=1)

            df = df[['Prénom', 'Nom', 'Email SKEMA']].dropna(subset=['Email SKEMA'])

            df['Email'] = df['Email SKEMA'].astype(str).str.lower()

            df['Users'] = df['Prénom'].astype(str) + ' ' + df['Nom'].astype(str)

            df_final = df[['Users', 'Email']].drop_duplicates(subset=['Email'])

            users_list = df_final.to_dict(orient='records')

            new_users = []
            skipped_count = 0

            for user in users_list:
                email = user["Email"]

                existing_user = self.job_seeker_profiles.find_one({"email": email})
                if existing_user:
                    skipped_count += 1
                    continue 

                new_users.append({
                    "_id": ObjectId(),
                    "email": email,
                    "username": user["Users"],
                    "user_role": "user",
                    "liked_posts": [],
                    "results_prediction": []
                })

            if new_users:
                self.job_seeker_profiles.insert_many(new_users)

            return {"inserted": len(new_users), "skipped": skipped_count}

        except errors.PyMongoError as e:
            raise Exception(f"Database error occurred: {str(e)}")
        except Exception as e:
            raise Exception(f"An error occurred while processing the Excel file: {str(e)}")

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

    
    def get_or_create_user(self, email: str) -> tuple[str, str]:
        """
        Retrieve an existing user's ID by email, or create a new user if none exists.
        Extracts username from SKEMA email format (nom.prenom@skema.edu).

        Args:
            email (str): The email address of the user.

        Returns:
            tuple[str, str]: A tuple containing (user_id, user_role).
        """
        try:
            email = email.lower()
            
            existing_user = self.job_seeker_profiles.find_one({"email": email})
            
            if existing_user:
                return str(existing_user['_id']), existing_user['user_role']
            
            username_part = email.split('@')[0]  
            prenom, nom = username_part.split('.') 
            nom = nom.capitalize()
            prenom = prenom.capitalize()
            username = f"{prenom} {nom}"
            
            user_role = "user"  
            
            user_data = {
                "_id": ObjectId(),
                "email": email,
                "username": username,
                "user_role": user_role,
                "liked_posts": [],
                "results_prediction": []
            }
            
            result = self.job_seeker_profiles.insert_one(user_data)
            return str(result.inserted_id), user_role

        except errors.PyMongoError as e:
            raise Exception(f"Database error occurred: {str(e)}")


    def add_liked_post(self, user_id: str, job_post: Dict) -> None:
        """
        Add a liked post to a user's list of liked posts.

        Args:
            user_id (str): The string representation of the user's ObjectId.
            job_post (Dict): A dictionary containing job post information.
        """
        try:
            now = datetime.now(timezone.utc)

            liked_post = {
            "Company": job_post.get("Company", ""),
            "Title": job_post.get("Title", ""),
            "Location": job_post.get("Location",""),
            "Publication Date": job_post.get("Publication Date",""),
            "Url": job_post.get("Url", ""),
            "Summary": job_post.get("Summary", ""),
            "Summary_fr": job_post.get("Summary_fr", ""),
            "added_date": now.strftime('%Y-%m-%d à %H:%M'),
            "added_date_parsed": now
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
            def normalize(value):
                return value.strip().lower() if value else None

            normalized_summary_type = normalize(summary_type)
            normalized_city_for_filter = normalize(city_for_filter)
            normalized_filename = normalize(filename)
            # Step 1: Check if the user already has a similar prediction
            user_data = self.job_seeker_profiles.find_one({"_id": ObjectId(user_id)}, {"results_prediction": 1})
            city_mapping = {
                "ile_de_france": "Île-de-France",
                "hauts_de_france": "Hauts-de-France",
                "alpes_cote_dazur": "Côte d'Azur",
                "Others": "Autres régions"
            }
            
            if normalized_city_for_filter in city_mapping:
                normalized_city_for_filter = normalize(city_mapping[normalized_city_for_filter])
            # check if a prediction is similar based on filename or summary type.
            if user_data and "results_prediction" in user_data:
                for prediction in user_data["results_prediction"]:
                    existing_summary_type = normalize(prediction.get("typedeSummary"))
                    existing_city_for_filter = normalize(prediction.get("city_for_filter"))
                    existing_filename = normalize(prediction.get("filename"))

                    if (existing_summary_type == normalized_summary_type and
                        existing_city_for_filter == normalized_city_for_filter and
                        existing_filename == normalized_filename):
                        raise Exception("A similar prediction already exists based on the current criteria.")
                    
            # Create the result structure for insertion
            now = datetime.now(timezone.utc)
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
                "added_date": now.strftime('%Y-%m-%d à %H:%M'),
                "added_date_parsed": now
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

    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, str]]:
        """
        Retrieve a user's ID and role given their email address.

        Args:
            email (str): The email address of the user.

        Returns:
            Optional[Dict[str, str]]: A dictionary containing the user's ObjectId (as a string) and user_role if found,
            None otherwise.
        """
        try:
            user = self.job_seeker_profiles.find_one({"email": email}, {"_id": 1, "user_role": 1})
            return {"_id": str(user["_id"]), "user_role": user["user_role"]} if user else None
        except errors.PyMongoError as e:
            raise Exception(f"Failed to retrieve user by email: {str(e)}")
    
    def log_admin_activity(self, admin_email: str, action_message: str) -> bool:
        """
        Logs an admin's activity into the admin_activity_logs collection.
        
        Args:
            admin_email (str): The email of the admin performing the action.
            action_message (str): A description of the action performed by the admin.
        
        Returns:
            bool: True if the log was successfully added, False otherwise.
        """
        try:
            admin_data = self.job_seeker_profiles.find_one(
                {"email": admin_email, "user_role": "admin"}
            )
            
            if not admin_data:
                return False
            
            admin_email = admin_data.get("email")
            admin_name = admin_data.get("username")
            
            current_time = datetime.now(timezone.utc)
            
            log_entry = {
                "admin_email": admin_email,
                "admin_name": admin_name,
                "action_message": action_message,
                "timestamp": current_time
            }
            
            result = self.admin_activity_logs.insert_one(log_entry)
            
            return result.acknowledged
        
        except errors.PyMongoError as e:
            #print(f"Erreur lors de l'enregistrement de l'activité admin : {e}")
            return False
        except Exception as e:
            #print(f"Erreur inattendue : {e}")
            return False
        
    def get_admin_activity_logs(self) -> List[Dict]:
        """
        Retrieve all admin activity logs from the database.
        
        Returns:
            List[Dict]: A list of formatted admin activity logs.
        """
        try:
            logs = (
                self.admin_activity_logs.find()
                .sort("timestamp", -1)  
            )
            
            formatted_logs = []
            for log in logs:
                formatted_logs.append({
                    "id": str(log["_id"]),
                    "admin_email": log.get("admin_email"),
                    "admin_name": log.get("admin_name"),
                    "action_message": log.get("action_message"),
                    "timestamp": log.get("timestamp").strftime("%Y-%m-%d %H:%M:%S")  
                })
            
            return formatted_logs
        
        except errors.PyMongoError as e:
            print(f"Erreur lors de la récupération des logs d'activité : {e}")
            return []
        except Exception as e:
            print(f"Erreur inattendue : {e}")
            return []
