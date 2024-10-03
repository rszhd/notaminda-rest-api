from django.http import JsonResponse
from ..utils import chat_stream
import threading
import requests
import os

def chat_view(request):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me a joke"}
    ]

    def on_stream(result):
        try:
            response = requests.post(
                os.environ.get('SOCKET_URL'),
                json={
                  "isSuccess": True,
                  "action": 'notamindastatus',
                  "datasetId": "notaminda",
                  "data": {
                    "reply": result
                  }
                },
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error sending streaming result: {str(e)}")

    def run_chat_stream():
        try:
            chat_stream(
                messages=messages,
                on_stream=on_stream
            )
        except Exception as e:
            print(f"Error in chat_stream: {str(e)}")

    thread = threading.Thread(target=run_chat_stream)
    thread.start()
    return JsonResponse({"success": True, "message": "Chat stream started"})
