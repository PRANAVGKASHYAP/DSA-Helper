def main():
    from langchain_ollama import OllamaLLM
    from langchain.chains.summarize import load_summarize_chain
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain.schema import Document

    # Initialize LLM
    llm = OllamaLLM(model="llama3")

    # Your text wrapped inside a Document
    docs = [
        Document(
            page_content="""
            Document splitting is often a crucial preprocessing step for many applications. 
            It involves breaking down large texts into smaller, manageable chunks. 
            This process offers several benefits, such as ensuring consistent processing 
            of varying document lengths, overcoming input size limitations of models, 
            and improving the quality of text representations used in retrieval systems.
            There are several strategies for splitting documents, each with its own advantages.
            """,
            metadata={"source": "example"}
        )
    ]

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    # Summarize with map_reduce
    chain = load_summarize_chain(llm, chain_type="map_reduce", verbose=False)
    compressed_text = chain.run(chunks)

    print(f"summarized text is: {compressed_text}")

if __name__ == "__main__":
    main()
