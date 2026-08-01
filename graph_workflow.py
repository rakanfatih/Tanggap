import time
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

# router node
def node_router(state: GraphState):
    start_time = time.time()
    print("\n" + "="*50)
    print("[NODE] ROUTER AGENT")
    print("-" * 50)
    print("INPUT DARI USER:")
    print(f"   - Pesan: {state['user_message']}")

    hasil = route_message(
        state["user_message"],
        chat_history=state.get("chat_history")
    )

    latensi = time.time() - start_time
    print("-" * 50)
    print("OUTPUT ROUTER AGENT:")
    print(f"   - Intent        : {hasil.intent}")
    print(f"   - Disaster Type : {hasil.disaster_type}")
    print(f"   - Confidence    : {hasil.confidence}")
    print(f"   - Alasan        : {hasil.alasan}")
    print(f"    Latensi Node  : {latensi:.2f} detik")
    print("=" * 50)

    return {
        "intent": hasil.intent,
        "disaster_type": hasil.disaster_type,
        "confidence": hasil.confidence,
        "router_reason": hasil.alasan
    }

# validator node
def node_validator(state: GraphState):
    start_time = time.time()
    print("\n" + "="*50)
    print("[NODE] VALIDATOR AGENT")
    print("-" * 50)
    print("INPUT DARI USER:")
    print(f"   - Koordinat: [{state.get('lat', 0.0)}, {state.get('lon', 0.0)}]")

    hasil = validasi_laporan(
        user_message=state["user_message"],
        lat=state.get("lat", 0.0),
        lon=state.get("lon", 0.0)
    )

    latensi = time.time() - start_time
    print("-" * 50)
    print("OUTPUT VALIDATOR AGENT:")
    print(f"   - Alamat Lengkap: {hasil['alamat_lengkap']}")
    print(f"   - GPS Valid     : {hasil['gps_valid']}")
    print(f"   - Cuaca         : {hasil['kategori_hujan']} ({hasil['curah_hujan_mm']} mm)")
    print(f"   - Val. Score    : {hasil['validation_score']}")
    print(f"    Latensi Node  : {latensi:.2f} detik")
    print("=" * 50)

    return {
        "validation_score": hasil["validation_score"],
        "gps_valid": hasil["gps_valid"],
        "alamat_lengkap": hasil["alamat_lengkap"],
        "suhu": hasil["suhu"],
        "kategori_hujan": hasil["kategori_hujan"],
        "curah_hujan_mm": hasil["curah_hujan_mm"],
        "poin_cuaca": hasil["poin_cuaca"]
    }

# vision node
def node_vision(state: GraphState):
    start_time = time.time()
    print("\n" + "="*50)
    print("[NODE] VISION AGENT")
    print("-" * 50)
    
    image_path = state.get("image_path")
    if not image_path:
        print("Tidak ada gambar yang dilampirkan.")
        print("=" * 50)
        return {}

    print(f"INPUT DARI USER:")
    print(f"   - Image Path: {image_path}")

    hasil = analyze_image(image_path)

    latensi = time.time() - start_time
    print("-" * 50)
    print("OUTPUT VISION AGENT:")
    print(f"   - Flood Detected: {hasil.flood_detected}")
    print(f"   - Confidence    : {hasil.confidence}")
    print(f"   - Severity      : {hasil.severity}")
    print(f"   - Est. Water    : {hasil.estimated_water_cm} cm")
    print(f"   - Objects Found : {hasil.object_count} {hasil.visible_objects}")
    print(f"   - Possible Fake : {hasil.possible_fake}")
    print(f"    Latensi Node  : {latensi:.2f} detik")
    print("=" * 50)

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
    start_time = time.time()
    print("\n" + "="*50)
    print("[NODE] RETRIEVER AGENT")
    print("-" * 50)
    print("INPUT DARI USER:")
    print(f"   - Query: {state['user_message']}")

    hasil = retrieve_sop_info(query=state["user_message"])

    latensi = time.time() - start_time
    print("-" * 50)
    print("OUTPUT RETRIEVER AGENT:")
    print(f"   - Total Referensi: {hasil['total_references']}")
    print(f"    Latensi Node   : {latensi:.2f} detik")
    print("=" * 50)

    return {
        "context": hasil["context"],
        "total_references": hasil["total_references"]
    }

