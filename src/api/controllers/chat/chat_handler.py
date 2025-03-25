from fastapi import APIRouter, Request, HTTPException, status, Query, Body
from api.schemas.chat_schemas import (
    CreateChatInputSchema,
    CreateChatOutputSchema,
    ChatOutputSchema,
    ChatMessagesListOutputSchema,
)
from helpers.sql_storage import SqlStorage
from context import AppContext

router = APIRouter()


@router.post(
    "/chat",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateChatOutputSchema,
    tags=["Chat"]
)
def create_new_chat(request: Request, data: CreateChatInputSchema | None = None):
    """
    Create a new chat with a new, auto-generated ID (UUID).
    If 'title' is provided in body, store it in the DB.
    """
    app_context: AppContext = request.state.app_context
    sql_storage = SqlStorage(app_context)
    title = data.title if data is not None else None

    chat_id = sql_storage.create_chat(title)

    app_context.logger.info(f"Created new chat with id {chat_id}, title={title}")
    return {"chat_id": chat_id}


@router.get("/chat",
            response_model=list[ChatOutputSchema],
            tags=["Chat"])
def get_all_chats(request: Request):
    """
    List all chats.
    """
    app_context: AppContext = request.state.app_context
    sql_storage = SqlStorage(app_context)

    rows = sql_storage.list_chats()
    # rows -> list of tuples (id, title, created_at)
    return [
        {
            "id": str(row[0]),
            "title": row[1],
            "created_at": row[2]
        }
        for row in rows
    ]


@router.get("/chat/{chat_id}",
            response_model=ChatOutputSchema,
            tags=["Chat"])
def get_chat(request: Request, chat_id: str):
    """
    Read a single chat by ID (UUID).
    """
    app_context: AppContext = request.state.app_context
    sql_storage = SqlStorage(app_context)

    row = sql_storage.read_chat(chat_id)
    if not row:
        raise HTTPException(status_code=404, detail="Chat not found.")
    # row -> (id, title, created_at)
    return {
        "id": str(row[0]),
        "title": row[1],
        "created_at": row[2]
    }


@router.delete("/chat/{chat_id}",
               tags=["Chat"])
def remove_chat(request: Request, chat_id: str):
    """
    Delete a single chat by ID (messages will be removed as well due to ON DELETE CASCADE).
    """
    app_context: AppContext = request.state.app_context
    sql_storage = SqlStorage(app_context)

    # Ensure chat actually exists, or raise 404
    row = sql_storage.read_chat(chat_id)
    if not row:
        raise HTTPException(status_code=404, detail="Chat not found.")
    sql_storage.delete_chat(chat_id)
    return {"status": "ok"}


# ----------------------------------------------------------------------
#      MESSAGES Endpoints
# ----------------------------------------------------------------------


@router.get("/chat/{chat_id}/messages",
            response_model=ChatMessagesListOutputSchema,
            tags=["Chat"])
def list_chat_messages(
        request: Request,
        chat_id: str,
        limit: int = Query(default=None, description="Limit the number of most recent messages.")
):
    """
    List messages for a given chat, optionally limited to the N most recent messages.
    """
    app_context: AppContext = request.state.app_context
    sql_storage = SqlStorage(app_context)

    row = sql_storage.read_chat(chat_id)
    if not row:
        raise HTTPException(status_code=404, detail="Chat not found.")

    msgs = sql_storage.get_messages(chat_id, limit=limit)
    # msgs -> list of tuples (sender, content) in chronological order
    return {
        "messages": [
            {
                "sender": m[0],
                "content": m[1]
            }
            for m in msgs
        ]
    }
