from rest_framework import serializers
from ..models import MindMap, Node
from .user import UserSerializer
from .node import NodeSerializer
from ..models.note import Note
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

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

class BaseMindMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = MindMap
        fields = ['id', 'title', 'flow_data', 'created_at']

class MindMapSerializer(BaseMindMapSerializer):
    user = UserSerializer(read_only=True)
    nodes = NodeSerializer(many=True, read_only=True)
    flow_data = JSONField()

    class Meta(BaseMindMapSerializer.Meta):
        fields = BaseMindMapSerializer.Meta.fields + ['user', 'nodes']

class NodeUpdateSerializer(serializers.ModelSerializer):
    id = serializers.CharField(required=False) 
    parent = serializers.CharField(allow_null=True, required=False)
    
    class Meta:
        model = Node
        fields = ['id', 'title', 'parent', 'flow_data']

class MindMapUpdateSerializer(BaseMindMapSerializer):
    title = serializers.CharField(required=True)
    nodes = NodeUpdateSerializer(many=True, required=False)

    class Meta(BaseMindMapSerializer.Meta):
        fields = ['title', 'nodes', 'flow_data']

    # def validate_nodes(self, value):
    #     mind_map = self.instance
    #     for node_data in value:
    #         if 'parent' in node_data and node_data['parent'] is not None:
    #             parent_id = node_data['parent'].id if isinstance(node_data['parent'], Node) else node_data['parent']
    #             try:
    #                 parent = Node.objects.get(id=parent_id, mind_map=mind_map)
    #                 node_data['parent'] = parent.id
    #             except Node.DoesNotExist:
    #                 raise serializers.ValidationError(f"Parent node with id {parent_id} does not exist in this mind map.")
    #     return value

    def update(self, instance, validated_data):
        user = self.context['request'].user
        if instance.user != user:
            raise serializers.ValidationError("You can only update your own mind maps.")

        if 'title' in validated_data:
            instance.title = validated_data['title']
            instance.save()

        if 'nodes' in validated_data:
            # print(validated_data['nodes'])
            self.update_nodes(instance, validated_data['nodes'])

        if 'flow_data' in validated_data:
            instance.flow_data = validated_data['flow_data']
            instance.save()

        return instance

    @transaction.atomic
    def update_nodes(self, mind_map, nodes_data):
        existing_nodes = {str(node.id): node for node in mind_map.nodes.all()}
        new_nodes = {}
        parent_updates = []

        # First pass: Create or update nodes without setting parent relationships
        for node_data in nodes_data:
            node_id = str(node_data.get('id'))
            parent_id = node_data.pop('parent', None)

            if node_id in existing_nodes:
                node = existing_nodes[node_id]
                for attr, value in node_data.items():
                    setattr(node, attr, value)
                node.save()
                del existing_nodes[node_id]
            else:
                node = Node.objects.create(mind_map=mind_map, **node_data)
                new_nodes[node_id] = node
                Note.objects.create(node=node, content="")

            if parent_id:
                parent_updates.append((node, parent_id))

        # Second pass: Update parent relationships
        for node, parent_id in parent_updates:
            try:
                parent_node = mind_map.nodes.get(id=parent_id)
                node.parent = parent_node
                node.save()
            except ObjectDoesNotExist:
                pass

        # Delete nodes that are no longer present in the input data
        for node in existing_nodes.values():
            node.delete()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['nodes'] = NodeSerializer(instance.nodes.all(), many=True).data
        return representation
    
class MindMapListSerializer(serializers.ModelSerializer):
    class Meta(BaseMindMapSerializer.Meta):
        fields = ['id', 'title', 'created_at']

class MindMapCreateSerializer(BaseMindMapSerializer):
    class Meta(BaseMindMapSerializer.Meta):
        fields = ['id', 'title']

    def create(self, validated_data):
        user = self.context['request'].user
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

    def to_representation(self, instance):
        if isinstance(instance, dict):
            return instance
        return super().to_representation(instance)
