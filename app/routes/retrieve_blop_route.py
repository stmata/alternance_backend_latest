import csv
from fastapi import APIRouter, HTTPException
from app.services import blob_service 
from app.logFile import logger
import os
import tempfile
from pydantic import BaseModel

retrieve_filerouter = APIRouter(prefix="/retrieval")

class FileRetrievalRequest(BaseModel):
    platform: str
    region: str

@retrieve_filerouter.post("/file")
async def retrieve_file(request: FileRetrievalRequest):
    """
    Endpoint to retrieve a file from Azure Blob Storage based on site name and region.

    Args:
        platform (str): The name of the site (e.g., 'apec', 'indeed', 'linkedin').
        region (str): The region name (e.g., 'france'). For this version, region is always 'france', with 'Location' column containing cities and 'Region' column categorizing into 'ile_de_france', 'hauts_de_france', or 'Others' for other regions.

    Returns:
        dict: A JSON representation of the CSV content or an error if the file does not exist.
    """
    # Format the blob path based on the inputs
    blob_path = f"{request.platform}/{request.region}.csv"
    
    try:
        # Create a temporary file to download the blob
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
            download_path = temp_file.name
        
        # Download the file from Azure Blob Storage
        blob_service.download_file(blob_path, download_path)
        
        # Read the file content (assuming it's a CSV file)
        with open(download_path, 'r') as file:
            reader = csv.DictReader(file)
            content = [row for row in reader]
        
        # Return the file content as a JSON response
        return {"message": f"Successfully retrieved {blob_path}", "content": content}
    
    except FileNotFoundError:
        logger.error(f"File not found: {blob_path}")
        raise HTTPException(status_code=404, detail=f"File {blob_path} not found in Azure Blob Storage")
    
    except Exception as e:
        logger.error(f"Error retrieving file {blob_path}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving the file: {str(e)}")
    
    finally:
        # Optionally delete the local temporary file
        if os.path.exists(download_path):
            os.remove(download_path)

@retrieve_filerouter.post("/file-with-summarize")
async def retrieve_file_with_summarize(request: FileRetrievalRequest):
    """
    Endpoint to retrieve a file from Azure Blob Storage based on site name and region.

    Args:
        platform (str): The name of the site (e.g., 'apec', 'indeed', 'linkedin').
        region (str): The region name (e.g., 'france'). For this version, region is always 'france', with 'Location' column containing cities and 'Region' column categorizing into 'ile_de_france', 'hauts_de_france', or 'Others' for other regions.

    Returns:
        dict: A JSON representation of the CSV content (which includes a 'Summarize' field)
              or an error if the file does not exist.
    """
    # Format the blob path based on the inputs, now pointing to the 'summarize' directory
    blob_path = f"summarize/{request.platform}/{request.region}.csv"
    
    try:
        # Create a temporary file to download the blob
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
            download_path = temp_file.name
        
        # Download the file from Azure Blob Storage
        blob_service.download_file(blob_path, download_path)
        
        # Read the file content (assuming it's a CSV file containing a 'Summarize' field)
        with open(download_path, 'r') as file:
            reader = csv.DictReader(file)
            #content = [row for row in reader] 
            # Filter rows where either 'Title' or 'Summary_fr' contains 'Alternance' or 'Alternant'
            content = [
                row for row in reader 
                if ("Alternance" in row.get("Title", "") or "Alternant" in row.get("Title", "")) or
                   ("Alternance" in row.get("Summary_fr", "") or "Alternant" in row.get("Summary_fr", ""))
            ] 
        # Return the file content as a JSON response
        return {"message": f"Successfully retrieved {blob_path}", "content": content}
    
    except FileNotFoundError:
        logger.error(f"File not found: {blob_path}")
        raise HTTPException(status_code=404, detail=f"File {blob_path} not found in Azure Blob Storage")
    
    except Exception as e:
        logger.error(f"Error retrieving file {blob_path}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving the file: {str(e)}")
    
    finally:
        # Optionally delete the local temporary file
        if os.path.exists(download_path):
            os.remove(download_path)
