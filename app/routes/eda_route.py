from fastapi import APIRouter, Form, HTTPException, File, UploadFile
from pydantic import BaseModel, Field, EmailStr
from pymongo import errors
import os
import pandas as pd
import tempfile
from typing import Annotated, Dict, List
from app.services import blob_service
from app.services import data_analysis_service, user_data_manager_service, datamanager_service
from app.logFile import logger

eda_route = APIRouter(prefix="/eda")

class UserRequest(BaseModel):
    email: EmailStr

class FileRetrievalRequest(BaseModel):
    platform: str
    region: str

class ActiveUsersTrendRequest(BaseModel):
    period: Annotated[str, Field(pattern="^(daily|weekly|monthly)$")]
    user_role: Annotated[str, Field(pattern="^(admin|user)$")]

class TrendRequest(BaseModel):
    period: Annotated[str, Field(pattern="^(daily|weekly|monthly)$")]

class CreateUserRequest(BaseModel):
    email: EmailStr
    username: Annotated[str, Field(min_length=1)]
    isAdmin: bool
    admin_email: EmailStr

class UpdateUserRequest(BaseModel):
    email: EmailStr
    username: Annotated[str, Field(min_length=1)]
    user_role: Annotated[str, Field(pattern="^(admin|user)$")]
    admin_email: EmailStr

class DeleteRequest(BaseModel):
    email: EmailStr
    admin_email: EmailStr

class UserResponse(BaseModel):
    message: str
    status: bool

class RegionsUsageResponse(BaseModel):
    regions: Dict[str, int]

class MissingSkillsResponse(BaseModel):
    en: List[str]
    fr: List[str]

class TrendResponse(BaseModel):
    current_period_count: int
    previous_period_count: int
    trend_percentage: float

# Mapping des noms de régions
REGION_MAPPING = {
    "Others": "Autres Régions",
    "ile_de_france": "Île-de-France",
    "hauts_de_france": "Hauts-de-France",
    "alpes_cote_dazur": "Province-Alpes-Côte d'Azur"
}

def format_error_message(error: Exception) -> str:
        if isinstance(error, ValueError):
            return "Les données du fichier sont invalides ou mal formatées."
        elif isinstance(error, FileNotFoundError):
            return "Le fichier n'a pas pu être trouvé ou est inaccessible."
        elif isinstance(error, KeyError):
            return "Certaines colonnes obligatoires sont manquantes dans le fichier."
        elif isinstance(error, errors.PyMongoError):
            return "Une erreur est survenue lors de l'interaction avec la base de données."
        else:
            return "Une erreur inattendue est survenue."
        
@eda_route.post("/analyze-data")
async def analyze_data(request: FileRetrievalRequest):
    """
    Endpoint to analyze data from a specific CSV file in Azure Blob Storage.

    Args:
        platform (str): The name of the site (e.g., "apec", "indeed", etc.).
        region (str): The region for which the CSV file will be retrieved and analyzed.

    Returns:
        dict: The results of the data analysis.

    Raises:
        HTTPException: If the CSV file is not found, empty, or if an error occurs during analysis.
    """
    try:
        # Construct the blob path in Azure Blob Storage
        blob_path = f"{request.platform}/{request.region}.csv"

        # Use the blob service to retrieve the CSV data as a string
        csv_content = blob_service.get_csv_content(blob_path)

        # Check if the CSV content is empty
        if not csv_content:
            raise HTTPException(status_code=404, detail=f"The CSV file for {request.platform} and {request.region} was not found or is empty.")

        # Create an instance of DataAnalysisService by passing the CSV content
        analysis_service = data_analysis_service(csv_content)

        # Perform the data analysis
        analysis_results = analysis_service.analyze_data()

        logger.info(f"Successful data analysis for {request.platform} in the {request.region} region.")
        return analysis_results

    except Exception as e:
        logger.error(f"Error during data analysis for {request.platform}/{request.region}: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred during data analysis.")

