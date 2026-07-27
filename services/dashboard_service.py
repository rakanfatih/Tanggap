import json


def send_to_dashboard(data):

    print("\n==============================")
    print("[SEND TO DASHBOARD]")
    print("==============================")

    print(
        json.dumps(
            data,
            indent=4,
            ensure_ascii=False
        )
    )

    return True