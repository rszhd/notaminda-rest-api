import json
from rest_framework import serializers
from django.core.exceptions import ValidationError
from ..models import Node

class JSONField(serializers.Field):
    def to_representation(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return value

    def to_internal_value(self, data):
        if data is None:
            return None
        if isinstance(data, str):
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON data")
        return json.dumps(data)

class NodeSerializer(serializers.ModelSerializer):
    flow_data = JSONField()

    class Meta:
        model = Node
        fields = ['id', 'title', 'parent', 'flow_data', 'note', 'created_at']
        read_only_fields = ['parent']

class NodeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = ['title', 'parent', 'mind_map']

    def validate(self, data):
        user = self.context['request'].user
        if data['mind_map'].user != user:
            raise ValidationError("You can only create nodes for your own mind maps.")
        return data

    def create(self, validated_data):
        return Node.objects.create(**validated_data)

class NodeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = ['title', 'note']

    def validate(self, data):
        user = self.context['request'].user
        if self.instance.mind_map.user != user:
            raise ValidationError("You can only update nodes in your own mind maps.")
        return data

class GenerateChildrenNodeSerializer(serializers.Serializer):
    x = serializers.FloatField()
    y = serializers.FloatField()
    absolute_x = serializers.FloatField()
    absolute_y = serializers.FloatField()
    title = serializers.CharField(max_length=255)
    id = serializers.CharField(max_length=20)

class GeneratedChildrenSerializer(serializers.Serializer):
    children = GenerateChildrenNodeSerializer(many=True, read_only=True)