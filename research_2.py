# this is a new research agent that made to make the llm outputs more structured 
from tavily import TavilyClient
import os
from dotenv import load_dotenv
load_dotenv()
from pydantic import BaseModel, ValidationError , Field


"""
- "source_summary": A concise, one or two-sentence summary of the topic based on all provided context.
            - "key_concepts": A list of the most important technical terms, algorithms, and concepts.
            - "example_problems": A list of specific, self-contained problem statements or questions found within the text.
            - "code_snippets": A list of objects with "language" and "code" keys .

"""

# write a class to standerdise the final llm output
class JsonOutput(BaseModel):

    """This class defines the structured output to match the synthesis prompt."""
    
    title: str = Field(description="A clear title for the overall topic.")
    description: str = Field(description="A concise summary of the algorithm.")
    algorithm_steps: list[dict] = Field(description="A list of objects, each with 'step' and 'description'.")
    coding_implementations: list[dict] = Field(description="A list of objects, each with 'language', 'description', and 'code'.")
    specialized_implementations: list[dict] = Field(description="A list describing variations or advanced uses.")
    benefits: list[dict] = Field(description="A list of the key advantages of using the algorithm.")

class ResearchAgent:
    
    # this class needs to have 3 methods , search  , summarize and synthesize

    def search(self, query):
        # 1 --> get the api key and perform a tavily search 
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        client = TavilyClient(api_key=tavily_api_key)

        response = client.search(query , max_results=3)
        # extract teh main answer and the rest of the data saperately
        answer = response['answer'] # --> store this saperately
        results = response['results'] 

        # gather all the individual page info 
        page_info = []

        for ele in results:
            content = ele['content']
            url = ele['url']
            page_info.append({
                "url": url,
                "content": content
            })

        # pass the answer and the page info to the chain to get a better summary
        page_summaries = self.summarize(page_info)
        final_summary = self.synthesize(page_summaries , answer) # this response will be in the form of an object 
        return final_summary


    def summarize(self, page_info):
        # here use the google gemini api to generate individual page summaries

        from google import genai
        from google.genai import types
        from google.genai.types import Tool, GenerateContentConfig

        # provide the url and content ot the gemini to extract detailed summary 

        #1. initilize the client
        client = genai.Client()

        system_prompt = """You are a helpful assistant. 
        You specialize in coding algorithms and analyzing 
        user coding requirements,you are extremely good at reading 
        and understanding coding and algorithm related articles. Your main task is to summarize a given website in detail covering all the key aspects
        and including all the technical and coding related aspects."""

        tools = [
            {"url_context": {}},
        ]

        #initialize the model
        search_agent = client.chats.create(
            model="gemini-2.5-flash",
            config=GenerateContentConfig(max_output_tokens=2048, system_instruction=system_prompt, tools=tools)
        )

        # get the generated summary for each url 
        summaries = []
        for ele in page_info:
            content = ele['content']
            url = ele['url'] 
            # now give these 2 to the gemini api to generrate a summary 
            currr_summary = search_agent.send_message(f"""Summarize the following content from the url {url} in detail covering all the key aspects and including all the technical and coding related aspects.
            You can also refer to the content {content} snippet , it can act like like a gist or abstract about that website , you the content 
            if it helps you in generating better summary otherwize you can ignore this content snippet  """)
            summaries.append(currr_summary.text)

        print(f"Output of gemini api is : \n{summaries}\n\n")
        return summaries


    def synthesize(self, information , tavily_answer):
        # using langchai packages for better data processing
        from langchain.prompts import PromptTemplate
        from langchain.output_parsers import JsonOutputToolsParser
        from langchain_core.utils.json import parse_partial_json
        from langchain_core.output_parsers.json import JsonOutputParser

        # this function is to combine the summaries and all the collected info into a single well structured json 
        combined_context = f"Primary Summary from Search Engine:\n{tavily_answer}\n\n"
        for i, summary in enumerate(information):
            combined_context += f"Content from Web Page {i+1}:\n{summary}\n\n"

        # use ollama llm to re format and structure this context into the needed format
        from langchain_ollama import OllamaLLM
        llm = OllamaLLM(model="llama3", temperature=0.7)
        #llm = llm.with_structured_output(JsonOutput)
        from langchain.prompts import SystemMessagePromptTemplate , HumanMessagePromptTemplate , ChatPromptTemplate


        # trying a new prompt
        system_prompt_template = """
            **Role:** You are an expert data synthesizer and computer science educator.

            **Task:** Your goal is to analyze the research context, which is compiled from MULTIPLE web pages, and synthesize all of it into a SINGLE, UNIFIED, and DE-DUPLICATED JSON object. Your response must be ONLY the final JSON object.

            **Instructions:**
            1.  **Synthesize, Don't List:** Do not create separate JSON objects for each source. Merge the findings into one definitive object.
            2.  **Combine and Refine:** If multiple sources describe the same algorithm step or concept, combine their descriptions into the most clear and comprehensive version.
            3.  **Include Code:** When you identify a coding implementation, you MUST include the actual code block in a "code" field.

            **JSON Schema:**
            - **`title`**: A clear title for the overall topic (e.g., "Comprehensive Guide to Binary Search").
            - **`description`**: A concise, one or two-sentence summary of the algorithm based on all provided context.
            - **`algorithm_steps`**: A list of objects, each with "step" and "description".
            - **`coding_implementations`**: A list of objects, each with "language", "description", AND "code".
            - **`specialized_implementations`**: A list describing variations or advanced uses.
            - **`benefits`**: A list of the key advantages of using the algorithm.

            **Research Context to Analyze:**
            ---
            {context}
            ---

            **Final Instruction:** Now, analyze all the provided context and generate the single, synthesized JSON object.
        """

        # using gemini insted of ollama 
        from langchain.chat_models import init_chat_model
        llm = init_chat_model("gemini-2.5-flash", temperature=0, api_key=os.getenv("GEMINI_API_KEY") , model_provider="google_genai")
        
        parser = JsonOutputParser(pydantic_object=JsonOutput , with_strict=True)

        prompt = PromptTemplate(
            template=system_prompt_template + "\n\n{context}\n\nReturn only JSON." +  "Output MUST be ONLY valid JSON. No explanations, no markdown, no text outside JSON." ,
            input_variables=["context"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        
        structured_llm = llm.with_structured_output(JsonOutput , strict=True)
        chain = prompt | structured_llm 

        raw_output: JsonOutput = chain.invoke({"context": combined_context})

        print(f"The final output of the model is:\n {raw_output} , and the type of it is :\n{type(raw_output)}")
        return raw_output.model_dump_json(indent=2)


import json

def is_valid_json(json_string: str) -> bool:
    try:
        json.loads(json_string)  # try parsing
        return True
    except (ValueError, TypeError):
        return False


def to_json_safe(obj):
    # If it's already a dict, convert to JSON string
    if isinstance(obj, dict):
        return json.dumps(obj, indent=2)
    
    # If it's a string, check if it's valid JSON
    if isinstance(obj, str):
        if is_valid_json(obj):
            return obj  # already JSON
        else:
            raise ValueError("String is not valid JSON")
    
    raise TypeError("Unsupported type for JSON conversion")


if __name__ == "__main__":
    agent = ResearchAgent()
    final_result = agent.search("binary search algorithm")
    with open("output_2_gemini.json", "w", encoding="utf-8") as f:
        f.write(final_result)
    