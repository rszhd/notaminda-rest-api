from rest_framework import viewsets, permissions
import uuid
from rest_framework.response import Response
from ..models import MindMap, Node
from ..serializers import (
    MindMapSerializer, MindMapCreateSerializer, MindMapUpdateSerializer,
    MindMapListSerializer
)

class IsMindMapOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class MindMapViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsMindMapOwner]

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

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        relationships = Node.get_relationships(instance.id)
        relationship_list = [
            {
                "id": str(uuid.uuid4()),
                "source": str(rel['parent_id']),
                "target": str(rel['id'])
            }
            for rel in relationships
        ]

        data['relationships'] = relationship_list
        return Response(data)