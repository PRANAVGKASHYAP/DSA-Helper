print(" this is a tavily demo ")
import json
from tavily import TavilyClient

tavily_client = TavilyClient(api_key="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")

#1 . get the search results from the Tavily API

response = tavily_client.search(
    query="key concepts of binary BFS algorithm , and trending coding questions based on it , make sure the question is descriptive",
    search_depth="advanced",
    max_results=1,
    include_answer="advanced",
    include_raw_content="markdown"
)

info = response['results']
print(f"Summarized search results is {response['answer']} ,  and the list of results got is {len(info)} \n")

# store the url and the title in saperate data structure
api_data = []

for i in range(len(info)):
    # this is to parse each response
    result = info[i]
    print(f"Result {i + 1}:\n")
    print(f"  Title: {result['title']} \n")
    print(f"  URL: {result['url']} \n")
    print(f"  Content: {result['content']} \n")

    api_data.append({
        "title": result['title'],
        "url": result['url'] , 
        "summary" : result['content']
    })



def website_summary(api_data):
    import langchain 
    from langchain.chains import LLMChain
    from langchain_community.document_loaders import WebBaseLoader
    from langchain_ollama import OllamaLLM
    from langchain.llms import Ollama
    from langchain.chains.summarize import load_summarize_chain
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain.prompts import PromptTemplate

    # defining prompts for the lmm to summarize the chunks and combine the cunks
    # Define prompt templates properly
    initial_prompt = PromptTemplate(
        input_variables=["text"],
        template=(
            "Summarize the following text in a concise manner, focusing on the key points and main ideas. "
            "Be sure to capture the essence of the content while keeping it brief.\n\n{text}\n\nSummary:"
        )
    )

    refine_prompt = PromptTemplate(
        input_variables=["existing_answer", "text"],
        template=(
            "Given the existing summary and a new chunk of text, refine the summary to include information "
            "from the new chunk. The summary should be elaborate and comprehensive. "
            "If the new chunk does not add any new information, return the existing summary with a bit more explanation.\n\n"
            "Existing Summary: {existing_answer}\n\nNew Chunk: {text}\n\nRefined Summary:"
        )
    )

    # initialize the llm to be used for the website summary
    llm = OllamaLLM(model="llama3")
    initial_chain = LLMChain(llm=llm, prompt=initial_prompt)
    refine_chain = LLMChain(llm=llm, prompt=refine_prompt)

    detailed_content = []

    # for every item in the api response read the html content
    for item in api_data:

        print(f"generating summary for the Title : {item['title']} \n")

        loader = WebBaseLoader(item['url'])
        docs = loader.load()
        data = docs[0].page_content

        # split the data and summarize it 
        splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100)
        chunks = splitter.split_documents(docs)

        # 🔹 3. Summarize chunks using map-reduce strategy
        chain = load_summarize_chain(
            llm,
            chain_type="refine",
            verbose=False,
            refine_prompt=refine_prompt
        )
        # chain = load_summarize_chain(llm, chain_type="refine",verbose=True,refine_prompt=PROMPT)

        compressed_text = chain.run(chunks)
        
        detailed_content.append({
            "title": item['title'],
            "url": item['url'],
            "summary": item['summary'],
            "compressed_content": compressed_text
        })
    
    return detailed_content

    # use any llm to summarize all the text data in this page 

result = website_summary(api_data)

print(f"the detailed search results are {result}")

with open("search_results2.json", "w") as f:
    json.dump(result, f, indent=2)