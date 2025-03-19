from typing import Any, Dict, List, Optional, Type

from attr import dataclass
from langchain.chains.base import Chain
from langchain_core.callbacks import CallbackManagerForChainRun
from langchain_core.embeddings import Embeddings
from langchain_core.runnables import RunnableConfig
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from pydantic import BaseModel, create_model

from context import AppContext


@dataclass
class RetrieverChainConfiguration:
    cluster_uri: str
    db_name: str
    collection_name: str
    embeddings: Embeddings
    index_name: str
    embedding_key: str
    relevance_score_fn: str
    text_key: str
    max_number_of_results: int
    max_score_distance: Optional[float] = None
    min_score_distance: Optional[float] = None


class RetrieverChain(Chain):
    context: AppContext
    configuration: RetrieverChainConfiguration

    query_key: str = "query"  #: :meta private:
    output_key: str = "input_documents"  #: :meta private:

    @property
    def input_keys(self) -> List[str]:
        return [self.query_key]

    @property
    def output_keys(self) -> List[str]:
        return [self.output_key]

    def get_input_schema(
            self, config: Optional[RunnableConfig] = None
    ) -> Type[BaseModel]:
        return create_model(
            "RetrieveChainInput",
            **{
                self.query_key: (
                    str,  # query
                    None
                ),
            },  # type: ignore[call-overload]
        )

    def get_output_schema(
            self, config: Optional[RunnableConfig] = None
    ) -> Type[BaseModel]:
        return create_model(
            "RetrieveChainOutput",
            **{self.output_key: (
                str,  # response
                None
            )},  # type: ignore[call-overload]
        )

    def _setup_vector_search(self):
        sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")

        return QdrantVectorStore.from_existing_collection(
            url=self.context.env_vars.VECTOR_DB_CLUSTER_URI,
            api_key=self.context.env_vars.QDRANT__SERVICE__API_KEY,
            collection_name=self.configuration.collection_name,
            embedding=self.configuration.embeddings,
            sparse_embedding=sparse_embeddings,
            vector_name=self.configuration.embedding_key,
            sparse_vector_name=self.configuration.text_key,
            retrieval_mode=RetrievalMode.HYBRID
        )

    def _call(self, inputs: Dict[str, Any], run_manager: CallbackManagerForChainRun | None = None) -> Dict[str, Any]:
        query = inputs[self.query_key]
        vector_search = self._setup_vector_search()
        result = vector_search.similarity_search(
            query,
            k=self.configuration.max_number_of_results,
            # score_threshold=0.6
        )
        return {
            self.output_key: result
        }
