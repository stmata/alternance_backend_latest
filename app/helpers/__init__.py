"""
This module initializes key utilities for web scraping and prompt management.

It imports and exposes the following utilities:
- BeautifulSoup: A library for parsing HTML and XML documents, facilitating web scraping tasks.
- Prompt: A utility for managing and generating prompts used in natural language processing tasks.

Attributes:
    beautifulSoup_ (BeautifulSoup): The BeautifulSoup class for HTML/XML parsing.
    prompt_helpers (Prompt): An instance of the Prompt utility for handling prompt generation and management.
"""

from bs4 import BeautifulSoup
from .prompt_helpers import Prompt

beautifulSoup_ = BeautifulSoup
prompt_helpers = Prompt