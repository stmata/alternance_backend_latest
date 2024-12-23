from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services import blob_service
from app.services import data_analysis_service
from app.logFile import logger

eda_route = APIRouter(prefix="/eda")

class FileRetrievalRequest(BaseModel):
    platform: str
    region: str

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