@eda_route.get("/active-sessions")
async def get_active_sessions():
    """
    Endpoint to retrieve the active sessions of users who are connected within the last 30 minutes.
    Returns:
        dict: A list of active sessions and their details or a failure status.
    """
    try:
        with datamanager_service() as mongodb_manager:
            user_data_manager = user_data_manager_service(mongodb_manager)
            active_sessions = user_data_manager.get_active_sessions(session_duration_minutes=30)
            if active_sessions > 0:
                return {"status": True, "active_sessions": active_sessions}
            else:
                return {"status": False, "message": "No active sessions found."}
    except Exception as e:
        logger.error(f"Error while retrieving active sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving active sessions.")


@eda_route.get("/get-all-users")
async def get_all_users():
    """
    Endpoint to retrieve a list of all users with their role, username, and email.
    Returns:
        dict: A dictionary containing the list of users or an error message.
    """
    try:
        with datamanager_service() as mongodb_manager:
            user_data_manager = user_data_manager_service(mongodb_manager)
            result = user_data_manager.get_users()
            
            if result["status"]:
                return {"users": result["users"], "status": True}
            else:
                raise HTTPException(status_code=404, detail="No users found.")
    except Exception as e:
        logger.error(f"Error while retrieving users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving users: {str(e)}")

@eda_route.post("/active-users-trend")
async def get_active_users_trend(request: ActiveUsersTrendRequest):
    """
    Endpoint to retrieve the number of active users within a given period and calculate the trend.
    Args:
        request (ActiveUsersTrendRequest): A Pydantic model containing the period and user role.
    Returns:
        dict: A dictionary containing the count of active users and the trend percentage.
    Raises:
        HTTPException: If an error occurs during retrieval.
    """
    try:
        period = request.period
        user_role = request.user_role

        with datamanager_service() as mongodb_manager:
            user_data_manager = user_data_manager_service(mongodb_manager)
            result = user_data_manager.get_active_users_trend(period, user_role)

            return {
                "current_period_count": result["current_period_count"],
                "trend_percentage": result["trend_percentage"],
                "status": True
            }
    except Exception as e:
        logger.error(f"Error while retrieving active users trend: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving active users trend: {str(e)}")

@eda_route.post("/import-users")
async def import_users(file: UploadFile = File(...), admin_email: str = Form(...)):
    """
    Endpoint to import users from an Excel file and save them to the database.
    Args:
        file (UploadFile): The Excel file to process.
    Returns:
        dict: A dictionary containing the count of inserted and skipped users.
    Raises:
        HTTPException: If the file is invalid or an error occurs during processing.
    """
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Invalid file format. Only .xlsx or .xls files are allowed.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name

        with datamanager_service() as mongodb_manager:
            user_data_manager = user_data_manager_service(mongodb_manager)
            result = user_data_manager.import_users_from_excel(temp_file_path)

            inserted_count = result["inserted"]
            skipped_count = result["skipped"]

            action_message = f"Admin a importé un fichier Excel contenant {inserted_count} utilisateurs insérés et {skipped_count} utilisateurs ignorés."
            log_result = user_data_manager.log_admin_activity(
                admin_email = admin_email,
                action_message = action_message
            )
            
            if not log_result:
                logger.warning("Admin activity logging failed")

        os.unlink(temp_file_path)
        return {
            "inserted": result["inserted"],
            "skipped": result["skipped"],
            "status": True,
            "message": f"Successfully imported {result['inserted']} users. Skipped {result['skipped']} duplicate users."
        }
    except Exception as e:
        logger.error(f"Error while importing users from Excel: {str(e)}")
        formatted_message = format_error_message(e)
        raise HTTPException(
            status_code=500,
            detail=formatted_message
        )

