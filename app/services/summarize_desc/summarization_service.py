import openai
from dotenv import load_dotenv
from app.helpers import prompt_helpers

load_dotenv()

class Summarizer:
    def __init__(self):
        """
        Initializes the GPTSummarizer class with the gpt-4o model deployed in Azure OpenAI.
        """
        openai.api_type = "azure"
        openai.api_version = "2023-06-01-preview"
        self.model = "gpt-4o-mini"  

    async def summarize(self, text: str, prompt: str = None) -> str:
        """
        Summarizes the provided job description with a structured bilingual output.

        Args:
            text (str): The job description to be summarized.

        Returns:
            str: The structured bilingual summary of the input job description.
        """
        # Load the default prompt for job summarization
        if not prompt:
            prompt = prompt_helpers.default_job_summary_prompt()
        
        # Make the API call with the customized prompt and job description
        response = openai.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an assistant specialized in job summarization."},
                {"role": "user", "content": f"{prompt}\n\n{text}"}
            ],
            max_tokens=750,  
            temperature=0.3,
            n=1,
            stop=None,
        )
        # Return the formatted bilingual summary
        return response.choices[0].message.content
