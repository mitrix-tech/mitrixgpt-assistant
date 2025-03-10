from langchain import hub
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import MessagesState, StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition

from helpers import pretty_print_docs
from db import get_connection
from vector_store import load_retriever

#
# 1) LLM + base prompt
#
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_tokens=2000)
base_prompt = hub.pull("mitrixgpt-base")  # "As an expert in Mitrix Technology..."


@tool(response_format="content_and_artifact")
def retrieve(query: str):
    """Retrieve information from Milvus using the load_retriever function."""

    retriever = load_retriever()

    if not retriever:
        return ("No vector store found. Please add documents or links first.", [])

    docs = retriever.invoke(query)
    pretty_print_docs(docs)

    if not docs:
        return ("No relevant documents found.", [])

    # Build a serialized string for the LLM
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\n"
         f"Content: {doc.page_content}")
        for doc in docs
    )
    return serialized, docs


#
# 3) Step 1 in the graph: Decide whether to call the retrieve tool or respond directly
#
def query_or_respond(state: MessagesState):
    """
    Generate an AIMessage that may include a tool-call to 'retrieve'.
    The `MessagesState` includes the full conversation so far: user messages, LLM messages, etc.
    """

    llm_with_tools = llm.bind_tools([retrieve])
    prompt = f"{base_prompt}\n\n{state['messages']}"

    response = llm_with_tools.invoke(prompt)
    return {"messages": [response]}


#
# 4) Step 2 in the graph: The actual retrieval
#
tools_node = ToolNode([retrieve])


#
# 5) Step 3 in the graph: generate the final answer from the retrieved content
#
def generate(state: MessagesState):
    """
    Take whatever the LLM got from the 'retrieve' step
    and produce a final user-visible answer using base prompt.
    """
    # 1) Gather the latest ToolMessages
    recent_tool_messages = []
    for message in reversed(state["messages"]):
        if message.type == "tool":
            recent_tool_messages.append(message)
        else:
            break
    tool_messages = recent_tool_messages[::-1]

    # 2) Extract the text from the tool messages
    #    The tool’s .content is the retrieved doc text; .artifact is the list of docs
    docs_content = "\n\n".join(msg.content for msg in tool_messages)

    # 3) Prepare the system message: `base_prompt` + the retrieved text
    system_message_content = f"{base_prompt}\n\n{docs_content}"

    # 4) Build the conversation up to now (excluding tool messages)
    conversation_messages = []
    for msg in state["messages"]:
        if msg.type in ("human", "system"):
            conversation_messages.append(msg)
        elif msg.type == "ai" and not msg.tool_calls:
            conversation_messages.append(msg)

    # Insert system message
    prompt = [SystemMessage(system_message_content)] + conversation_messages

    # 5) Run the LLM
    response = llm.invoke(prompt)
    return {"messages": [response]}


#
# 6) Build and compile the graph
#
def build_chat_graph():
    graph_builder = StateGraph(MessagesState)
    graph_builder.add_node(query_or_respond)
    graph_builder.add_node(tools_node)
    graph_builder.add_node(generate)

    graph_builder.set_entry_point("query_or_respond")
    graph_builder.add_conditional_edges(
        "query_or_respond",
        tools_condition,
        {END: END, "tools": "tools"},
    )
    graph_builder.add_edge("tools", "generate")
    graph_builder.add_edge("generate", END)

    saver = PostgresSaver(get_connection())
    # Make sure the table named 'checkpoints' is created if not exists:
    saver.setup()

    return graph_builder.compile(checkpointer=saver)


#
# 7) Prepare a function for streaming usage with Postgres memory
#

def stream_chat_graph(messages: list, thread_id: str):
    """
    Stream execution of the graph given a list of messages in
    the format: [ {"role": "user"|"assistant", "content": "..."} ]
    """
    graph = build_chat_graph()
    config = {"configurable": {"thread_id": thread_id}}

    for step in graph.stream({"messages": messages}, stream_mode="values", config=config):
        yield step
