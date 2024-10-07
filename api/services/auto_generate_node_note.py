import os
import threading
import requests
import json
from ..utils.openai import OpenaiUtil
from ..models import Node

socket_url = os.environ.get('SOCKET_URL')

class AutoGenerateNodeNote:
    @staticmethod
    def run(node, instruction=None):
        node_id = node.id
        flow_data = json.loads(node.flow_data)
        node_title = node.title if node.title else flow_data['data']['label']
        nodes = list(Node.objects.filter(mind_map=node.mind_map).values('id', 'title', 'parent'))
        
        default_message = f"""
        I want to create a note & here's the whole content structure.

        {nodes}

        **I'm currently thinking about {node_title} with node id {node_id}**

        Instruction:
        """
        default_instruction = f"""
        {default_message}
        Explain this subtopic in 300 words.
        """
        new_instruction = f"""
        {default_message}
        {instruction}
        """
        message = new_instruction if instruction else default_instruction
        messages = [
            {"role": "system", "content": "You are a content generator."},
            {"role": "user", "content": message}
        ]
        
        def on_stream(result):
            try:
                response = requests.post(
                    socket_url,
                    json={
                      "isSuccess": True,
                      "action": 'notaminda-node-auto-generate-note',
                      "datasetId": node_id,
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

        def run_chat_stream(callback):
            try:
                OpenaiUtil.chat_stream(messages=messages, on_stream=on_stream)
            except Exception as e:
                print(f"Error in chat_stream: {str(e)}")
            finally:
                callback()

        def thread_finished_callback():
            try:
                response = requests.post(
                    socket_url,
                    json={
                      "isSuccess": True,
                      "action": 'notaminda-node-auto-generate-note-finished',
                      "datasetId": node_id,
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"Error sending streaming result: {str(e)}")

        thread = threading.Thread(target=run_chat_stream, args=(thread_finished_callback,))
        thread.start()

        return {"success": True, "message": "Stream started"}
