from fastapi import APIRouter, Request, status, HTTPException

from api.schemas.chat_completion_schemas import (
    ChatCompletionInputSchema, ChatCompletionOutputSchema)
from application.assistance.service import AssistantService, AssistantServiceChatCompletionResponse
from context import AppContext
from helpers.sql_storage import SqlStorage

router = APIRouter()


@router.post(
    "/chat/completions",
    response_model=ChatCompletionOutputSchema,
    status_code=status.HTTP_200_OK,
    tags=["Chat"]
)
async def chat_completions(request: Request, chat: ChatCompletionInputSchema):
    """
    Handles chat completions by generating responses to user queries, taking into account the context provided in the chat history. Retrieves relevant information from the configured vector store to formulate responses.
    If `chat_id` is supplied, message history will be fetched from DB;
    otherwise uses the `chat_history` array from the payload.
    """

    request_context: AppContext = request.state.app_context

    request_context.logger.info("Chat completions request received")
    sql_storage: SqlStorage = SqlStorage(request_context)

    # Determine chat_history
    final_history = []
    if chat.chat_id is not None:
        # Make sure the chat actually exists
        row = sql_storage.read_chat(chat.chat_id)
        if not row:
            raise HTTPException(status_code=404, detail="Chat not found")

        # Retrieve messages from DB
        db_msgs = sql_storage.get_messages(chat.chat_id)
        for sender, content in db_msgs:
            print(f"### Sender: {sender}\n{content}")
            final_history.append(content)

        # The user is also providing a new query: store that as a "user" message in DB
        sql_storage.create_message(chat.chat_id, "user", chat.chat_query)
    else:
        # fallback: no chat ID => user is providing chat_history explicitly
        final_history = chat.chat_history

    assistant_service = AssistantService(app_context=request_context)

    # Now call the chain
    completion_response = assistant_service.chat_completion(
        query=chat.chat_query,
        chat_history=final_history
    )

    # If chat_id is present, store the assistant's reply in DB
    if chat.chat_id is not None:
        sql_storage.create_message(chat.chat_id, "assistant", completion_response.response)

    request_context.logger.info("Chat completions request completed")

    return response_mapper(completion_response)


def response_mapper(completion_response: AssistantServiceChatCompletionResponse):
    message = completion_response.response
    references = []

    for doc in completion_response.references:
        reference = {"content": doc.page_content}
        if "url" in doc.metadata:
            reference["url"] = doc.metadata["url"]

        references.append(reference)

    return {
        "message": message,
        "references": references
    }
