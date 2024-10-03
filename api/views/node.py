import asyncio
import os
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from ..models import Node
from ..serializers import (
    NodeSerializer,
    NodeCreateSerializer,
    NodeUpdateSerializer,
    GeneratedChildrenSerializer
)
from rest_framework.decorators import action
import threading
import requests
from django.http import JsonResponse
from ..utils import chat_stream

socket_url = os.environ.get('SOCKET_URL')

class NodeViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Node.objects.filter(mind_map__user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return NodeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return NodeUpdateSerializer
        return NodeSerializer

    def perform_create(self, serializer):
        mind_map = serializer.validated_data['mind_map']
        if mind_map.user != self.request.user:
            return Response({"detail": "You can only create nodes for your own mind maps."},
                            status=status.HTTP_403_FORBIDDEN)
        serializer.save()

    def perform_update(self, serializer):
        if serializer.instance.mind_map.user != self.request.user:
            return Response({"detail": "You can only update nodes in your own mind maps."},
                            status=status.HTTP_403_FORBIDDEN)
        serializer.save()

    @action(detail=True, methods=['post'])
    def auto_generate_children(self, request, pk=None):
        node = self.get_object()
        
        if node.mind_map.user != request.user:
            return Response({"detail": "You can only generate children for nodes in your own mind maps."},
                            status=status.HTTP_403_FORBIDDEN)

        num_children = request.data.get('num_children', 3)
        positions = request.data.get('nodes_position')
        ai_key = request.data.get('ai_key')
        ai_model = request.data.get('ai_model')
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        children = loop.run_until_complete(node.generate_children(
            num_children,
            positions,
            ai_key,
            ai_model)
        )
        
        serializer = GeneratedChildrenSerializer({'children': children})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def auto_generate_note(self, request, pk=None):
        node = self.get_object()
        instruction = request.data.get('instruction')
        node_id = request.data.get('node_id')
        node_title = node.title
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
                chat_stream(messages=messages, on_stream=on_stream)
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
        return JsonResponse({"success": True, "message": "Stream started"})
    