from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, Field
from qdrant_client.models import Distance


class AzureLlmConfiguration(BaseModel):
    apiVersion: str = Field(
        ..., description='The API version of the Azure OpenAI service to be used.'
    )
    deploymentName: str = Field(
        ...,
        description='The name of the configured deployment model to be used by AI RAG.',
    )
    name: str = Field(
        ...,
        description='The name of the language model (LLM) to be used. Check the Azure OpenAI documentation for available models.',
    )
    type: str = Field(
        'azure',
        description='The type of language model to be used by AI RAG for natural language processing and understanding.',
    )
    url: str = Field(
        ..., description='The URL of the Azure OpenAI service to connect with.'
    )
    temperature: Optional[float] = Field(
        0.0,
        description='The temperature parameter for sampling from the language model. A higher value increases the randomness of the generated text.',
    )


class OpenAILlmConfiguration(BaseModel):
    type: str = Field(
        'openai',
        description='The type of language model to be used by AI RAG for natural language processing and understanding.',
    )
    name: str = Field(
        ...,
        description='The name of the language model (LLM) to be used. Check the OpenAI documentation for available models.',
    )
    temperature: Optional[float] = Field(
        0.0,
        description='The temperature parameter for sampling from the language model. A higher value increases the randomness of the generated text.',
    )


class Tokenizer(BaseModel):
    name: Optional[str] = Field(
        'gpt-4o', description='The name of the tokenizer'
    )


class AzureEmbeddingsConfiguration(BaseModel):
    apiVersion: str = Field(
        ..., description='The API version of the Azure OpenAI service to be used.'
    )
    deploymentName: str = Field(
        ...,
        description='The name of the configured deployment model to be used by AI RAG.',
    )
    name: str = Field(
        ...,
        description='The name of the embeddings model to be used by RAG for various tasks such as text representation and similarity.',
    )
    type: str = Field(
        'azure',
        description='The type of language model to be used by AI RAG for the embeddings generation.',
    )
    url: str = Field(
        ..., description='The URL of the Azure OpenAI service to connect with.'
    )


class OpenAIEmbeddingsConfiguration(BaseModel):
    type: str = Field(
        'openai',
        description='The type of language model to be used by AI RAG for the embeddings generation.',
    )
    name: str = Field(
        ...,
        description='The name of the embeddings model to be used by RAG for various tasks such as text representation and similarity.',
    )


class VectorStore(BaseModel):
    dbName: Optional[str] = Field(
        None, description='The name of the database where the vector store is hosted.'
    )
    collectionName: str = Field(
        'rag-data',
        description='The name of the collection of vectors to be used by RAG for various tasks such as text representation and similarity.',
    )
    indexName: str = Field(
        ...,
        description='The name of the index to be used by RAG for various tasks such as text representation and similarity.',
    )
    relevanceScoreFn: Optional[Distance] = Field(
        'Euclid',
        description="The function used to calculate relevance scores for vectors. Options: 'Euclid', 'Cosine', 'Dot'.",
    )

    embeddingKey: str = Field(
        ..., description='The key used to identify embeddings in the vector store.'
    )
    textKey: str = Field(
        ..., description='The key used to store text data in the vector store.'
    )
    maxDocumentsToRetrieve: Optional[int] = Field(
        4,
        description='The maximum number of documents to be retrieved from the vector store.',
    )
    maxScoreDistance: Optional[float] = Field(
        None, description='The maximum score distance for the vectors.'
    )
    minScoreDistance: Optional[float] = Field(
        None, description='The maximum score distance for the vectors.'
    )


class PromptsFilePath(BaseModel):
    system: Optional[str] = Field(
        None, description='The system prompt to be used for the RAG chain.'
    )
    user: Optional[str] = Field(
        None, description='The user prompt to be used for the RAG chain.'
    )


class Rag(BaseModel):
    promptsFilePath: Optional[PromptsFilePath] = None


class Chain(BaseModel):
    aggregateMaxTokenNumber: Optional[int] = Field(
        4000,
        description='The maximum number of tokens to be used for aggregation of multiple responses from different services.',
    )
    rag: Optional[Rag] = Field(None, description='RAG chain configuration')


class RagTemplateConfigSchema(BaseModel):
    llm: Union[AzureLlmConfiguration, OpenAILlmConfiguration]
    tokenizer: Optional[Tokenizer] = Field(
        default_factory=lambda: Tokenizer.model_validate({'name': 'gpt-4o'})
    )
    embeddings: Union[AzureEmbeddingsConfiguration, OpenAIEmbeddingsConfiguration]
    vectorStore: VectorStore
    chain: Optional[Chain] = Field(
        default_factory=lambda: Chain.model_validate({'aggregateMaxTokenNumber': 4000})
    )
