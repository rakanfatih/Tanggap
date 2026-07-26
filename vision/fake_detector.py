FAKE_OBJECTS = [
    "cat",
    "dog",
    "tv",
    "laptop",
    "keyboard",
    "mouse",
    "book",
    "cell phone"
]

FLOOD_RELATED = [
    "person",
    "car",
    "truck",
    "bus",
    "boat",
    "motorcycle"
]

def detect_fake(detections):

    labels = [
        d["label"]
        for d in detections
    ]

    fake_score = 0

    for label in labels:

        if label in FAKE_OBJECTS:
            fake_score += 20

    flood_score = 0

    for label in labels:

        if label in FLOOD_RELATED:
            flood_score += 10

    possible_fake = fake_score > flood_score

    if possible_fake:
        reason = "Objek tidak relevan dengan laporan banjir."

    else:
        reason = "Objek sesuai dengan kondisi banjir."

    return {
        "possible_fake": possible_fake,
        "reason": reason
    }