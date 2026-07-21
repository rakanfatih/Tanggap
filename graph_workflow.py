from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from agents.router_agent import route_message
from agents.validator_agent import validasi_laporan
from agents.retriever_agent import retrieve_sop_info
from agents.decision_agent import make_decision
from agents.executor_agent import execute_response

# graph state
class GraphState(TypedDict):

    # input
    user_message: str
    lat: Optional[float]
    lon: Optional[float]

    # router
    intent: Optional[str]
    disaster_type: Optional[str]
    confidence: Optional[float]
    router_reason: Optional[str]

    # validator
    validation_data: Optional[dict]

    # retriever
    retrieval_data: Optional[dict]

    # decision
    action: Optional[str]
    eskalasi_posko: Optional[bool]
    kategori_laporan: Optional[str]
    decision_reason: Optional[str]

    # executor
    final_response: Optional[str]

# router node
def node_router(state: GraphState):

    print("\n[NODE] Router")

    hasil = route_message(
        state["user_message"]
    )

    return {
        "intent": hasil.intent,
        "disaster_type": hasil.disaster_type,
        "confidence": hasil.confidence,
        "router_reason": hasil.alasan
    }

# validator node
def node_validator(state: GraphState):

    print("\n[NODE] Validator")

    hasil = validasi_laporan(
        user_message=state["user_message"],
        lat=state.get("lat", 0.0),
        lon=state.get("lon", 0.0)
    )

    return {
        "validation_data": hasil
    }

# retriever node
def node_retriever(state: GraphState):

    print("\n[NODE] Retriever")

    hasil = retrieve_sop_info(
        query=state["user_message"]
    )

    return {
        "retrieval_data": hasil
    }

# decision node
def node_decision(state: GraphState):

    print("\n[NODE] Decision")

    validation_score = None

    if state.get("validation_data"):
        validation_score = state["validation_data"]["validation_score"]

    hasil = make_decision(
        intent=state["intent"],
        disaster_type=state["disaster_type"],
        validation_score=validation_score
    )

    return {
        "action": hasil.action,
        "eskalasi_posko": hasil.eskalasi_posko,
        "kategori_laporan": hasil.kategori_laporan,
        "decision_reason": hasil.reason
    }

# executor node
def node_executor(state: GraphState):

    print("\n[NODE] Executor")

    context = ""

    if state.get("retrieval_data"):
        context = state["retrieval_data"]["context"]

    hasil = execute_response(
        user_message=state["user_message"],
        intent=state["intent"],
        action=state["action"],
        kategori_laporan=state["kategori_laporan"],
        reason=state["decision_reason"],
        context=context
    )

    return {
        "final_response": hasil.final_response
    }

# routing
def router_condition(state: GraphState):

    intent = state["intent"]

    if intent == "lapor_darurat":
        return "validator"
    elif intent == "tanya_info":
        return "retriever"
    else:
        return "decision"

# build  
workflow = StateGraph(GraphState)

workflow.add_node(
    "router",
    node_router
)

workflow.add_node(
    "validator",
    node_validator
)

workflow.add_node(
    "retriever",
    node_retriever
)

workflow.add_node(
    "decision",
    node_decision
)

workflow.add_node(
    "executor",
    node_executor
)

workflow.set_entry_point(
    "router"
)

workflow.add_conditional_edges(
    "router",
    router_condition,
    {
        "validator": "validator",
        "retriever": "retriever",
        "decision": "decision"
    }
)

workflow.add_edge(
    "validator",
    "decision"
)

workflow.add_edge(
    "retriever",
    "decision"
)

workflow.add_edge(
    "decision",
    "executor"
)

workflow.add_edge(
    "executor",
    END
)

app = workflow.compile()

# test
if __name__ == "__main__":

    hasil = app.invoke(
        {
            "user_message": "Rumah saya kebanjiran.",
            "lat": -6.200000,
            "lon": 106.816666
        }
    )

    print("\n==============================")
    print("HASIL AKHIR")
    print("==============================")

    print(f"Intent               : {hasil.get('intent')}")
    print(f"Disaster Type        : {hasil.get('disaster_type')}")
    print(f"Confidence           : {hasil.get('confidence')}")
    print(f"Action               : {hasil.get('action')}")
    print(f"Eskalasi Posko       : {hasil.get('eskalasi_posko')}")
    print(f"Kategori             : {hasil.get('kategori_laporan')}")
    print(f"Final Response       : {hasil.get('final_response')}")