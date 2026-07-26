from agents.vision_agent import analyze_image

hasil = analyze_image("banjir_ringan.jpg")

print(hasil.model_dump())