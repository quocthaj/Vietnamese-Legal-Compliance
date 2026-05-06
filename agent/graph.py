from typing import TypedDict, Annotated, Optional
import operator
from langgraph.graph import StateGraph, START, END

from nodes import query_analyzer, retriever, generator_node, judge

# Define State
class AgentState(TypedDict):
    keywords: list[str]
    so_dieu: Optional[str]
    ten_van_ban: Optional[str]
    intent: str
    query: str
    is_ambiguous: bool  # câu hỏi mơ hồ
    context: str  # thông tin thu thập được từ luật
    answer: str  # câu trả lời
    retriever_count: Annotated[int, operator.add]
    generator_count: Annotated[int, operator.add]
    is_sufficient: bool
    pass_judge: bool

# Placeholder for ambiguous query handling (can be kept simple)
def clarify_node(state: AgentState) -> dict:
    """Ask user to clarify ambiguous query (fallback)."""
    print("Node: clarify_node")
    return {"answer": "Bạn có thể làm rõ câu hỏi hơn được không?"}

# Map node names to imported functions
# query_analyzer, retriever, generator, judge will refer to the imported implementations

# Define Edge Logic Functions
def check_ambiguity(state: AgentState) -> str:
    """Determine whether the query is ambiguous."""
    if state.get("is_ambiguous", False):
        return "clarify_node"
    return "retriever"

def should_generate(state: AgentState) -> str:
    if state.get("is_sufficient", False) or state.get("retriever_count", 0) >= 3:
        return "generator"
    return "retriever"  
def check_judge(state: AgentState) -> str:
    """Determine whether to end or regenerate."""
    if state.get("pass_judge", False) or state.get("generator_count", 0) >= 3:
        return END
    return "generator"
# Build Graph
workflow = StateGraph(AgentState)
# Add Nodes
workflow.add_node("query_analyzer", query_analyzer)
workflow.add_node("clarify_node", clarify_node)
workflow.add_node("retriever", retriever)
workflow.add_node("generator", generator_node)
workflow.add_node("judge", judge)
# Add Edges
workflow.add_edge(START, "query_analyzer")

# Conditional edge from query_analyzer
workflow.add_conditional_edges(
    "query_analyzer",
    check_ambiguity,
    {
        "clarify_node": "clarify_node",
        "retriever": "retriever"
    }
)
# Edge from clarify_node directly to END
workflow.add_edge("clarify_node", END)
# Conditional edge from Retriever
workflow.add_conditional_edges(
    "retriever",
    should_generate,
    {
        "generator": "generator",
        "retriever": "retriever"
    }
)
# Edge from Generator to Judge
workflow.add_edge("generator", "judge")
# Conditional edge from Judge
workflow.add_conditional_edges(
    "judge",
    check_judge,
    {
        END: END,
        "generator": "generator"
    }
)
# Compile Graph
app = workflow.compile()