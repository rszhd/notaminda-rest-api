from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.http import JsonResponse
import os
import asyncio

from ..models import Node
from ..services import NodeChildrenGenerator, NodeNoteGenerator
from ..serializers import (
    NodeSerializer,
    NodeUpdateSerializer,
    GeneratedChildrenSerializer,
    AutoGenerateChildrenSerializer,
    AutoGenerateNoteSerializer,
)

OPENAI_KEY = os.environ.get("OPENAI_KEY")
AI_MODEL = os.environ.get("AI_MODEL")


class IsNodeOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.mind_map.user == request.user


class NodeViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsNodeOwner]
    queryset = Node.objects.all()

    def get_queryset(self):
        return Node.objects.filter(mind_map__user=self.request.user)

    def get_serializer_class(self):
        if self.action == "update":
            return NodeUpdateSerializer
        return NodeSerializer

    @action(detail=True, methods=["post"])
    def auto_generate_note(self, request, pk=None):
        node = self.get_object()

        serializer = AutoGenerateNoteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        instruction = validated_data.get("instruction")
        ai_key = validated_data.get("ai_key")
        ai_model = validated_data.get("ai_model")
        result = NodeNoteGenerator.generate(
            node,
            instruction,
            ai_key or OPENAI_KEY,
            ai_model if ai_key and ai_model else AI_MODEL,
        )
        return JsonResponse(result)

    @action(detail=True, methods=["post"])
    def auto_generate_children(self, request, pk=None):
        node = self.get_object()

        serializer = AutoGenerateChildrenSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        positions = validated_data.get("nodes_position")
        ai_key = validated_data["ai_key"]
        ai_model = validated_data["ai_model"]

        children = asyncio.run(
            NodeChildrenGenerator.generate(
                ai_model if ai_key and ai_model else AI_MODEL,
                ai_key or OPENAI_KEY,
                node,
                positions,
            )
        )

        response_serializer = GeneratedChildrenSerializer({"children": children})
        return Response(response_serializer.data)
