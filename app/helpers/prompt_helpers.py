class Prompt:
    """A service to hold predefined prompts for other tasks."""
    
    @staticmethod
    def default_job_summary_prompt() -> str:
        """
        Returns the default prompt for summarizing job descriptions.

        Returns:
            str: The default prompt for job summarization.
        """
        prompt = ("Given the following text, first **extract the job title**, then summarize the **job description** by including only: "
          "1. **Primary Responsibilities**: List the main tasks the candidate will perform. "
          "2. **Key Required Skills**: Include only the skills and qualifications necessary for performing the job. "
          "3. **Main Objectives**: Summarize what success looks like for this role. "
          "Exclude any information about company background, benefits, team dynamics, or non-essential context. "
          "Focus exclusively on the actionable requirements and expectations for the role. "
          "The output should include both English and French summaries, formatted with clear headings and bullet points for each section, "
          "in a structured manner as follows:\n"
          "### English Summary\n"
          "**Job Title:** [title]\n"
          "**Job Description:**\n"
          "- **Primary Responsibilities:**\n"
          "  - [responsibility 1]\n"
          "  - [responsibility 2]\n"
          "  - [...]\n"
          "- **Key Required Skills:**\n"
          "  - [skill 1]\n"
          "  - [skill 2]\n"
          "  - [...]\n"
          "- **Main Objectives:**\n"
          "  - [objective 1]\n"
          "  - [objective 2]\n"
          "  - [...]\n"
          "\n### Résumé Français\n"
          "**Titre du Poste:** [titre]\n"
          "**Description du Poste:**\n"
          "- **Responsabilités Principales:**\n"
          "  - [responsabilité 1]\n"
          "  - [responsabilité 2]\n"
          "  - [...]\n"
          "- **Compétences Clés Requises:**\n"
          "  - [compétence 1]\n"
          "  - [compétence 2]\n"
          "  - [...]\n"
          "- **Objectifs Principaux:**\n"
          "  - [objectif 1]\n"
          "  - [objectif 2]\n"
          "  - [...]"
            )
        
        return prompt
    
    @staticmethod
    def cv_summary_prompt() -> str:
        """
        Returns the prompt for summarizing candidate CVs.

        Returns:
            str: The prompt for CV summarization.
        """
        prompt = ("Extract and summarize the candidate’s CV by focusing on the following key elements: "
                "1. **Target Job Title**: Identify the position the candidate is seeking. "
                "2. **Core Skills and Competencies**: Extract the main technical and soft skills relevant to the position. "
                "3. **Professional Experience**: Summarize the most recent and relevant job experiences, including the main responsibilities and achievements. "
                "Exclude any details about hobbies, interests, or non-professional information. "
                "The final summary should highlight the candidate’s profile, ensuring a clear match with potential job offers based on title, skills, and experience.")
        
        return prompt

    @staticmethod
    def human_profile_summary_prompt() -> str:
        """
        Returns the prompt for analyzing and summarizing human profiles.

        Returns:
            str: The prompt for human profile summarization.
        """
        prompt = ("Analyze and summarize the given human profile by focusing on the following key elements: "
                "1. **Intent and Goal**: Identify the person's primary objective or motivation (e.g., career aspirations, project goals, learning intentions). "
                "2. **Core Skills and Strengths**: Extract the main strengths and competencies relevant to their stated or implied objectives. "
                "3. **Background and Experience**: Summarize the person's most relevant experiences, including educational background, notable achievements, and any key responsibilities. "
                "4. **Constraints and Preferences**: Identify any stated or implied limitations, preferences, or special requirements the person has. "
                "The final summary should provide a coherent profile of the individual, making assumptions where necessary to fill gaps, and ensuring a clear representation of their intent, strengths, and potential fit for various opportunities based on goals, skills, and experience.")
        
        return prompt
    
    @staticmethod
    def cover_letter_prompt() -> str:
        """
        Returns the default prompt for generating a cover letter template based on a CV summary or human profile summary and job description.
        The cover letter will be structured in HTML or Markdown with placeholders for headers, addresses, and other key elements in both English and French.

        Returns:
            str: The bilingual prompt for cover letter generation.
        """
        prompt = ("Given the following candidate summary and job description, generate a personalized and professional cover letter in Markdown format that feels genuine and crafted by a human."
                  "Ensure the tone is polite, engaging, and natural, avoiding any robotic or overly formal phrasing. The letter should include the following structure:"
                  "1. A placeholder for the Sender's Address, Recipient's Address, and Date."
                  "2. A Subject line that clearly states the position being applied for."
                  "3. An opening paragraph that introduces the candidate, mentions the job title, and expresses genuine interest in both the role and the company, demonstrating a strong understanding of the company’s mission or values."
                  "4. A second paragraph that highlights specific skills and relevant experiences from the candidate summary that directly match the job description, weaving these into a brief story or achievement to make them feel natural."
                  "5. A third paragraph that addresses any transitions or gaps in the candidate's career and explains how these experiences have enriched their perspective, adding value to the role they are applying for."
                  "6. A closing paragraph that shows genuine enthusiasm for the position, thanks the employer, and expresses eagerness to discuss how the candidate can contribute to the company's success."
                  "7. Include a Signature block with placeholders for Name and Contact Information."
                  "Tone and Length:"
                  "1. The tone should be human, approachable, and professional. Avoid overly formal or robotic language."
                  "2. The letter should be concise, natural, and flow smoothly, ideally within 3-4 paragraphs. The result should feel tailored and thoughtful, as if written by the candidate themselves."
                  "\nThe output should include both English and French versions, formatted with clear headings and bullet points for each section, in a structured manner as follows:\n"
                  "### English Version\n"
                  "\n### Version Française\n"
                  )
        
        return prompt


    @staticmethod
    def missing_skills_prompt() -> str:
        """
        Returns the prompt for identifying missing skills in a CV summary or human profile summary compared to a job description.
        The output will be short, concise, and presented in bullet points in both English and French.

        Returns:
            str: The bilingual prompt for identifying missing skills.
        """

        prompt = ("Compare the following candidate summary with the given job description, and:"
                "1. Identify key skills, qualifications, or experiences from the job description that are absent or not clearly mentioned in the candidate's summary."
                "2.  For each missing skill or qualification, provide a short and specific phrase detailing what is missing."
                "3. Use bullet points for each missing element, keeping the explanation concise and focused."
                "\nThe output should include both English and French versions, presented in a clear and professional manner formatted with clear headings and bullet points as follows:\n"
                "### English Version\n"
                "\n### Version Française\n"
            )
        return prompt

   
    @staticmethod
    def matching_skills_prompt() -> str:
        """
        Returns a prompt for strictly identifying matching skills between a candidate's summary and a job description.
        The output will be concise and focus only on skills explicitly stated in both the summary and the job description, provided in both English and French.

        Returns:
            str: A bilingual prompt for identifying matching skills.
        """

        prompt = (
          "Compare the candidate summary below with the provided job description, and strictly follow these instructions:\n"
          "1. Only list the skills, qualifications, or experiences that are explicitly mentioned in both the job description and the candidate's summary.\n"
          "2. For each matching skill, provide a concise explanation of how it aligns with the job requirements.\n"
          "3. Use bullet points to present each matching element, ensuring the descriptions are clear and direct.\n"
          "4. Do not make any assumptions or guesses about the candidate's abilities beyond what is explicitly stated in their summary.\n"
          "\nThe output should include both English and French versions, presented in a clear and professional manner formatted with clear headings and bullet points as follows:\n"
          "### English Version\n"
          "\n### Version Française\n"
        )

        return prompt
    
    @staticmethod
    def generate_followup_question_prompt() -> str:
        """
        Returns the prompt for generating relevant follow-up questions based on candidate responses.

        Returns:
            str: The prompt for generating follow-up questions.
        """
        prompt = (
            "Based on the candidate's response to the previous question, generate a relevant follow-up question that:\n"
            "1. Delves deeper into specific aspects of their answer\n"
            "2. Clarifies any ambiguous points\n"
            "3. Explores practical applications of their experience\n"
            "\nProvide the follow-up question in both English and French, formatted as:\n"
            "{\n"
            '  "en": "[Follow-up question in English]",\n'
            '  "fr": "[Question de suivi en français]"\n'
            "}"
        )
        return prompt
    
    @staticmethod
    def generate_interview_questions_prompt() -> str:
        """
        Returns the prompt for generating interview questions based on job and candidate summaries.

        Returns:
            str: The prompt for generating interview questions.
        """
        prompt = ("Based on the following job summary and candidate profile, generate a list of relevant interview questions. "
                  "Ensure the questions assess the candidate's fit for the position, covering areas such as skills, experience, "
                  "and cultural fit. The output should be in a clear bullet-point format, with a mix of technical and behavioral questions, "
                  "structured as follows:\n"
                  "- Question 1: [Insert question]\n"
                  "- Question 2: [Insert question]\n"
                  "- [...]"
                 )
        
        return prompt

    @staticmethod
    def generate_interview_evaluation_prompt() -> str:
        """
        Returns the prompt for generating an evaluation of the interview.

        Returns:
            str: The prompt for generating interview evaluation.
        """
        prompt = ("Based on the job summary, candidate profile, and the responses provided during the interview, generate a comprehensive "
                  "evaluation of the candidate's performance. The evaluation should address strengths, weaknesses, and overall fit for the role. "
                  "Structure the evaluation clearly with sections for:\n"
                  "- Strengths: [Insert strengths]\n"
                  "- Areas for Improvement: [Insert weaknesses]\n"
                  "- Overall Assessment: [Insert assessment]\n"
                  "Conclude with recommendations for hiring or further steps."
                 )
        
        return prompt