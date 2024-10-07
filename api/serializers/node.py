from rest_framework import serializers
from ..models import Node
from ..utils.json_field_serializer import JSONFieldSerializer

class NodeSerializer(serializers.ModelSerializer):
    flow_data = JSONFieldSerializer()

    class Meta:
        model = Node
        fields = ['id', 'title', 'parent', 'flow_data', 'note', 'created_at']
        read_only_fields = ['parent']

class NodeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = ['title', 'parent', 'mind_map']

class NodeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = ['title', 'note']

class GenerateChildrenNodeSerializer(serializers.Serializer):
    x = serializers.FloatField()
    y = serializers.FloatField()
    absolute_x = serializers.FloatField()
    absolute_y = serializers.FloatField()
    title = serializers.CharField(max_length=255)
    id = serializers.CharField(max_length=20)

class GeneratedChildrenSerializer(serializers.Serializer):
    children = GenerateChildrenNodeSerializer(many=True, read_only=True)

class AutoGenerateChildrenSerializer(serializers.Serializer):
    num_children = serializers.IntegerField(default=3, min_value=1, max_value=10)
    nodes_position = serializers.ListField()
    ai_key = serializers.CharField(max_length=255, required=False, allow_null=True)
    ai_model = serializers.CharField(max_length=100, required=False, allow_null=True)

    def validate_num_children(self, value):
        if value < 1:
            raise serializers.ValidationError("Number of children must be more than 1.")
        return value

class AutoGenerateNoteSerializer(serializers.Serializer):
    instruction = serializers.CharField(required=False, max_length=500)
