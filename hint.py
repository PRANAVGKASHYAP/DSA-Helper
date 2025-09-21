import json
from langchain.prompts import PromptTemplate
from langchain.output_parsers import JsonOutputToolsParser
#langchain_core.output_parsers.json.JsonOutputParser
from langchain_core.output_parsers.json import JsonOutputParser  
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import OllamaLLM
import os
from dotenv import load_dotenv
load_dotenv()

# define the class for structuring of hint
from pydantic import BaseModel, ValidationError , Field

class helpful_hint(BaseModel):
    """ this is a class that defines how each test case needs to be defined """
    hint: str = Field(..., description="The hint to help solve the problem ,  this defined the hint that will help the user to solve the problem")
    explanation: str = Field(..., description="A brief explanation of why this hint is helpful for the given problem")



class HintGenerator:

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
        # other params...
        )

        # get the algorithm in focus 
        
    structured_llm = llm.with_structured_output(helpful_hint)

    @staticmethod
    def generate_hint(topic , title , description , test_cases):
        # use the geminimodel to generate the hint

        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                (
                    """You are an expert coding assistant. Your task is to generate a **helpful hint** for a programming problem given its title, problem description, and test cases. 

                    Rules for generating the hint:
                    1. The hint should help the user solve the problem without giving the full solution.
                    2. Focus on guiding the user towards the correct algorithm, approach, or edge case consideration.
                    3. Analyze the problem description and test cases to identify important patterns or constraints.
                    4. Keep the hint concise, clear, and actionable (1-3 sentences).
                    5. Avoid giving explicit code unless specifically requested.
                    6. Use natural language that is easy for a learner to understand.

                    Input will include:
                    - title: The title of the problem
                    - description: The detailed problem statement
                    - test_cases: A list of sample input/output to illustrate the problem 
                    - topic: The main algorithm or concept the problem is focused on
                    """
                )
            ),
            (
                "user",
                (
                    "Here is the title:\n\n```json\n{title}\n```\n\n"
                    "Here is the description:\n\n```json\n{description}\n```\n\n"
                    "Here are some test cases:\n\n```json\n{test_cases}\n```"
                    "The main topic is: {topic} . this is the algorithm on which the coding problem is based \n\n"
                    "Now generate a helpful hint to help me solve the problem"
                )
            ),
        ])

        chain = prompt | HintGenerator.structured_llm

        gemini_response = chain.invoke(
        {
            "title": title,
            "description": description,
            "test_cases": json.dumps(test_cases),
            "topic": topic
        }
        )

        return gemini_response
    
