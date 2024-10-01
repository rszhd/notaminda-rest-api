from rest_framework import serializers
from ..models import MindMap, Node, Note
from django.contrib.auth.models import User
from .note import NoteSerializer

import json
from rest_framework import serializers

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
                raise serializers.ValidationError("Invalid JSON data")
        return json.dumps(data)

class NodeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    note = NoteSerializer(read_only=True)
    flow_data = JSONField()

    class Meta:
        model = Node
        fields = ['id', 'title', 'parent', 'mind_map', 'flow_data', 'created_at', 'children', 'note']

    def get_children(self, obj):
        return NodeSerializer(obj.children.all(), many=True).data

class NodeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = ['title', 'parent', 'mind_map']

    def create(self, validated_data):
        user = self.context['request'].user
        if validated_data['mind_map'].user != user:
            raise serializers.ValidationError("You can only create nodes for your own mind maps.")
        return Node.objects.create(**validated_data)

class NodeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = ['title', 'parent']

    def update(self, instance, validated_data):
        user = self.context['request'].user
        if instance.mind_map.user != user:
            raise serializers.ValidationError("You can only update nodes in your own mind maps.")
        return super().update(instance, validated_data)
