from typing import TypedDict, Annotated, Sequence, Optional
import operator
from langgraph.graph import StateGraph, START, END
# Define State
class AgentState(TypedDict):
    keywords: list[str]
    so_dieu: Optional[str]
    ten_van_ban: Optional[str]
    intent: str
    query: str
    is_ambiguous: bool #câu hỏi mơ hồ
    context: str #thông tin thu thập được từ luật
    answer: str #câu trả lời
    retriever_count: Annotated[int, operator.add] #số lần truy xuất
    generator_count: Annotated[int, operator.add] #số lần sinh câu trả lời
    is_sufficient: bool #đủ thông tin
    pass_judge: bool #đạt yêu cầu của judge

# Define Nodes
def query_analyzer(state: AgentState) -> dict:
    """Analyze the user's query."""
    print("Node: query_analyzer")
    # Giả lập query_analyzer: trả về False cho is_ambiguous
    return {"is_ambiguous": True}

def clarify_node(state: AgentState) -> dict:
    """Ask user to clarify ambiguous query."""
    print("Node: clarify_node")
    return {"answer": "Bạn có thể làm rõ câu hỏi hơn được không?"}
def retriever(state: AgentState) -> dict:
    """Retrieve documents and check if they are sufficient."""
    print("Node: retriever")
    # Increment retriever count
    return {"retriever_count": 1}
def generator(state: AgentState) -> dict:
    """Generate answer based on context."""
    print("Node: generator")
    return {"generator_count": 1}
def judge(state: AgentState) -> dict:
    """Evaluate the generated answer."""
    print("Node: judge")
    
    # Giả lập logic chấm điểm của Judge (sẽ thay bằng LLM call sau)
    is_passed = False 
    
    if not is_passed:
        return {"pass_judge": False}
        
    return {"pass_judge": True}
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
workflow.add_node("generator", generator)
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
result = app.invoke({
    "query": "an ninh mạng là gì",
    "is_ambiguous": True,
    "retriever_count": 0,
    "generator_count": 0,
    "is_sufficient": False,
    "pass_judge": False,
    "context": "",
    "answer": ""
})
print(result)