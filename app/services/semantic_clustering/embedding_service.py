from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
import numpy as np
import os
from dotenv import load_dotenv

# Set Azure environment variables
load_dotenv()

class OpenAIEmbeddingService:
    def __init__(
        self, 
        deployment_name: str = "text-embedding-3-large",
        model_name: str = "text-embedding-3-large",
        api_version: str = "2024-02-15-preview"
        ):
        
        """
        Initializes the Azure OpenAI embedding service.
        
        :param azure_endpoint: Azure OpenAI endpoint URL
        :param api_key: Azure OpenAI API key
        :param deployment_name: Name of the deployment in Azure (default 'embedding')
        :param model_name: Name of the model to use (default 'text-embedding-ada-002')
        :param api_version: Azure API version to use (default '2024-02-15-preview')
        """
        
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        # Initialize the embedding model
        self.embed_model = AzureOpenAIEmbedding(
            model=model_name,
            api_key=api_key,
            azure_deployment=deployment_name,
            api_version=api_version,
            embed_batch_size=512

    )
    
    def get_openai_embeddings(self, paragraphs):
        """
        Generates Azure OpenAI embeddings for a list of paragraphs.
        
        :param paragraphs: List of paragraphs to encode
        :return: Embeddings as a numpy array
        """
        # Generate embeddings for each paragraph
        embeddings = [self.embed_model.get_text_embedding(paragraph) for paragraph in paragraphs]
        return np.array(embeddings)