@eda_route.post("/create-user", response_model=UserResponse)
async def create_user(request: CreateUserRequest):
    """
    Endpoint to create a new user if the email does not already exist.
    Args:
        request (CreateUserRequest): The request body containing user details and the admin email.
    Returns:
        UserResponse: A response containing success status and message.
    Raises:
        HTTPException: If an error occurs during user creation.
    """
    try:
        with datamanager_service() as mongodb_manager:
            user_data_manager = user_data_manager_service(mongodb_manager)
            result = user_data_manager.create_user(
                request.email,
                request.username,
                request.isAdmin
            )

            if result["status"]:
                action_message = f"Admin a créé un utilisateur avec l'email {request.email}."
                log_result = user_data_manager.log_admin_activity(
                        admin_email=request.admin_email,  
                        action_message=action_message
                    )
                    
                if not log_result:
                    logger.warning("Admin activity logging failed")
                return UserResponse(message="User successfully created", status=True)
            else:
                raise HTTPException(
                    status_code=409,
                    detail="User with this email already exists."
                )
    except Exception as e:
        logger.error(f"Error while creating user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while creating the user: {str(e)}"
        )

@eda_route.put("/update-user", response_model=UserResponse)
async def update_user(request: UpdateUserRequest):
    """
    Endpoint to update a user's username and role based on their email.
    Args:
        request (UpdateUserRequest): The request body containing updated user details and the admin email.
    Returns:
        UserResponse: A response containing success status and message.
    Raises:
        HTTPException: If the user is not found or an error occurs.
    """
    try:
        with datamanager_service() as mongodb_manager:
            user_data_manager = user_data_manager_service(mongodb_manager)
            result = user_data_manager.update_user(
                request.email,
                request.username,
                request.user_role
            )

            if result["status"]:
                action_message = f"Admin a mis à jour les informations de l'utilisateur avec l'email {request.email}."
                log_result = user_data_manager.log_admin_activity(
                        admin_email=request.admin_email,  
                        action_message=action_message
                    )
                    
                if not log_result:
                    logger.warning("Admin activity logging failed")
                return UserResponse(message="User successfully updated", status=True)
            else:
                raise HTTPException(status_code=404, detail="User not found.")
    except Exception as e:
        logger.error(f"Error while updating user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while updating the user: {str(e)}"
        )

@eda_route.delete("/delete-user", response_model=UserResponse)
async def delete_user(request: DeleteRequest):
    """
    Endpoint to delete a user from the database by email.
    Args:
        request (DeleteRequest): The request body containing the user's email and the admin email.
    Returns:
        UserResponse: A response indicating success or failure of the operation.
    Raises:
        HTTPException: If the user is not found or an error occurs.
    """
    try:
        with datamanager_service() as mongodb_manager:
            user_data_manager = user_data_manager_service(mongodb_manager)
            result = user_data_manager.delete_user(request.email)

            if result["status"]:
                action_message = f"Admin a supprimé l'utilisateur avec l'email {request.email}."
                log_result = user_data_manager.log_admin_activity(
                        admin_email=request.admin_email,  
                        action_message=action_message
                    )
                    
                if not log_result:
                    logger.warning("Admin activity logging failed")
                return UserResponse(message="User successfully deleted", status=True)
            else:
                raise HTTPException(status_code=404, detail="User not found.")
    except Exception as e:
        logger.error(f"Error while deleting user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while deleting the user: {str(e)}"
        )
    


@eda_route.post("/predictions-trends", response_model=TrendResponse)
async def get_predictions_trends_endpoint(request: TrendRequest) -> TrendResponse:
    """
    Endpoint to retrieve the global number of predict_jobs uses and calculate trends.
    Args:
        request (TrendRequest): The time period to calculate trends for ("daily", "weekly", or "monthly").
    Returns:
        TrendResponse: A dictionary containing global counts and trends.
    """
    try:
        with datamanager_service() as mongodb_manager:
            user_data_manager = user_data_manager_service(mongodb_manager)
            trends_data = user_data_manager.get_predictions_trends(request.period)
            if not trends_data:
                raise HTTPException(status_code=404, detail="No predictions trends data found.")
            return TrendResponse(
                current_period_count=trends_data["current_period_count"],
                previous_period_count=trends_data["previous_period_count"],
                trend_percentage=trends_data["trend_percentage"]
            )
    except Exception as e:
        logger.error(f"Error in /predictions-trends endpoint: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving predictions trends.")

