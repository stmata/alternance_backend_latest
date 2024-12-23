from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.services.summarize_desc import file_parser_and_summarize_service

pdf_input_summarize_router = APIRouter(prefix="/summarize")


# Define the input structure for text
class TextInput(BaseModel):
    text: str

   

@pdf_input_summarize_router.post("/text")
async def summarize_text(input: TextInput):
    """
    Endpoint to summarize a given text.
    
    Args:
        input (TextInput): Input containing the text to summarize.
        
    Returns:
        dict: A dictionary with the summarized text.
        
    Raises:
        HTTPException: If an error occurs during summarization.
    """
    try:
        # Summarize the provided text
        summarized_text = await file_parser_and_summarize_service.summarize_text(input.text)
        return {"summary": summarized_text}
    except Exception as e:
        # Raise an HTTP exception with a 400 status code in case of error
        raise HTTPException(status_code=400, detail=str(e))

@pdf_input_summarize_router.post("/file")
async def summarize_file(file: UploadFile = File(...)):
    """
    Endpoint to extract a summary from a PDF file.
    
    Args:
        file (UploadFile): The uploaded PDF file from which to extract the summary.
        
    Returns:
        dict: A dictionary with the summarized text extracted from the PDF file.
        
    Raises:
        HTTPException: If an error occurs during file processing or summarization.
    """
    try:
        # Read the content of the uploaded PDF file
        file_content = await file.read()

        # Summarize the content of the PDF file
        summarized_text = await file_parser_and_summarize_service.summarize_file(file_content, file.filename)

        #return {"summary": summarized_text}
        return {
            "summary": summarized_text,
            "filename": file.filename 
        }
    
    except Exception as e:
        # Raise an HTTP exception with a 400 status code in case of error
        raise HTTPException(status_code=400, detail=str(e))