from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.core.config import settings
from app.services.ai_agent.state import AgentState


def build_graph(tools: list):
    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=0.2,
        timeout=45,
        max_retries=1,
    ).bind_tools(tools)

    def call_model(state: AgentState):
        messages = [SystemMessage(content=state.get("system_prompt", ""))]
        messages.extend(state["messages"])
        response = llm.invoke(messages)
        return {"messages": [response]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(tools, handle_tool_errors=True))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    return graph.compile()
