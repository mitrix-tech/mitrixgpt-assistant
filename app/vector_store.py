import os

from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.document_loaders import (
    TextLoader,
    CSVLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
)
from langchain_core.documents import Document
from langchain_milvus import Milvus
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

MILVUS_URI = "tcp://localhost:19530"

DEFAULT_COLLECTION_NAME = "mitrixdata"

llm = ChatOpenAI(
    model="gpt-4o-mini", temperature=0, max_tokens=2000
)

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, add_start_index=True)


def create_collection(collection_name, documents):
    """
    Create a new Milvus collection from the given documents.

    Args:
    collection_name (str): The name of the collection to create.
    documents (list): A list of documents to add to the collection.

    Returns:
    None

    This function splits the documents into texts, creates a new Milvus collection,
    and persists it to disk.
    """

    # Split the documents into smaller text chunks
    texts = text_splitter.split_documents(documents)

    # Create a new Milvus collection from the text chunks
    try:
        vector_store = Milvus.from_documents(
            documents=texts,
            embedding=embeddings,
            connection_args={"uri": MILVUS_URI},
            index_params={"index_type": "FLAT", "metric_type": "COSINE"},
            collection_name=collection_name,
            auto_id=True,
            consistency_level="Strong",
            enable_dynamic_field=True,
            drop_old=False,
        )

    except Exception as e:
        print(f"Error creating collection: {e}")
        return None

    return vector_store


def load_collection(collection_name):
    """
    Load an existing Milvus collection.

    Args:
    collection_name (str): The name of the collection to load.

    Returns:
    Milvus: The loaded Milvus collection.
    This function loads a previously created Milvus collection from disk.
    """

    vector_store = Milvus(
        embedding_function=embeddings,
        connection_args={"uri": MILVUS_URI},
        index_params={"index_type": "FLAT", "metric_type": "COSINE"},
        collection_name=collection_name,
        auto_id=True,
        consistency_level="Strong",
        enable_dynamic_field=True,
        drop_old=False,
    )

    return vector_store


def add_documents_to_collection(vectordb, documents):
    """
    Add documents to the vector database collection.

    Args:
        vectordb: The vector database object to add documents to.
        documents: A list of documents to be added to the collection.
    This function splits the documents into smaller chunks, adds them to the
    vector database, and persists the changes.
    """

    # Split the documents into smaller text chunks
    texts = text_splitter.split_documents(documents)

    # Add the text chunks to the vector database
    vectordb.add_documents(texts)

    return vectordb


def load_retriever(collection_name: str = DEFAULT_COLLECTION_NAME, score_threshold: float = 0.6):
    """
    Create a retriever from a Milvus collection with a similarity score threshold.

    Args:
    collection_name (str): The name of the collection to use.
    score_threshold (float): The minimum similarity score threshold for retrieving documents.
                           Documents with scores below this threshold will be filtered out.
                           Defaults to 0.6.
    Returns:
    Retriever: A retriever object that can be used to query the collection with similarity
              score filtering.
    This function loads a Milvus collection and creates a retriever from it that will only
    return documents meeting the specified similarity score threshold.

    """

    # Load the Milvus collection
    vectordb = load_collection(collection_name)

    # Create a retriever from the collection with specified search parameters
    retriever = vectordb.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"score_threshold": score_threshold, "k": 4},
    )

    from langchain.retrievers.document_compressors import LLMChainFilter

    _filter = LLMChainFilter.from_llm(llm)
    retriever = ContextualCompressionRetriever(
        base_compressor=_filter, base_retriever=retriever
    )

    # from langchain.retrievers.document_compressors import DocumentCompressorPipeline
    # from langchain_community.document_transformers import EmbeddingsRedundantFilter
    #
    # redundant_filter = EmbeddingsRedundantFilter(embeddings=embeddings)
    # relevant_filter = EmbeddingsFilter(embeddings=embeddings, similarity_threshold=0.6)
    # pipeline_compressor = DocumentCompressorPipeline(
    #     transformers=[redundant_filter, relevant_filter]
    # )
    #
    # retriever = ContextualCompressionRetriever(
    #     base_compressor=pipeline_compressor, base_retriever=retriever
    # )

    return retriever


def load_document(file_path: str) -> list[Document]:
    """
    Load a document from a file path.
    Supports .txt, .pdf, .docx, .csv, .html, and .md files.

    Args:
    file_path (str): Path to the document file.

    Returns:
    list[Document]: A list of Document objects.

    Raises:
    ValueError: If the file type is not supported.
    """
    _, file_extension = os.path.splitext(file_path)

    if file_extension == ".txt":
        loader = TextLoader(file_path)
    elif file_extension == ".pdf":
        loader = PyPDFLoader(file_path)
    elif file_extension == ".docx":
        loader = Docx2txtLoader(file_path)
    elif file_extension == ".csv":
        loader = CSVLoader(file_path)
    elif file_extension == ".html":
        loader = UnstructuredHTMLLoader(file_path)
    elif file_extension == ".md":
        loader = UnstructuredMarkdownLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

    return loader.load()

