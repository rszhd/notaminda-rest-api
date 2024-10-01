from django.db import models
from .node import Node

class Note(models.Model):
    node = models.OneToOneField(Node, on_delete=models.CASCADE, related_name='note')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Note for {self.node.title}"
