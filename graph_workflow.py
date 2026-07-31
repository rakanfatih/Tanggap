from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from agents.router_agent import route_message
from agents.validator_agent import validasi_laporan
from agents.retriever_agent import retrieve_sop_info
from agents.decision_agent import make_decision
from agents.executor_agent import execute_response
from agents.vision_agent import analyze_image


# graph state
class GraphState(TypedDict):

    # input
    user_message: str
    lat: Optional[float]
    lon: Optional[float]
    image_path: Optional[str]
    chat_history: Optional[str]

    # router
    intent: Optional[str]
    disaster_type: Optional[str]
    confidence: Optional[float]
    router_reason: Optional[str]

    # validator
    validation_score: Optional[int]
    gps_valid: Optional[bool]
    alamat_lengkap: Optional[str]
    kondisi_cuaca: Optional[str]
    suhu: Optional[float]
    is_hujan: Optional[bool]

    # vision
    image_path: Optional[str]
    flood_detected: Optional[bool]
    vision_confidence: Optional[float]
    severity: Optional[str]
    estimated_water_level: Optional[str]
    estimated_water_cm: Optional[float]
    water_percentage: Optional[float]
    visible_objects: Optional[list]
    object_count: Optional[int]
    image_quality: Optional[str]
    possible_fake: Optional[bool]
    vision_reason: Optional[str]
    vision_image_path: Optional[str]

    # retriever
    context: Optional[str]
    total_references: Optional[int]

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
        state["user_message"],
        chat_history=state.get("chat_history")

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
        "validation_score": hasil["validation_score"],
        "gps_valid": hasil["gps_valid"],
        "alamat_lengkap": hasil["alamat_lengkap"],
        "kondisi_cuaca": hasil["kondisi_cuaca"],
        "suhu": hasil["suhu"],
        "is_hujan": hasil["is_hujan"]
    }

# vision node
def node_vision(state: GraphState):

    print("\n[NODE] Vision")
    image_path = state.get("image_path")

    if not image_path:
        print("Tidak ada gambar.")
        return {}

    hasil = analyze_image(image_path)
    return {
        "flood_detected": hasil.flood_detected,
        "vision_confidence": hasil.confidence,
        "severity": hasil.severity,
        "estimated_water_level": hasil.estimated_water_level,
        "estimated_water_cm": hasil.estimated_water_cm,
        "water_percentage": hasil.water_percentage,
        "visible_objects": hasil.visible_objects,
        "object_count": hasil.object_count,
        "image_quality": hasil.image_quality,
        "possible_fake": hasil.possible_fake,
        "vision_reason": hasil.reason,
        "vision_image_path": hasil.vision_image_path
    }

# retriever node
def node_retriever(state: GraphState):

    print("\n[NODE] Retriever")

    hasil = retrieve_sop_info(
        query=state["user_message"]
    )

    return {
        "context": hasil["context"],
        "total_references": hasil["total_references"]
    }

# decision node
def node_decision(state: GraphState):

    print("\n[NODE] Decision")

    hasil = make_decision(
        intent=state["intent"],
        disaster_type=state["disaster_type"],
        validation_score=state.get("validation_score"),
        flood_detected=state.get("flood_detected"),
        vision_confidence=state.get("vision_confidence"),
        possible_fake=state.get("possible_fake"),
        severity=state.get("severity")
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

    hasil = execute_response(
        user_message=state["user_message"],
        intent=state["intent"],
        action=state["action"],
        kategori_laporan=state["kategori_laporan"],
        reason=state["decision_reason"],
        context=state.get("context", ""),
        chat_history=state.get("chat_history", "")
    )

    return {
        "final_response": hasil.final_response
    }

# routing
def router_condition(state: GraphState):

    intent = state["intent"]

    if intent == "lapor_darurat":
        return ["validator", "vision"]
    elif intent == "tanya_info":
        return "retriever"
    else:
        return "decision"

# build  
workflow = StateGraph(GraphState)

workflow.add_node("router", node_router)
workflow.add_node("validator", node_validator)
workflow.add_node("vision", node_vision)
workflow.add_node("retriever", node_retriever)
workflow.add_node("decision", node_decision)
workflow.add_node("executor", node_executor)

workflow.set_entry_point("router")

workflow.add_conditional_edges(
    "router",
    router_condition,
    ["validator", "vision", "retriever", "decision"]
)

workflow.add_edge("validator","decision")
workflow.add_edge("vision","decision")
workflow.add_edge("retriever","decision")
workflow.add_edge("decision","executor")
workflow.add_edge("executor",END)

app = workflow.compile()

# test
if __name__ == "__main__":

    hasil = app.invoke(
        {
            "user_message": "Rumah saya kebanjiran.",
            "lat": -6.200000,
            "lon": 106.816666,
            "image_path": "banjir.jpg"
        }
    )

    print("\n==============================")
    print("HASIL AKHIR")
    print("==============================")

    print(f"Intent               : {hasil.get('intent')}")
    print(f"Disaster Type        : {hasil.get('disaster_type')}")
    print(f"Confidence           : {hasil.get('confidence')}")
    print(f"Flood Detected       : {hasil.get('flood_detected')}")
    print(f"Vision Confidence    : {hasil.get('vision_confidence')}")
    print(f"Severity             : {hasil.get('severity')}")
    print(f"Estimated Water      : {hasil.get('estimated_water_cm')} cm")
    print(f"Water Area           : {hasil.get('water_percentage')} %")
    print(f"Possible Fake        : {hasil.get('possible_fake')}")
    print(f"Action               : {hasil.get('action')}")
    print(f"Eskalasi Posko       : {hasil.get('eskalasi_posko')}")
    print(f"Kategori             : {hasil.get('kategori_laporan')}")
    print(f"Final Response       : {hasil.get('final_response')}")