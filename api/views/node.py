from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from ..models import Node
from ..serializers import (
    NodeSerializer, NodeCreateSerializer, NodeUpdateSerializer,
)

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
