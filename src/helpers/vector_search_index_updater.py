from logging import Logger

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, SparseVectorParams

from constants import DEFAULT_NUM_DIMENSIONS_VALUE, DIMENSIONS_DICT
from context import AppContext


class VectorStoreInitializer:
    def __init__(self, app_context: AppContext):
        self.app_context: AppContext = app_context
        self.logger: Logger = app_context.logger
        self.embedding_key = app_context.configurations.vectorStore.embeddingKey
        self.index_name = app_context.configurations.vectorStore.indexName

    def init_collection(self) -> None:
        collection_name = self.app_context.configurations.vectorStore.collectionName

        client = QdrantClient(path="/tmp/qdrant")

        configured_similarity_fn = self.app_context.configurations.vectorStore.relevanceScoreFn or Distance.COSINE
        num_dimensions = DIMENSIONS_DICT.get(self.app_context.configurations.embeddings.name,
                                             DEFAULT_NUM_DIMENSIONS_VALUE)
        embeddings_key = self.app_context.configurations.vectorStore.embeddingKey
        sparse_key = self.app_context.configurations.vectorStore.textKey

        # Create the collection if it does not exist
        if not client.collection_exists(collection_name):
            self.logger.info(f'Collection "{collection_name}" missing, it will be created now')
            client.create_collection(
                collection_name=collection_name,
                vectors_config={embeddings_key: VectorParams(size=num_dimensions,
                                                             distance=configured_similarity_fn)},
                sparse_vectors_config={sparse_key: SparseVectorParams()},
            )
        else:
            self.logger.info(f'Using existing collection "{collection_name}"')
