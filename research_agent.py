from tavily import TavilyClient
import os
from dotenv import load_dotenv
load_dotenv()


class Research:
    # this class is to perform the web search and summarize and synthesize the information

    def search(self, query):
        # perform web search using the client

        #1. make a search api call tavily client to get the raw search results 

        # api key 
        tavily_key = os.getenv("TAVILY_API_KEY")
        client = TavilyClient(api_key=tavily_key)

        response = client.search(query , max_results=3)
        
        tavily_answer = response['answer'] # this is the main summary of all the search results 
        results = response['results']

        page_info = [] # this is to store individual page information 

        # extract the content and the url from the results
        for ele in results:
            content = ele['content']
            url = ele['url']
            # add this to the page info 
            page_info.append({
                "url": url,
                "content": content
            })

        print(f"Output of tavily api is : \n{page_info}\n\n")
        #2 use gemini api to summarize the url 
        page_summaries = self.summarize(page_info)

        final_json = self.synthesize(page_summaries , tavily_answer)
        return final_json


    def summarize(self, page_info):
        # summarize the content using the client
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

        #initiliza the model 
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
            summaries.append(currr_summary)

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

        from langchain.prompts import SystemMessagePromptTemplate , HumanMessagePromptTemplate , ChatPromptTemplate

        system_prompt = SystemMessagePromptTemplate.from_template(
            """
            **Role:** You are an expert computer science educator specializing in Data Structures and Algorithms (DSA).

            **Task:** Your goal is to analyze the provided research  and extract key information. The context includes a primary summary and content from several web pages. You must structure this information and respond ONLY with a single, well-formed JSON object.

            **JSON Schema:**
            - "source_summary": A concise, one or two-sentence summary of the topic based on all provided context.
            - "key_concepts": A list of the most important technical terms, algorithms, and concepts.
            - "example_problems": A list of specific, self-contained problem statements or questions found within the text.
            - "code_snippets": A list of objects with "language" and "code" keys .

            **Research Context to Analyze:**
            ---
            {context}
            ---

            **Final Instruction:** Now, analyze all the provided context and generate the final, structured JSON object.

            """
        )

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

        
        prompt2 = PromptTemplate(template=system_prompt_template, input_variables=["context"])
        #chain = prompt2 | llm | JsonOutputParser()
        #final_output = chain.invoke({"context": combined_context})

        ############## making changes to the output parsing ##############
        from langchain.output_parsers import OutputFixingParser
        
        # 1. parsing using partial_parse insted of JsonOutputParser
        raw_output = (prompt2 | llm).invoke({"context": combined_context})
        #2. forse parse into json
        final_forced_output = {}
        try:
            final_forced_output = parse_partial_json(raw_output)
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            final_forced_output = {}

        # save the final context and the code output
        try:
            with open("full_context.txt", "w", encoding="utf-8") as f:
                f.write(combined_context)
        except Exception as e:
            print(f"Error saving final context: {e}")

        try:
            with open("output_2.json", "w", encoding="utf-8") as f:
                import json
                json.dump(final_forced_output, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving final output: {e}")

        return final_forced_output


