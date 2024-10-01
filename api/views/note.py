from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from ..models import Note
from ..serializers import (
    NoteSerializer, NoteCreateSerializer, NoteUpdateSerializer
)

class NoteViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Note.objects.filter(node__mind_map__user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return NoteCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return NoteUpdateSerializer
        return NoteSerializer

    def perform_create(self, serializer):
        node = serializer.validated_data['node']
        if node.mind_map.user != self.request.user:
            return Response({"detail": "You can only create notes for your own mind maps."},
                            status=status.HTTP_403_FORBIDDEN)
        serializer.save()

    def perform_update(self, serializer):
        if serializer.instance.node.mind_map.user != self.request.user:
            return Response({"detail": "You can only update notes in your own mind maps."},
                            status=status.HTTP_403_FORBIDDEN)
        serializer.save()

        