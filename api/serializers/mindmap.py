import json
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework import serializers
from django.db import transaction

from ..models import MindMap, Node
from ..serializers import UserSerializer
from ..utils.json_field_serializer import JSONFieldSerializer
from ..services import UpdateMindMapNodes

class NodeSerializer(serializers.ModelSerializer):
    flow_data = JSONFieldSerializer()

    class Meta:
        model = Node
        fields = ['id', 'title', 'parent', 'flow_data', 'created_at']

class MindMapSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    nodes = NodeSerializer(many=True)

    class Meta:
        model = MindMap
        fields = ['id', 'title', 'user', 'created_at', 'nodes', 'user']

class MindMapListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MindMap
        fields = ['id', 'title', 'created_at']

class MindMapUpdateNodeSerializer(serializers.ModelSerializer):
    id = serializers.CharField(required=False) 
    parent = serializers.CharField(allow_null=True, required=False)
    
    class Meta:
        model = Node
        fields = ['id', 'title', 'parent', 'flow_data']

class MindMapUpdateSerializer(serializers.ModelSerializer):
    nodes = MindMapUpdateNodeSerializer(many=True, required=False)

    class Meta:
        model = MindMap
        fields = ['nodes']

    def update(self, instance, validated_data):
        if 'nodes' in validated_data:
            UpdateMindMapNodes.run(instance, validated_data['nodes'])

        return instance

    def to_representation(self, instance):
        return {"message": "Mind map updated successfully"}

class MindMapCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MindMap
        fields = ['id', 'title']

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        
        with transaction.atomic():
            mind_map = MindMap.objects.create(user=user, **validated_data)
            
            flow_data = {
                "id": "root",
                "type": "mindmap",
                "data": {"label": mind_map.title},
                "position": {"x": 0, "y": 0},
                "dragHandle": ".dragHandle",
            }
            
            Node.objects.create(
                title=mind_map.title,
                mind_map=mind_map,
                parent=None,
                flow_data=json.dumps(flow_data, cls=DjangoJSONEncoder)
            )
        
        return {
            'id': mind_map.id,
            'title': mind_map.title
        }
    