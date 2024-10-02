from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models import Node
from ..serializers import (
    NodeSerializer
)
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny

class PublicNodeViewSet(viewsets.ModelViewSet):
    serializer_class = NodeSerializer

    def get_permissions(self):
        if self.action == 'retrieve':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Node.objects.filter(mind_map__user=user)
        return Node.objects.filter(mind_map__is_private=False)

    def retrieve(self, request, *args, **kwargs):
        node = self.get_object()
        mind_map = node.mind_map

        if mind_map.is_private and (not request.user.is_authenticated or mind_map.user != request.user):
            return Response({"detail": "You do not have permission to access this node."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(node)
        return Response(serializer.data)

    def get_object(self):
        queryset = Node.objects.all()
        obj = get_object_or_404(queryset, pk=self.kwargs['pk'])
        self.check_object_permissions(self.request, obj)
        return obj

    def get_serializer_class(self):
        if self.action == 'create':
            return
        elif self.action in ['update', 'partial_update']:
            return
        return NodeSerializer
    