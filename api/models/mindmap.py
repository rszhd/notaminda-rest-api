from django.db import models
from django.contrib.auth.models import User
import uuid

def generate_unique_id():
    return uuid.uuid4().hex[:20]

class MindMap(models.Model):
    id = models.CharField(max_length=20, primary_key=True, default=generate_unique_id, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    title = models.CharField(max_length=200)
    is_private = models.BooleanField(default=True)
    flow_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return self.title