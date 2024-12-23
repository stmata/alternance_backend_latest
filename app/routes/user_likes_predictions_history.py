from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.services import user_data_manager_service, datamanager_service
from app.logFile import logger


history_router = APIRouter(prefix="/history")

# Model for the verification code request
class UserIDRequest(BaseModel):
    user_id: str

# Model for the liked post
class LikedPostRequest(BaseModel):
    user_id: str
    job_post: dict

# Model for the disliked post
class RemoveLikedPostRequest(BaseModel):
    user_id: str
    job_post_url: str

# Model for adding CV resume
class CVResumeRequest(BaseModel):
    user_id: str
    cv_resume_content: str


@history_router.post("/add-cv-resume")
async def add_cv_resume(request: CVResumeRequest):
    """
    Add or update the CV resume for a given user ID.

    Args:
        request (CVResumeRequest): The request containing the user ID and CV resume content.

    Returns:
        dict: A message indicating success or failure.
    """
    try:
        with datamanager_service() as mongodb_manager:
            user_data_manager = user_data_manager_service(mongodb_manager)
            result_message = user_data_manager.add_cv_resume(request.user_id, request.cv_resume_content)

        return {"message": result_message}

    except Exception as e:
        logger.error(f"Error adding CV resume: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Error adding CV resume"}
        )


@history_router.post("/get-cv-resume")
async def get_cv_resume(request: UserIDRequest):
    """
    Retrieve the CV resume for a given user ID.

    Args:
        request (UserIDRequest): The request containing the user ID.

    Returns:
        dict: The CV resume content or a message if not found.
    """
    try:
        with datamanager_service() as mongodb_manager:
            user_data_manager = user_data_manager_service(mongodb_manager)
            cv_resume = user_data_manager.get_cv_resume(request.user_id)

        if cv_resume:
            return {"cv_resume": cv_resume}
        else:
            return {"message": "No CV resume found."}

    except Exception as e:
        logger.error(f"Error retrieving CV resume: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Error retrieving CV resume"}
        )


@history_router.post("/add-liked-post")
async def add_liked_post(request: LikedPostRequest):
    """
    Add a liked post for a given user ID.

    Args:
        request (LikedPostRequest): The request containing the user ID and job post data.

    Returns:
        dict: A message indicating success or failure.
    """
    try:
        with datamanager_service() as mongodb_manager:
            user_data_manager = user_data_manager_service(mongodb_manager)  
            user_data_manager.add_liked_post(request.user_id, request.job_post)

        return {"message": "Post aimé ajouté avec succès."}

    except Exception as e:
        logger.error(f"Error adding liked post: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Error adding liked post"}
        )

@history_router.post("/remove-liked-post")
async def remove_liked_post(request: RemoveLikedPostRequest):
    """
    Remove a liked post for a given user ID.

    Args:
        request (RemoveLikedPostRequest): The request containing the user ID and the job post URL to be removed.

    Returns:
        dict: A message indicating success or failure.
    """
    try:
        with datamanager_service() as mongodb_manager:
            user_data_manager = user_data_manager_service(mongodb_manager)
            result_message = user_data_manager.remove_liked_post(request.user_id, request.job_post_url)

        return {"message": result_message}

    except Exception as e:
        logger.error(f"Error removing liked post: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Error removing liked post"}
        )


@history_router.post("/get-liked-posts")
async def get_user_liked_posts(request: UserIDRequest):
    """
    Retrieve all liked posts for a given user ID.

    Args:
        request (UserIDRequest): The request containing the user ID.

    Returns:
        List[Dict]: A list of liked post information.
    """
    try:
        # Use the context manager for MongoDB service
        with datamanager_service() as mongodb_manager:
            user_data_manager = user_data_manager_service(mongodb_manager)  
            liked_posts = user_data_manager.get_user_liked_posts(request.user_id) 

        if liked_posts:
            return {"liked_posts": liked_posts}
        else:
            return {"message": "Aucun post aimé trouvé."}

    except Exception as e:
        logger.error(f"Error retrieving liked posts: {str(e)}")
        return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": "Error retrieving liked posts"}
        )

@history_router.post("/get-prediction-history")
async def get_user_prediction_hystory(request: UserIDRequest):
    """
    Retrieve all prediction results for a given user ID.

    Args:
        user_id (str): The string representation of the user's ObjectId.

    Returns:
        List[PredictionResult]: A list of prediction result information.
    """
    try:
        with datamanager_service() as mongodb_manager:
            user_data_manager = user_data_manager_service(mongodb_manager)  
            prediction_results = user_data_manager.get_user_prediction_results(request.user_id)

        if prediction_results:
            return {"prediction_results": prediction_results}
        else:
            return {"message": "No prediction results found."}

    except Exception as e:
        logger.error(f"Error retrieving prediction results: {str(e)}")
        return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"message": "Error retrieving prediction results"}
        )