@eda_route.post("/liked-posts-trends", response_model=TrendResponse)
async def get_liked_posts_trends_endpoint(request: TrendRequest) -> TrendResponse:
    """
    Endpoint to retrieve the global number of liked posts and calculate trends.
    Args:
        request (TrendRequest): The time period to calculate trends for ("daily", "weekly", or "monthly").
    Returns:
        TrendResponse: A dictionary containing global counts and trends.
    """
    try:
        with datamanager_service() as mongodb_manager:
            user_data_manager = user_data_manager_service(mongodb_manager)
            trends_data = user_data_manager.get_liked_posts_trends(request.period)
            if not trends_data:
                raise HTTPException(status_code=404, detail="No liked posts trends data found.")
            return TrendResponse(
                current_period_count=trends_data["current_period_count"],
                previous_period_count=trends_data["previous_period_count"],
                trend_percentage=trends_data["trend_percentage"]
            )
    except Exception as e:
        logger.error(f"Error in /liked-posts-trends endpoint: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving liked posts trends.")

@eda_route.post("/missing-skills", response_model=MissingSkillsResponse)
async def get_missing_skills_endpoint(request: UserRequest) -> MissingSkillsResponse:
    """
    Endpoint to retrieve missing skills for a specific user.
    Args:
        request (UserRequest): The email of the user to retrieve missing skills for.
    Returns:
        MissingSkillsResponse: A dictionary with two keys:
            - "en": List of missing skills in English.
            - "fr": List of missing skills in French.
    """
    try:
        with datamanager_service() as mongodb_manager:
            user_data_manager = user_data_manager_service(mongodb_manager)
            missing_skills = user_data_manager.missings_skills_user(request.email)

            if not missing_skills["en"] and not missing_skills["fr"]:
                return MissingSkillsResponse(
                    en=[],
                    fr=[]
                )

            return MissingSkillsResponse(
                en=missing_skills["en"],
                fr=missing_skills["fr"]
            )
    except Exception as e:
        logger.error(f"Error in /missing-skills endpoint: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving missing skills.")

@eda_route.get("/regions-usage", response_model=RegionsUsageResponse)
async def get_regions_usage_endpoint() -> RegionsUsageResponse:
    """
    Endpoint to retrieve the usage of regions (city_for_filter) in results_prediction.
    Returns:
        RegionsUsageResponse: A dictionary where keys are region names and values are their counts.
    """
    try:
        with datamanager_service() as mongodb_manager:
            user_data_manager = user_data_manager_service(mongodb_manager)
            regions_usage = user_data_manager.get_regions_usage()
            if not regions_usage:
                raise HTTPException(status_code=404, detail="No regions usage data found.")
            mapped_counts = {
                    REGION_MAPPING.get(region, region): count 
                    for region, count in regions_usage.items()
                }
            return RegionsUsageResponse(regions=mapped_counts)
    except Exception as e:
        logger.error(f"Error in /regions-usage endpoint: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving regions usage.")

@eda_route.get("/region-stats", response_model=RegionsUsageResponse)
async def get_region_stats_endpoint() -> RegionsUsageResponse:
    """
    Endpoint to retrieve the number of job offers per region from the merged CSV file.
    Returns:
        RegionsUsageResponse: A dictionary with region names as keys and offer counts as values.
    """
    try:
        blob_path = "summarize/merged/france.csv"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
            temp_file_path = temp_file.name
            
            try:
                blob_service.download_file(blob_path, temp_file_path)
                
                df = pd.read_csv(temp_file_path)
                
                region_counts = df['Region'].value_counts().to_dict()
                
                mapped_counts = {
                    REGION_MAPPING.get(region, region): count 
                    for region, count in region_counts.items()
                }
                return RegionsUsageResponse(regions=mapped_counts)
                
            finally:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
    except Exception as e:
        logger.error(f"Error in /region-stats endpoint: {e}")
        raise HTTPException(
            status_code=500, 
            detail="An error occurred while retrieving region statistics."
        )