from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, field_validator
from typing import Optional
from app.services.semantic_clustering import predict_service
from app.services.semantic_clustering import clustering_training_service

predict_jobs_router = APIRouter(prefix="/analytics")


class SummarizedTextRequest(BaseModel):
    platform: str
    region: str = "france"
    summarized_text: str
    user_id: str
    type_summary: str
    filename: Optional[str] = None
    education_level: str
    city_for_filter: str

    @field_validator("education_level")
    def validate_education_level(cls, value):
        valid_levels = ['Bac+2', 'Bac+3', 'Bac+4', 'Master']
        if value not in valid_levels:
            raise ValueError(f"Invalid education level. Valid options are {valid_levels}.")
        return value

    @field_validator("city_for_filter")
    def validate_city_for_filter(cls, value):
        valid_cities = ['ile_de_france', 'hauts_de_france', 'Others']
        if value not in valid_cities:
            raise ValueError(f"Invalid city for filter. Valid options are {valid_cities}.")
        return value


@predict_jobs_router.post("/predict-summary")
async def predict_from_summary(request: SummarizedTextRequest):
    """
    Endpoint to predict cluster from an already summarized text.

    Args:
        request (SummarizedTextRequest): Contains the summarized text, platform, region (always 'france'), user_id, type of summary (cv or prompt),
        education_level (str): The education level (e.g., 'Bac+2', 'Bac+3', 'Bac+4', 'Master').
        city_for_filter (str): The city filter for prediction ('ile_de_france', 'hauts_de_france', or 'others').

    Returns:
        dict: A dictionary containing the prediction results.

    Raises:
        HTTPException: If an error occurs during prediction.
    """
    try:
        results = await predict_service.predict_cluster(request.summarized_text, request.platform, request.region, request.user_id, request.type_summary,request.filename, request.education_level, request.city_for_filter)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@predict_jobs_router.post("/process-all-clustering-in-background")
async def run_all_clustering_in_background(background_tasks: BackgroundTasks):
    """
    Endpoint to trigger the clustering process for all platforms and regions in the background.

    Args:
        background_tasks (BackgroundTasks): FastAPI's BackgroundTasks object to manage background tasks.

    Returns:
        dict: A message indicating that the clustering process has started and is running in the background.
    
    Raises:
        HTTPException: If an error occurs during the clustering process.
    """
    try:
        background_tasks.add_task(clustering_training_service.process_clustering)

        return {"message": "Clustering process is in progress. You will be notified once completed."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))