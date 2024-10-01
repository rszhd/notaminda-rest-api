from rest_framework import viewsets, permissions
from ..models import MindMap
from ..serializers import (
    MindMapSerializer, MindMapCreateSerializer, MindMapUpdateSerializer,
    MindMapListSerializer
)

class MindMapViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MindMap.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return MindMapListSerializer
        elif self.action == 'create':
            return MindMapCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MindMapUpdateSerializer
        return MindMapSerializer

    def perform_create(self, serializer):
        serializer.save()
