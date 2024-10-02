from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from ..models import MindMap
from ..serializers import (
    MindMapSerializer
)
class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow authenticated users full access,
    but allow read-only access to public mind maps for unauthenticated users.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return not obj.is_private or obj.user == request.user
        return obj.user == request.user

class PublicMindMapViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = MindMap.objects.all()

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return MindMap.objects.filter(user=self.request.user) | MindMap.objects.filter(is_private=False)
        return MindMap.objects.filter(is_private=False)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return
        elif self.action == 'create':
            return
        elif self.action in ['update', 'partial_update']:
            return
        return MindMapSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)