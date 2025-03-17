import uvicorn
from fastapi import FastAPI

from api.controllers.chat import chat_handler
from api.controllers.chat_completions import chat_completions_handler
from api.controllers.core.checkup import checkup_handler
from api.controllers.core.liveness import liveness_handler
from api.controllers.core.readiness import readiness_handler
from api.controllers.core.metrics import metrics_handler
from api.controllers.embeddings import embeddings_handler
from api.middlewares.app_context_middleware import AppContextMiddleware
from api.middlewares.logger_middleware import LoggerMiddleware
from configurations.configuration import get_configuration
from configurations.variables import get_variables
from context import AppContext, AppContextParams
from helpers.sql_storage import SqlStorage
from infrastracture.logger import get_logger
from infrastracture.metrics.manager import MetricsManager
from helpers.vector_search_index_updater import VectorStoreInitializer


def create_app(context: AppContext) -> FastAPI:
    app = FastAPI(
        openapi_url="/docs/openapi.json",
        redoc_url=None,
        title="mitrixgpt"
    )

    app.add_middleware(AppContextMiddleware, app_context=context)
    app.add_middleware(LoggerMiddleware, logger=context.logger)

    app.include_router(liveness_handler.router)
    app.include_router(readiness_handler.router)
    app.include_router(checkup_handler.router)
    app.include_router(metrics_handler.router)
    app.include_router(chat_handler.router)
    app.include_router(chat_completions_handler.router)
    app.include_router(embeddings_handler.router)

    return app


if __name__ == '__main__':
    logger = get_logger()
    metrics_manager = MetricsManager()
    env_vars = get_variables(logger)
    configurations = get_configuration(env_vars.CONFIGURATION_PATH, logger)

    app_context = AppContext(
        params=AppContextParams(
            logger=logger,
            metrics_manager=metrics_manager,
            env_vars=env_vars,
            configurations=configurations
        )
    )

    application = create_app(app_context)

    vector_store_initializer = VectorStoreInitializer(app_context)
    vector_store_initializer.init_collection()

    # Ensure SQL tables exist:
    sql_storage = SqlStorage(app_context)
    sql_storage.create_tables()

    uvicorn.run(
        application,
        host='0.0.0.0',  # nosec B104 # binding to all interfaces is required to expose the service in containers
        port=int(app_context.env_vars.PORT),
        log_level='error'
    )
