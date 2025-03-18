import contextlib
import os
import time

import bs4
import streamlit as st
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document

from db import (
    create_chat,
    list_chats,
    delete_chat,
    read_chat,
    create_message,
    get_messages,
    create_source,
    list_sources,
    delete_source, create_tables,
)
from vector_store import (
    create_collection,
    load_collection,
    add_documents_to_collection,
    DEFAULT_COLLECTION_NAME, load_document
)


from rag_graph import stream_chat_graph


# ========== UI Helpers ==========

def stream_response(response: str, delay=0.03):
    """
    Stream a response word by word with a delay.
    """
    for word in response.split():
        yield word + " "
        time.sleep(delay)


def show_chat_history(chat_id: int):
    """
    Display all messages for a chat in chronological order.
    """
    messages = get_messages(chat_id)
    for sender, content in messages:
        if sender == "user":
            with st.chat_message("user"):
                st.markdown(content)
        else:
            with st.chat_message("assistant"):
                st.markdown(content)


def handle_user_message(chat_id: int, user_message: str):
    """
    Use the new multi-step graph to handle each user message
    with streaming partial steps in the UI.
    """
    # 1) Save the user's new message in DB
    create_message(chat_id, "user", user_message)

    # 2) Display user message
    with st.chat_message("user"):
        st.markdown(user_message)

    # 3) Build the list of all messages from DB for conversation context
    messages_for_graph = []
    rows = get_messages(chat_id, limit=10)
    # rows is a list of (sender, content)
    for sender, content in rows:
        role = "assistant" if sender == "ai" else "user"
        messages_for_graph.append({"role": role, "content": content})

    # messages_for_graph = [message for message in messages_for_graph if message.get("role") == "user"]
    # messages_for_graph = messages_for_graph[-2:]

    # 4) We want to pass this entire conversation to the graph
    final_answer = ""
    with st.chat_message("assistant"):
        placeholder = st.empty()

        # The graph yields partial steps. Each step has "messages": [...]
        for partial_state in stream_chat_graph(messages_for_graph, str(chat_id)):
            # partial_state might look like:
            #   {"messages": [AIMessage(...)]}
            # So let's get the last message from partial_state:
            last_message = partial_state["messages"][-1]
            if last_message.type == "ai":
                final_answer = last_message.content
                placeholder.markdown(final_answer)

    # 5) Save the final assistant message in DB
    create_message(chat_id, "ai", final_answer)


def add_link_to_collection(chat_id: int, link: str):
    """
    Retrieve text from a link, add to Milvus collection, and store in DB.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    loader = WebBaseLoader(
        web_paths=(link,),
        # bs_kwargs=dict(features="html.parser")
    )

    docs = loader.load()

    cleaned_docs = []
    for doc in docs:
        soup = bs4.BeautifulSoup(doc.page_content, "html.parser")

        # Remove unwanted tags
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()

        # Extract text
        text = soup.get_text(separator=" ", strip=True)
        text = " ".join(text.split())

        # Create a new Document with the cleaned text (preserving metadata)
        cleaned_doc = Document(
            page_content=text,
            metadata=doc.metadata
        )
        cleaned_docs.append(cleaned_doc)

    collection_name = DEFAULT_COLLECTION_NAME

    # If collection doesn't exist -> create; else -> add
    try:
        load_collection(collection_name)
        # If loaded, simply add
        add_documents_to_collection(load_collection(collection_name), cleaned_docs)
    except:
        # Means collection doesn't exist
        create_collection(collection_name, cleaned_docs)

    # Save link in DB
    create_source(link, "", chat_id, source_type="link")
    st.success(f"Link added: {link}")


def add_document_to_collection(chat_id: int, file):
    """
    Save uploaded file contents to the vector store.
    """
    temp_dir = "temp_files"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, file.name)
    with open(temp_file_path, "wb") as f:
        f.write(file.getbuffer())

    docs = load_document(temp_file_path)

    collection_name = DEFAULT_COLLECTION_NAME

    try:
        load_collection(collection_name)
        add_documents_to_collection(load_collection(collection_name), docs)
    except:
        create_collection(collection_name, docs)

    create_source(file.name, "", chat_id, source_type="document")
    with contextlib.suppress(FileNotFoundError):
        os.remove(temp_file_path)
    st.success(f"Uploaded file: {file.name}")


# ========== Streamlit pages ==========

def chats_home():
    st.title("MitrixGPT Demo")

    # Create new chat
    chat_title = st.text_input("Chat Title", placeholder="Enter a name for your new chat")
    if st.button("Create Chat"):
        if chat_title:
            chat_id = create_chat(chat_title)
            st.session_state["selected_chat_id"] = chat_id
            st.success(f"Created chat: {chat_title}")
            st.rerun()

    st.subheader("Existing Chats")
    chats = list_chats()
    if chats:
        for chat in chats:
            chat_id, title, created = chat
            col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
            with col1:
                st.write(f"**{title}** (ID: {chat_id})")
            with col2:
                if st.button("Open", key=f"open_{chat_id}"):
                    st.session_state["selected_chat_id"] = chat_id
                    st.rerun()
            with col3:
                if st.button("Delete", key=f"del_{chat_id}"):
                    delete_chat(chat_id)
                    st.success(f"Chat {title} deleted.")
                    st.rerun()
    else:
        st.write("No chats. Create one above.")


def chat_page(chat_id: int):
    chat_info = read_chat(chat_id)
    if not chat_info:
        st.error("Chat not found.")
        return

    st.title(f"Chat: {chat_info[1]} (ID: {chat_id})")

    # Sidebar for context
    with st.sidebar:
        if st.button("Back to Chats"):
            st.session_state.pop("selected_chat_id", None)
            st.rerun()

        st.subheader("📑 Documents")
        docs = list_sources(chat_id, source_type="document")
        if docs:
            for doc in docs:
                doc_id, doc_name, source_text, doc_type = doc
                st.write(f"- {doc_name}")
                if st.button("Delete", key=f"deldoc_{doc_id}"):
                    delete_source(doc_id)
                    st.success(f"Deleted document: {doc_name}")
                    st.rerun()

        uploaded_file = st.file_uploader("Upload Document")
        if uploaded_file:
            add_document_to_collection(chat_id, uploaded_file)

        st.subheader("🔗 Links")
        links = list_sources(chat_id, source_type="link")
        if links:
            for ln in links:
                link_id, link_name, _, _ = ln
                st.markdown(f"- [{link_name}]({link_name})")
                if st.button("Delete", key=f"delink_{link_id}"):
                    delete_source(link_id)
                    st.success(f"Deleted link: {link_name}")
                    st.rerun()
        new_link = st.text_input("Add a link to parse")
        if st.button("Add Link"):
            if new_link:
                add_link_to_collection(chat_id, new_link)

    # Show existing conversation
    show_chat_history(chat_id)

    # Chat input
    user_input = st.chat_input("Type your message here...")
    if user_input:
        handle_user_message(chat_id, user_input)
        st.rerun()


def main():
    if "selected_chat_id" not in st.session_state:
        chats_home()
    else:
        chat_page(st.session_state["selected_chat_id"])


if __name__ == "__main__":
    create_tables()
    st.set_page_config(page_title="MitrixGPT", layout="wide")
    main()
