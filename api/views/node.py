import asyncio
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