# decision node
def node_decision(state: GraphState):
    start_time = time.time()
    print("\n" + "="*50)
    print("[NODE] DECISION AGENT")
    print("-" * 50)
    print("MENGAMBIL DATA DARI AGENT LAIN:")
    print(f"   - Intent (Router)       : {state.get('intent')}")
    print(f"   - Disaster (Router)     : {state.get('disaster_type')}")
    print(f"   - Val. Score (Validator): {state.get('validation_score')}")
    print(f"   - Flood Det. (Vision)   : {state.get('flood_detected')}")
    print(f"   - Vis. Conf. (Vision)   : {state.get('vision_confidence')}")
    print(f"   - Severity (Vision)     : {state.get('severity')}")
    print(f"   - Obj. Count (Vision)   : {state.get('object_count')}")
    print(f"   - Poss. Fake (Vision)   : {state.get('possible_fake')}")

    object_count = state.get("object_count", 0)
    flood_detected = state.get("flood_detected", False)
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

    reason_final = hasil.reason + (" (Ditambah: Eskalasi paksa karena kedalaman air tidak dapat diverifikasi visual)." if eskalasi_paksa else "")

    latensi = time.time() - start_time
    print("-" * 50)
    print("OUTPUT DECISION AGENT:")
    print(f"   - Action          : {hasil.action}")
    print(f"   - Eskalasi Posko  : {hasil.eskalasi_posko or eskalasi_paksa}")
    print(f"   - Kategori Laporan: {hasil.kategori_laporan}")
    print(f"   - Alasan          : {reason_final}")
    print(f"    Latensi Node  : {latensi:.2f} detik")
    print("=" * 50)

    return {
        "action": hasil.action,
        "eskalasi_posko": hasil.eskalasi_posko or eskalasi_paksa,
        "kategori_laporan": hasil.kategori_laporan,
        "decision_reason": reason_final
    }

# executor node
def node_executor(state: GraphState):
    start_time = time.time()
    print("\n" + "="*50)
    print("[NODE] EXECUTOR AGENT")
    print("-" * 50)
    print("MENGAMBIL DATA DARI AGENT LAIN:")
    print(f"   - Intent (Router)   : {state.get('intent')}")
    print(f"   - Action (Decision) : {state.get('action')}")
    print(f"   - Kategori (Decision): {state.get('kategori_laporan')}")
    print(f"   - Alasan (Decision) : {state.get('decision_reason')}")
    
    context_info = "Ada" if state.get("context") else "Tidak Ada (Atau Kosong)"
    print(f"   - Context (Retriever): {context_info}")

    hasil = execute_response(
        user_message=state["user_message"],
        intent=state.get("intent", ""),
        action=state.get("action", ""),
        kategori_laporan=state.get("kategori_laporan", ""),
        reason=state.get("decision_reason", ""),
        context=state.get("context", ""),
        chat_history=state.get("chat_history", "")
    )

    latensi = time.time() - start_time
    print("-" * 50)
    print("OUTPUT EXECUTOR AGENT:")
    print(f"   - Final Response: \n{hasil.final_response}")
    print(f"    Latensi Node  : {latensi:.2f} detik")
    print("=" * 50)

    return {
        "final_response": hasil.final_response
    }

# routing condition
def router_condition(state: GraphState):
    intent = state["intent"]
    if intent == "lapor_darurat":
        return ["validator", "vision"]
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
    ["validator", "vision", "retriever", "decision"]
)

workflow.add_edge("validator", "decision")
workflow.add_edge("vision", "decision")
workflow.add_edge("retriever", "decision")
workflow.add_edge("decision", "executor")
workflow.add_edge("executor", END)

app = workflow.compile()

# test
if __name__ == "__main__":
    
    print("\nMEMULAI PROSES MULTI-AGENT...\n")
    
    start_total = time.time()

    hasil = app.invoke(
        {
            "user_message": "Rumah saya kebanjiran.",
            "lat": -6.200000,
            "lon": 106.816666,
            "image_path": "uploads/banjir1.jpg"
        }
    )

    end_total = time.time()
    latensi_total = end_total - start_total

    print("\n" + "="*50)
    print("HASIL AKHIR GRAPH")
    print("="*50)
    for key, value in hasil.items():
        if key in ["context", "chat_history"] and value:
            print(f"{key.upper():<20} : [Berisi teks panjang...]")
        else:
            print(f"{key.upper():<20} : {value}")
    print(f"\nTOTAL WAKTU EKSEKUSI : {latensi_total:.2f} detik")
    print("="*50 + "\n")