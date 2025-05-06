import os
import time
import requests
import streamlit as st

# =============================================================================
# SETTINGS / CONFIG
# =============================================================================

BASE_URL = os.getenv("COMPANY_GPT_API_URL")

if "documents_by_chat" not in st.session_state:
    st.session_state["documents_by_chat"] = {}
if "links_by_chat" not in st.session_state:
    st.session_state["links_by_chat"] = {}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def list_chats():
    resp = requests.get(f"{BASE_URL}/chat")
    resp.raise_for_status()
    return resp.json()


def create_chat(title: str = None):
    resp = requests.post(f"{BASE_URL}/chat", json={"title": title})
    resp.raise_for_status()
    data = resp.json()
    return data["chat_id"]


def read_chat(chat_id: str):
    resp = requests.get(f"{BASE_URL}/chat/{chat_id}")
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def delete_chat(chat_id: str):
    resp = requests.delete(f"{BASE_URL}/chat/{chat_id}")
    resp.raise_for_status()
    return True


def list_messages(chat_id: str, limit: int = None):
    params = {}
    if limit is not None:
        params["limit"] = limit
    resp = requests.get(f"{BASE_URL}/chat/{chat_id}/messages", params=params)
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    data = resp.json()
    return data.get("messages", [])


def send_chat_message(chat_id: str, user_message: str):
    payload = {"chat_id": chat_id, "chat_query": user_message}
    resp = requests.post(f"{BASE_URL}/chat/completions", json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data["message"]


def generate_embeddings_from_link(url: str, filter_path: str = None):
    payload = {"url": url, "filterPath": filter_path}
    resp = requests.post(f"{BASE_URL}/embeddings/generate", json=payload)
    resp.raise_for_status()
    return resp.json()  # => { "statusOk": true }


def generate_embeddings_from_file(uploaded_file):
    files = {
        "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
    }
    resp = requests.post(f"{BASE_URL}/embeddings/generateFromFile", files=files)
    resp.raise_for_status()
    return resp.json()  # => { "statusOk": true }


def check_embeddings_status():
    """
    Calls GET /embeddings/status to check if generation is 'running' or 'idle'.
    Returns: dict with a 'status' key => {'status': 'running' or 'idle'}.
    """
    resp = requests.get(f"{BASE_URL}/embeddings/status")
    resp.raise_for_status()
    return resp.json()  # => {"status": "running"} or {"status": "idle"}


def wait_until_idle_or_timeout(max_seconds=60):
    """
    Poll /embeddings/status until it returns 'idle' or we time out.
    Returns True if status became idle, or False if we timed out.
    """
    start_time = time.time()
    st.info("Checking embedding generation status...")

    while (time.time() - start_time) < max_seconds:
        try:
            status_data = check_embeddings_status()
            if status_data.get("status") == "idle":
                return True
        except requests.exceptions.HTTPError as ex:
            # Even if there's an error, let's break or handle it
            st.error(f"Error checking status: {ex}")
            break
        time.sleep(2)  # Wait a bit before polling again
    return False


def show_chat_history(chat_id: str):
    messages = list_messages(chat_id)
    for msg in messages:
        sender = msg["sender"]
        content = msg["content"]
        if sender.lower() == "user":
            with st.chat_message("user"):
                st.markdown(content)
        else:
            with st.chat_message("assistant"):
                st.markdown(content)


def handle_http_error(ex: requests.exceptions.HTTPError):
    try:
        err_data = ex.response.json()
        detail = err_data.get("detail", "No details")
        st.error(f"API Error {ex.response.status_code}: {detail}")
    except ValueError:
        st.error(f"HTTP Error {ex.response.status_code}: {ex.response.text}")


# =============================================================================
# STREAMLIT PAGES
# =============================================================================

def chats_home():
    st.title("CompanyGPT Demo")

    chat_title = st.text_input("Chat Title", placeholder="Enter a name for your new chat")
    if st.button("Create Chat"):
        try:
            new_id = create_chat(chat_title)
            st.session_state["selected_chat_id"] = new_id
            st.session_state["documents_by_chat"][new_id] = []
            st.session_state["links_by_chat"][new_id] = []
            st.success(f"Created chat with ID: {new_id}")
            st.rerun()
        except requests.exceptions.HTTPError as ex:
            handle_http_error(ex)

    st.subheader("Existing Chats")
    try:
        chats = list_chats()
    except requests.exceptions.HTTPError as ex:
        handle_http_error(ex)
        chats = []

    if len(chats) == 0:
        st.write("No chats. Create one above.")
    else:
        for chat_info in chats:
            chat_id = chat_info["id"]
            title = chat_info.get("title") or "(untitled)"
            created_at = chat_info["created_at"]
            col1, col2, col3 = st.columns([0.5, 0.3, 0.2])
            with col1:
                st.write(f"**{title}** (ID: {chat_id})")
                st.caption(f"Created: {created_at}")
            with col2:
                if st.button("Open", key=f"open_{chat_id}"):
                    st.session_state["selected_chat_id"] = chat_id
                    st.session_state["documents_by_chat"].setdefault(chat_id, [])
                    st.session_state["links_by_chat"].setdefault(chat_id, [])
                    st.rerun()
            with col3:
                if st.button("Delete", key=f"del_{chat_id}"):
                    try:
                        delete_chat(chat_id)
                        if chat_id in st.session_state["documents_by_chat"]:
                            del st.session_state["documents_by_chat"][chat_id]
                        if chat_id in st.session_state["links_by_chat"]:
                            del st.session_state["links_by_chat"][chat_id]
                        st.success(f"Chat {title} deleted.")
                        st.rerun()
                    except requests.exceptions.HTTPError as ex:
                        handle_http_error(ex)


def chat_page(chat_id: str):
    try:
        chat_info = read_chat(chat_id)
    except requests.exceptions.HTTPError as ex:
        handle_http_error(ex)
        chat_info = None

    if not chat_info:
        st.error("Chat not found in server DB.")
        return

    chat_title = chat_info.get("title") or chat_id
    st.title(f"Chat: {chat_title}")

    with st.sidebar:
        if st.button("Back to Chats"):
            st.session_state.pop("selected_chat_id", None)
            st.rerun()

        st.subheader("📑 Documents")
        docs = st.session_state["documents_by_chat"].get(chat_id, [])
        for doc_name in docs:
            st.write(f"- {doc_name}")

        # Let user choose a file, but do not auto-process
        uploaded_file = st.file_uploader("Choose a file to embed", key="file_uploader", help="""
            The file must have one of the following type: .txt, .md, .pdf, .zip, .tar.gz, .tgz;\n
            Please mind that archive files must contain only files with the aforementioned content types.""")
        if uploaded_file is not None:
            st.write(f"**Selected file**: `{uploaded_file.name}`")
            if st.button("Generate Embeddings for File"):
                with st.spinner("Starting embeddings generation..."):
                    try:
                        generate_embeddings_from_file(uploaded_file)
                    except requests.exceptions.HTTPError as ex:
                        handle_http_error(ex)
                        st.stop()
                    st.info("Embeddings process started, checking status...")

                # Wait until idle or timeout
                with st.spinner("Waiting for embeddings to finish..."):
                    is_idle = wait_until_idle_or_timeout(max_seconds=60)
                if is_idle:
                    # If idle => success
                    st.session_state["documents_by_chat"][chat_id].append(uploaded_file.name)
                    st.success(f"Uploaded & processed file: {uploaded_file.name}")
                else:
                    st.warning("Embeddings are still running after 60 seconds. Please check status later.")

        st.subheader("🔗 Links")
        links = st.session_state["links_by_chat"].get(chat_id, [])
        for ln in links:
            st.markdown(f"- [{ln}]({ln})")

        new_link = st.text_input("Add a link to parse", help="""Generate embeddings for a given URL.\n
        It starts from a single web page and generates embeddings for the text data of that page and for every page
        connected via hyperlinks (anchor tags).""")
        if st.button("Generate Embeddings for Link"):
            if new_link:
                with st.spinner("Starting embeddings generation..."):
                    try:
                        generate_embeddings_from_link(new_link)
                    except requests.exceptions.HTTPError as ex:
                        handle_http_error(ex)
                        st.stop()
                    st.info("Embeddings process started, checking status...")

                # Wait until idle or timeout
                with st.spinner("Waiting for embeddings to finish..."):
                    is_idle = wait_until_idle_or_timeout(max_seconds=60)
                if is_idle:
                    st.session_state["links_by_chat"][chat_id].append(new_link)
                    st.success(f"Link added & embeddings generated: {new_link}")
                else:
                    st.warning("Embeddings are still running after 60 seconds. Please check status later.")
            else:
                st.warning("Please enter a link before clicking the button.")

    # Show existing conversation
    try:
        show_chat_history(chat_id)
    except requests.exceptions.HTTPError as ex:
        handle_http_error(ex)
        return

    user_input = st.chat_input("Type your message here...")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    assistant_response = send_chat_message(chat_id, user_input)
                    st.markdown(assistant_response)
                except requests.exceptions.HTTPError as ex:
                    handle_http_error(ex)

        st.rerun()


def main():
    if "selected_chat_id" not in st.session_state:
        chats_home()
    else:
        chat_page(st.session_state["selected_chat_id"])


if __name__ == "__main__":
    st.set_page_config(page_title="CompanyGPT", layout="wide")
    main()
