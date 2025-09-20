print(" this is a sample script to test the gemini api")

# load the api kep 
import os
from dotenv import load_dotenv
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

from google import genai

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
# client = genai.Client()

# question_generator = client.chats.create(model="gemini-2.5-pro")

# response = client.models.generate_content(
#     model="gemini-2.5-pro", contents="Explain how dams work in a few words"
# )
# print(f"the full response object is {response}\n")
# print(response.text)

# def testing_history():
#     print(" this is a sample script to test the gemini api chat history")
#     response = question_generator.send_message("hi i am ron and i am in usa")
#     print(f"AI-->{response.text}")
#     response = question_generator.send_message("where am i from?")
#     print(f"AI-->{response.text}")

# testing_history()

from google import genai
from google.genai import types
from google.genai.types import Tool, GenerateContentConfig

client = genai.Client()
# chat = client.chats.create(model="gemini-2.5-flash" , config={"max_output_tokens":2048})

# response = chat.send_message("hey man thanks , the previous suggesstion helped a lot")
# print(response.text)
# print(response)

# # use the types library to give system prompts or instructions
# system_message = types.Message(
#     role=types.Role.SYSTEM,
#     content="You are a helpful assistant. You specialize in coding algorithms and analyzing user coding requirements, you are extremely good at reading and understanding coding and algorithm related articles."
# )
# chat.add_message(system_message)

system_prompt = """You are a helpful assistant. 
You specialize in coding algorithms and analyzing 
user coding requirements,you are extremely good at reading 
and understanding coding and algorithm related articles. Your main task is to summarize a given website in detail covering all the key aspects
and including all the technical and coding related aspects."""

# chat2 = client.chats.create(model="gemini-2.5-flash" , config={"max_output_tokens":2048 , "system_instruction":system_prompt})
# coding_response = chat2.send_message("explain the binary search algorithm in python")
# print("response from coding agent-->\n", coding_response.text)


def summarize_url(url):

    system_prompt = """You are a helpful assistant. You specialize in summarizing web content. you can go the the url given to u and summarize the entire webpage 
    in an very informative way adding to the knowledge of the user"""
    tools = [
        {"url_context": {}},
    ]

    response = client.chats.create(
        model="gemini-2.5-flash",
        config=GenerateContentConfig(max_output_tokens=2048, system_instruction=system_prompt, tools=tools)
    )

    response = response.send_message(f"summarize the content of the following url: {url}")
    print("response from summarization agent -->\n", response.text)

summarize_url("https://www.geeksforgeeks.org/dsa/largest-sum-contiguous-subarray/")