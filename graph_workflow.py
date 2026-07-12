from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

#import function agent
from agents.router_agent import route_message
from agents.validator_agent import validasi_laporan
from agents.retriever_agent import retrieve_sop_info
from agents.executor_agent import execute_response
#state
class GraphState(TypedDict):
    user_message: str
    lat: Optional[float]
    lon: Optional[float]
    intent: Optional[str] #hasil router agent
    validation_data: Optional[dict] #hasil validator agent
    context_data: Optional[str] #hasil retriever agent
    
    #hasil akhir executor agent
    final_response: Optional[str]
    eskalasi_posko: Optional[bool]
    kategori_laporan: Optional[str] 

#node
def node_router(state:GraphState):
    print("\n[NODE] masuk ke agen router...")
    hasil_router = route_message(state["user_message"])
    return {"intent" : hasil_router.intent}

def node_validator(state:GraphState):
    print("\n[NODE] masuk ke agen validator...")
    #jika gps tidak aktif, nilai default = 0.0
    lat = state.get("lat") or 0.0
    lon = state.get("lon") or 0.0
    hasil_validasi = validasi_laporan(state["user_message"], lat, lon)
    return {"validation_data": hasil_validasi}

def node_retriever(state:GraphState):
    print("\n[NODE] masuk ke agen retriever...")
    teks_sop_mentah = retrieve_sop_info(state["user_message"])
    return {"context_data": teks_sop_mentah}


def node_executor(state:GraphState):
    print("\n[NODE] masuk ke agen executor...")
    hasil_eksekutor = execute_response(
        intent=state.get("intent", "lainnya"),
        user_message=state["user_message"],
        context_data=state.get("context_data", ""),
        validation_data=state.get("validation_data", None)
    )
    return {
        "final_response": hasil_eksekutor.balasan_warga,
        "eskalasi_posko": hasil_eksekutor.eskalasi_posko,
        "kategori_laporan": hasil_eksekutor.kategori_laporan
    }

#logika pemilah jalur
def route_after_classification(state: GraphState):
    intent = state.get("intent")
    if intent == "lapor_darurat":
        return "validator"
    elif intent == "tanya_info":
        return "retriever"
    else:
        return "executor" #kalau spam atau kategori 'lainnya'

#bangun grafik
workflow = StateGraph(GraphState)

#tambah node
workflow.add_node("router", node_router)
workflow.add_node("validator", node_validator)
workflow.add_node("retriever", node_retriever)
workflow.add_node("executor", node_executor)

workflow.set_entry_point("router") #titik masuk
#conditional edges
workflow.add_conditional_edges(
    "router",
    route_after_classification,
    {
        "validator": "validator", #if return validator = jalan ke node validator
        "retriever": "retriever", #if return retriever =  jalan ke node retriever
        "executor": "executor"   #if return executor = jalan ke node executor
    }
)

#normal edges
workflow.add_edge("validator", "executor")
workflow.add_edge("retriever", "executor") 
workflow.add_edge("executor", END) 

app = workflow.compile()

#pengujian
if __name__ == "__main__":
    print("="*50)
    print("PENGUJIAN SISTEM SECARA KESELURUHAN")
    print("="*50)
    
    #contoh input dari warga
    input_awal = {
        "user_message": "Tolong bantu, ada banjir besar di daerah saya!",
        "lat": -6.200000,
        "lon": 106.816666
    }

    hasil_akhir = app.invoke(input_awal)

    print("HASIL AKHIR:")
    print("Intent: ", hasil_akhir.get("intent"))
    print("Balasan untuk Warga: ", hasil_akhir.get("final_response"))
    print("Eskalasi ke Posko:", hasil_akhir.get("eskalasi_posko"))
    print("Kategori Laporan:", hasil_akhir.get("kategori_laporan"))