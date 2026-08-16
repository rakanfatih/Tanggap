from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from agents.router_agent import route_message
from agents.validator_agent import validasi_laporan
from agents.retriever_agent import retrieve_sop_info
from agents.decision_agent import make_decision
from agents.executor_agent import execute_response
from agents.vision_agent import analyze_image


# graph State
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
    suhu: Optional[float]
    kategori_hujan: Optional[str]
    curah_hujan_mm: Optional[float]
    poin_cuaca: Optional[int]

    # vision
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


# nodes
def node_router(state: GraphState):
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


def node_validator(state: GraphState):
    hasil = validasi_laporan(
        user_message=state["user_message"],
        lat=state.get("lat", 0.0),
        lon=state.get("lon", 0.0)
    )

    return {
        "validation_score": hasil["validation_score"],
        "gps_valid": hasil["gps_valid"],
        "alamat_lengkap": hasil["alamat_lengkap"],
        "suhu": hasil["suhu"],
        "kategori_hujan": hasil["kategori_hujan"],
        "curah_hujan_mm": hasil["curah_hujan_mm"],
        "poin_cuaca": hasil["poin_cuaca"]
    }


def node_vision(state: GraphState):
    image_path = state.get("image_path")
    if not image_path:
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


def node_retriever(state: GraphState):
    hasil = retrieve_sop_info(query=state["user_message"])

    return {
        "context": hasil["context"],
        "total_references": hasil["total_references"]
    }


def node_decision(state: GraphState):
    object_count = state.get("object_count", 0)
    flood_detected = state.get("flood_detected", False)
    
    # jika ada banjir, tapi tidak ada objek referensi
    eskalasi_paksa = flood_detected and object_count == 0

    hasil = make_decision(
        intent=state.get("intent", ""),
        disaster_type=state.get("disaster_type", ""),
        validation_score=state.get("validation_score"),
        flood_detected=state.get("flood_detected"),
        vision_confidence=state.get("vision_confidence"),
        possible_fake=state.get("possible_fake"),
        severity=state.get("severity"),
        object_count=state.get("object_count")
    )

    reason_final = hasil.reason + (" (ditambah: eskalasi paksa karena kedalaman air tidak dapat diverifikasi visual)." if eskalasi_paksa else "")

    return {
        "action": hasil.action,
        "eskalasi_posko": hasil.eskalasi_posko or eskalasi_paksa,
        "kategori_laporan": hasil.kategori_laporan,
        "decision_reason": reason_final
    }


def node_executor(state: GraphState):
    hasil = execute_response(
        user_message=state["user_message"],
        intent=state.get("intent", ""),
        action=state.get("action", ""),
        kategori_laporan=state.get("kategori_laporan", ""),
        reason=state.get("decision_reason", ""),
        context=state.get("context", ""),
        chat_history=state.get("chat_history", "")
    )

    return {
        "final_response": hasil.final_response
    }


# edge routing and workflow compilation
def router_condition(state: GraphState):
    intent = state["intent"]
    if intent == "lapor_darurat":
        return "validator"
    elif intent == "tanya_info":
        return "retriever"
    else:
        return "decision"


# build graph
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
    ["validator", "retriever", "decision"]
)

workflow.add_edge("validator", "vision")
workflow.add_edge("vision", "decision")
workflow.add_edge("retriever", "decision")
workflow.add_edge("decision", "executor")
workflow.add_edge("executor", END)

app = workflow.compile()