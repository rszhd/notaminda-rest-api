from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.http import JsonResponse

from ..models import Node
from ..services import AutoGenerateNodeChildren, AutoGenerateNodeNote
from ..serializers import (
    NodeSerializer, NodeUpdateSerializer,
    GeneratedChildrenSerializer, AutoGenerateChildrenSerializer,
    AutoGenerateNoteSerializer
)

class IsNodeOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.mind_map.user == request.user

class NodeViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsNodeOwner]
    queryset = Node.objects.all()

    def get_queryset(self):
        return Node.objects.filter(mind_map__user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'update':
            return NodeUpdateSerializer
        return NodeSerializer
    
    @action(detail=True, methods=['post'])
    def auto_generate_note(self, request, pk=None):
        node = self.get_object()
        
        serializer = AutoGenerateNoteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        instruction = validated_data.get('instruction')
        result = AutoGenerateNodeNote.run(node, instruction)
        return JsonResponse(result)
    
    @action(detail=True, methods=['post'])
    def auto_generate_children(self, request, pk=None):
        node = self.get_object()

        serializer = AutoGenerateChildrenSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        num_children = validated_data.get('num_children', 3)
        positions = validated_data.get('nodes_position')
        ai_key = validated_data['ai_key']
        ai_model = validated_data['ai_model']
        
        children = AutoGenerateNodeChildren.run(node, num_children, positions, ai_key, ai_model)
        
        response_serializer = GeneratedChildrenSerializer({'children': children})
        return Response(response_serializer.data)
