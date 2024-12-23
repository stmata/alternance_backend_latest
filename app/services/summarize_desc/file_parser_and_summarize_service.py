from io import BytesIO
from llama_parse import LlamaParse
from dotenv import load_dotenv
from llama_index.core.response_synthesizers import TreeSummarize
from app.helpers import prompt_helpers
from app.logFile import logger

load_dotenv()
parser = LlamaParse(result_type="markdown")  # "markdown" and "text" are available

class FileParserAndSummarizer:
    """A service for extracting text from files and summarizing it."""

    def __init__(self):
        """
        Initializes the Summarize service with a parser for extracting text.

        Attributes:
            parser (LlamaParse): An instance of LlamaParse for processing documents.
        """
        self.parser = LlamaParse(result_type="markdown")  # "markdown" and "text" are available

    async def extract_text(self, file_content: bytes, file_name: str) -> str:
        """
        Extracts text from a given file content.

        Args:
            file_content (bytes): The content of the file in bytes.
            file_name (str): The name of the file being processed.

        Returns:
            str: The extracted text from the file.
        """
        # Convert file content to BytesIO for in-memory handling
        pdf_stream = BytesIO(file_content)
        
        # Extra info with file name
        extra_info = {"file_name": file_name}

        # Await the asynchronous aload_data function with extra_info
        documents = await self.parser.aload_data(pdf_stream, extra_info=extra_info)

        # Extract text from documents
        extracted_text = "\n".join([doc.get_text() for doc in documents])

        return extracted_text
    
    async def summarize_file(self, file_content: bytes, file_name: str) -> str:
        """
        Summarizes the content of a file.

        Args:
            file_content (bytes): The content of the file in bytes.
            file_name (str): The name of the file being processed.

        Returns:
            str: The summary of the extracted text from the file.
        """
        extracted_text = await self.extract_text(file_content, file_name)

        prompt = prompt_helpers.cv_summary_prompt()
        # Once we have the extracted text, proceed with summarization
        summarizer = TreeSummarize(verbose=True)
        
        # Use the summarizer to generate the response (which is a string, not an object)
        response = await summarizer.aget_response(prompt, [extracted_text])
        logger.info(response)
        return response  
    
    async def summarize_text(self, input: str) -> str:
        """
        Summarizes the given text input.

        Args:
            input (str): The text to be summarized.

        Returns:
            str: The summary of the provided text.
        """
        prompt = prompt_helpers.human_profile_summary_prompt()
        logger.info(f'oooooooooooooo: {input}')
        # Once we have the extracted text, proceed with summarization
        summarizer = TreeSummarize(verbose=True)
        
        # Use the summarizer to generate the response (which is a string, not an object)
        response = await summarizer.aget_response(prompt, [input])
        logger.info(response)

        return response  
