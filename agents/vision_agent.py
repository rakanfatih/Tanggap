import os
import base64
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="meta-llama/llama-4-scout-17b-16e-instruct"
)


def encode_image(path: str):

    with open(path, "rb") as image:

        return base64.b64encode(
            image.read()
        ).decode("utf-8")


def analyze_image(image_path: str):

    print("\n==============================")
    print("[VISION AGENT]")
    print("==============================")

    if image_path is None:
        return {
            "image_validation": False,
            "image_confidence": 0.0,
            "image_description": "Tidak ada gambar."
        }

    if not os.path.exists(image_path):
        return {
            "image_validation": False,
            "image_confidence": 0.0,
            "image_description": "File gambar tidak ditemukan."
        }

    try:

        image = encode_image(image_path)
        prompt = """
Anda adalah Vision Agent pada sistem pelaporan banjir.

Analisis gambar.

Jawab hanya dalam format berikut.

VALID : YA / TIDAK

CONFIDENCE : 0-100

DESKRIPSI :
...
"""

        response = llm.invoke(
            [
                HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": prompt
                        },

                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image}"
                            }
                        }
                    ]
                )
            ]
        )

        hasil = response.content
        print(hasil)
        valid = "YA" in hasil.upper()
        confidence = 0
        for line in hasil.split("\n"):

            if "CONFIDENCE" in line.upper():
                angka = "".join(
                    c for c in line
                    if c.isdigit()
                )

                if angka:
                    confidence = float(angka)

        return {
            "image_validation": valid,
            "image_confidence": confidence,
            "image_description": hasil
        }

    except Exception as e:
        print(e)
        return {
            "image_validation": False,
            "image_confidence": 0,
            "image_description": str(e)
        }


if __name__ == "__main__":

    hasil = analyze_image(
        "uploads/contoh.jpg"
    )
    print(hasil)