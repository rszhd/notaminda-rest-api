from rest_framework import viewsets, permissions
from ..models import Node
from ..serializers import NodeSerializer

class PublicNodePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return not obj.mind_map.is_private

class PublicNodeViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [PublicNodePermission]
    queryset = Node.objects.filter(mind_map__is_private=False)
    serializer_class = NodeSerializer