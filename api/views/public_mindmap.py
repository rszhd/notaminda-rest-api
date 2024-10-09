from rest_framework import viewsets, permissions
from ..models import MindMap
from ..serializers import MindMapSerializer


class PublicMindMapPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return not obj.is_private


class PublicMindMapViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [PublicMindMapPermission]
    queryset = MindMap.objects.filter(is_private=False)
    serializer_class = MindMapSerializer
