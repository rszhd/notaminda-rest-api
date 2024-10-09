import os
import concurrent.futures
import requests
import json
from typing import List, Dict, Any, Optional
from rest_framework.exceptions import APIException

from ..utils.openai import OpenaiUtil
from ..models import Node

SOCKET_URL = os.environ.get("SOCKET_URL")

thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)


class NodeNoteGenerator:
    @classmethod
    def generate(
        cls,
        node: Node,
        instruction: Optional[str] = None,
        ai_key: Optional[str] = None,
        ai_model: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            nodes = cls._get_nodes(node)
            message = cls._create_message(node, nodes, instruction)
            messages = cls._create_chat_messages(message)

            # Submit the task to the thread pool instead of creating a new thread
            thread_pool.submit(
                cls._run_chat_stream, node.id, messages, ai_key, ai_model
            )

            return {"success": True, "message": "Stream started"}
        except Exception as e:
            raise APIException(f"Failed to start auto-generation: {str(e)}")

    @staticmethod
    def _get_nodes(node: Node) -> List[Dict[str, Any]]:
        nodes = Node.objects.filter(mind_map=node.mind_map).values(
            "id", "title", "parent", "flow_data"
        )
        return [
            {
                "id": node["id"],
                "label": (
                    json.loads(node["flow_data"])["data"]["label"]
                    if node["flow_data"]
                    else node["title"]
                ),
                "parent": node["parent"],
            }
            for node in nodes
        ]

    @staticmethod
    def _create_message(
        node: Node, nodes: List[Dict[str, Any]], instruction: Optional[str]
    ) -> str:
        flow_data = json.loads(node.flow_data)
        node_title = node.title or flow_data["data"]["label"]

        default_message = f"""
        I want to create a note & here's the whole content structure.

        {nodes}

        **I'm currently thinking about a topic with a title '{node_title}' & node id '{node.id}'**

        Instruction:
        """

        if instruction:
            return f"{default_message}\n{instruction}"
        else:
            return f"{default_message}\nExplain this subtopic in 300 words."

    @staticmethod
    def _create_chat_messages(message: str) -> List[Dict[str, str]]:
        return [
            {"role": "system", "content": "You are a content generator."},
            {"role": "user", "content": message},
        ]

    @classmethod
    def _run_chat_stream(
        cls,
        node_id: int,
        messages: List[Dict[str, str]],
        ai_key: Optional[str],
        ai_model: Optional[str],
    ):
        try:
            OpenaiUtil.chat_stream(
                messages=messages,
                on_stream=lambda result: cls._send_stream_result(node_id, result),
                api_key=ai_key,
                model=ai_model,
            )
        except Exception as e:
            print(f"Error in chat_stream: {str(e)}")
        finally:
            cls._send_finished_notification(node_id)

    @classmethod
    def _send_stream_result(cls, node_id: int, result: str):
        cls._send_socket_request(
            action="notaminda-node-auto-generate-note",
            dataset_id=node_id,
            data={"reply": result},
        )

    @classmethod
    def _send_finished_notification(cls, node_id: int):
        cls._send_socket_request(
            action="notaminda-node-auto-generate-note-finished", dataset_id=node_id
        )

    @classmethod
    def _send_socket_request(
        cls, action: str, dataset_id: int, data: Optional[Dict[str, Any]] = None
    ):
        try:
            payload = {
                "isSuccess": True,
                "action": action,
                "datasetId": dataset_id,
            }
            if data:
                payload["data"] = data

            response = requests.post(
                SOCKET_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error sending socket request: {str(e)}")
