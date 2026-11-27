from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from app.tools import get_all_tools


class AgentState(TypedDict):
    """Representasi state percakapan pada LangGraph."""
    messages: Annotated[Sequence[BaseMessage], add_messages]


def agent_node(state: AgentState) -> dict:
    """
    Node agent (LLM).
    TODO: Diimplementasikan oleh tim untuk memanggil model LLM dengan tools yang di-bind.
    """
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""
    
    # Stub response sebelum integrasi model LLM sesungguhnya
    reply_content = (
        f"[Stub Agent] Menerima pesan: '{last_message}'. "
        "Logika LLM & routing tools akan diimplementasikan oleh tim."
    )
    return {"messages": [AIMessage(content=reply_content)]}


def tool_node(state: AgentState) -> dict:
    """
    Node eksekusi tools.
    TODO: Diimplementasikan oleh tim menggunakan ToolNode dari langgraph.prebuilt atau routing khusus.
    """
    return {"messages": []}


def should_continue(state: AgentState) -> str:
    """
    Kondisi percabangan: menentukan apakah lanjut ke eksekusi tools atau selesai.
    """
    # TODO: Cek apakah pesan terakhir memiliki tool_calls
    return END


def build_graph():
    """Membangun dan mengompilasi StateGraph dengan MemorySaver checkpointer."""
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END,
        },
    )
    workflow.add_edge("tools", "agent")

    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)


# Instance graph global
graph = build_graph()


async def process_message(user_input: str, thread_id: str) -> str:
    """
    Helper untuk mengeksekusi graph percakapan dengan thread_id tertentu.
    """
    config = {"configurable": {"thread_id": thread_id}}
    input_state = {"messages": [HumanMessage(content=user_input)]}

    # Menjalankan graph
    result = await graph.ainvoke(input_state, config=config)
    messages = result.get("messages", [])
    if messages:
        return messages[-1].content
    return "Tidak ada respon dari asisten."
