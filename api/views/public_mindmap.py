from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from ..models import MindMap
from ..serializers import MindMapSerializer

class PublicMindMapPermission(permissions.BasePermission):
    """
    Custom permission to allow access only to public mind maps.
    """
    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return not obj.is_private

class PublicMindMapViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [PublicMindMapPermission]
    queryset = MindMap.objects.filter(is_private=False)
    serializer_class = MindMapSerializer

    def get_queryset(self):
        return MindMap.objects.filter(is_private=False)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)