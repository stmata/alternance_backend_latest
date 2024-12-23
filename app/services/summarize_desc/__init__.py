"""
This module initializes the services for job scraping and summarization.

It imports and instantiates the following services:
- LinkedInJobScraper: A service for scraping job listings from LinkedIn.
- Summarizer: A service for summarizing text content, particularly for job descriptions and CVs.
- FileParserAndSummarizer: A service for extracting text from various file formats and summarizing it.

Instances of these services are created for use throughout the application.

Attributes:
    summarization_service (Summarizer): An instance of the summarization service.
    file_parser_and_summarize_service (FileParserAndSummarizer): An instance of the file parsing and summarization service.
    linkedInJobScraper_service (LinkedInJobScraper): An instance of the LinkedIn job scraper service.
"""

from .summarization_service import Summarizer
from .file_parser_and_summarize_service import FileParserAndSummarizer

summarization_service = Summarizer()
file_parser_and_summarize_service = FileParserAndSummarizer()
