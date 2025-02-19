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
        #prompt = ("Given the following candidate summary and job description, generate a personalized and professional cover letter in Markdown format that feels genuine and crafted by a human."
        #          "Ensure the tone is polite, engaging, and natural, avoiding any robotic or overly formal phrasing. The letter should include the following structure:"
        #          "1. A placeholder for the Sender's Address, Recipient's Address, and Date."
        #          "2. A Subject line that clearly states the position being applied for."
        #         "3. An opening paragraph that introduces the candidate, mentions the job title, and expresses genuine interest in both the role and the company, demonstrating a strong understanding of the company’s mission or values."
        #          "4. A second paragraph that highlights specific skills and relevant experiences from the candidate summary that directly match the job description, weaving these into a brief story or achievement to make them feel natural."
        #          "5. A third paragraph that addresses any transitions or gaps in the candidate's career and explains how these experiences have enriched their perspective, adding value to the role they are applying for."
        #          "6. A closing paragraph that shows genuine enthusiasm for the position, thanks the employer, and expresses eagerness to discuss how the candidate can contribute to the company's success."
        #          "7. Include a Signature block with placeholders for Name and Contact Information."
        #          "Tone and Length:"
        #          "1. The tone should be human, approachable, and professional. Avoid overly formal or robotic language."
        #          "2. The letter should be concise, natural, and flow smoothly, ideally within 3-4 paragraphs. The result should feel tailored and thoughtful, as if written by the candidate themselves."
        #          "\nThe output should include both English and French versions, formatted with clear headings and bullet points for each section, in a structured manner as follows:\n"
        #          "### English Version\n"
        #          "\n### Version Française\n"
        #          )
        prompt = (
            "Using the candidate’s summary and the provided job description, generate a **well-crafted, personalized, and compelling** cover letter in Markdown format. "
            "Ensure that the letter reads as if written by the candidate themselves, exhibiting a natural flow, professionalism, and enthusiasm while avoiding generic, robotic, or overly formulaic phrasing.\n\n"
            "**Structure of the Cover Letter:**\n"
            "1. **Header Section:**\n"
            "   - Placeholders for **Sender’s Address, Recipient’s Address, and Date**.\n"
            "   - A clear **Subject line** stating the position being applied for.\n\n"
            "2. **Opening Paragraph:**\n"
            "   - A warm and engaging introduction that immediately captures the employer’s attention.\n"
            "   - Clearly states the **job title** and expresses sincere enthusiasm for the role and company.\n"
            "   - Demonstrates a **genuine understanding of the company’s mission, values, or recent achievements**.\n\n"
            "3. **Core Strengths & Achievements:**\n"
            "   - Highlights key **skills and experiences** that **directly match** the job description.\n"
            "   - Integrates these into a **brief and compelling story or accomplishment** to add credibility.\n"
            "   - Uses natural transitions to ensure a seamless flow of ideas.\n\n"
            "4. **Addressing Career Transitions or Gaps (if applicable):**\n"
            "   - Provides a **brief, positive, and professional explanation** of any transitions, career shifts, or gaps.\n"
            "   - Emphasizes how these experiences have **enriched the candidate’s perspective and value** for the applied role.\n\n"
            "5. **Closing Paragraph:**\n"
            "   - Expresses **genuine enthusiasm** for the opportunity and gratitude for the employer’s time.\n"
            "   - Reaffirms the candidate’s desire to discuss how their expertise can contribute to the company’s success.\n"
            "   - Ends with a **polite yet confident call to action**, such as a willingness to meet or discuss further.\n\n"
            "6. **Signature Block:**\n"
            "   - Includes placeholders for **Name, Contact Information, and any relevant LinkedIn or portfolio links**.\n\n"
            "**Tone & Style:**\n"
            "✔ **Human, engaging, and professional:** Avoids generic AI-generated phrasing.\n"
            "✔ **Academically refined but approachable:** Uses clear, articulate, and well-structured language.\n"
            "✔ **Concise and well-paced:** Ideally within 3-4 paragraphs, ensuring **brevity without sacrificing depth**.\n"
            "✔ **Tailored & thoughtful:** Feels uniquely written for the candidate, avoiding clichés or generic statements.\n\n"
            "**Final Check Before Output:**\n"
            "✔ Ensure all elements align naturally with the candidate’s profile and the job description.\n"
            "✔ Avoid redundancy or excessive formalism; maintain a smooth and logical flow.\n"
            "✔ Guarantee coherence between the **candidate’s strengths and the job role**.\n\n"
            "The final output must be bilingual, formatted with clear headings and bullet points for each section, in a structured manner as follows:\n"
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
        # prompt = (
        #     "Compare the candidate's summary with the given job description and:\n"
        #     "1. Identify key skills, qualifications, or experiences required in the job description that are absent or not clearly mentioned in the candidate's summary.\n"
        #     "2. Consider semantic similarity: If a skill is mentioned in a different but equivalent way, do not mark it as missing.\n"
        #     "   - For example, if the job requires 'Business English' and the candidate is 'fluent in English,' do NOT consider Business English as missing.\n"
        #     "   - If the job requires 'project management' and the candidate states 'led multiple projects,' do NOT consider it missing.\n"
        #     "3. Do NOT include unnecessary adjectives or adverbs—only list essential skills and qualifications.\n"
        #     "4. Ensure that the final output is reviewed before returning and only includes genuinely missing elements.\n"
        #     "5. Present the results in a clear and structured format with distinct headings and bullet points as follows:\n"
        #     "### English Version\n"
        #     "\n### Version Française\n"
        # )
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
        # prompt = (
        #     "Compare the candidate's summary with the provided job description, and follow these precise instructions:\n\n"
        #     "1. Identify skills, qualifications, or experiences that are **explicitly or semantically present** in both the job description and the candidate's summary.\n"
        #     "   - Consider variations in wording, but ensure they retain the same meaning (e.g., 'project management' and 'managed multiple projects' should be considered a match).\n"
        #     "   - If a skill is only **implied** but not directly stated in both, do NOT include it.\n"
        #     "2. Ensure **each skill is clearly aligned with the job description**—do not add redundant explanations.\n"
        #     "3. Only return essential skills without unnecessary adjectives or embellishments (e.g., write 'Python' instead of 'Strong Python programming skills').\n"
        #     "4. **Do not assume or infer additional abilities** beyond what is explicitly provided.\n"
        #     "5. **Before finalizing the list, double-check each skill** to confirm it is genuinely present in both sources and not just a partial or loosely related match.\n"
        #     "6. Present the output in a structured format with clear headings and bullet points, separating the English and French sections as follows:\n"
        #     "### English Version\n"
        #     "\n### Version Française\n"
        # )

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
    
    @staticmethod
    def missing_skills_business_school_prompt() -> str:
        """
        Returns a prompt template for analyzing and summarizing missing skills
        in a business school context, with emphasis on clear gaps identification.
        """
        prompt = (
            "You are an expert career advisor for a prestigious business school. Your task is to analyze the missing skills "
            "and present them in a clear, direct format that emphasizes the GAPS in the student's profile. "
            "\n\n"
            "Given Skills:\n{skills_data}"
            "\n\n"
            "Instructions:\n"
            "- Analyze the provided skills and determine what is missing.\n"
            "- Convert missing skills into concise statements.\n"
            "- Start each statement with action words like: 'Needs', 'Lacks', 'Requires', 'Missing'.\n"
            "- Do NOT use: 'Mastery in', 'Proficiency in', 'Excellence in'.\n"
            "- Keep each statement under 10 words when possible.\n"
            "- Organize statements into relevant categories (Business, Technical, Professional, Market Knowledge).\n"
            "\n"
            "**Important Formatting Rules:**\n"
            "- DO NOT return a JSON structure.\n"
            "- Return ONLY two separate lists: one in English, one in French.\n"
            "- Each missing skill must be a bullet point using '-'.\n"
            "- Do NOT use additional headers, sections, or tables.\n"
            "\n"
            "**Expected Output Example:**\n"
            "en:\n"
            "- Needs data analysis skills for business decisions\n"
            "- Lacks project management certification\n"
            "- Missing digital marketing experience\n"
            "\n"
            "fr:\n"
            "- Manque de compétences en analyse de données\n"
            "- Besoin d'une certification en gestion de projet\n"
            "- Absence d'expérience en marketing digital\n"
            "\n"
            "Key Words to Start Statements:\n"
            "EN: Needs, Lacks, Requires, Missing, Must develop, To acquire\n"
            "FR: Besoin de, Manque de, Absence de, À développer, Nécessite, À acquérir\n"
            "\n"
            "Please return the missing skills as two separate lists formatted with bullet points, one in English and one in French."
        )

        return prompt