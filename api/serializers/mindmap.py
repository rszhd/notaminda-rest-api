from rest_framework import serializers
from ..models import MindMap, Node
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.db import transaction

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

class MindMapNodeSerializer(serializers.ModelSerializer):
    flow_data = JSONField()

    class Meta:
        model = Node
        fields = ['id', 'title', 'parent', 'flow_data', 'created_at']
        read_only_fields = ['parent']

class MindMapSerializer(BaseMindMapSerializer):
    nodes = MindMapNodeSerializer(many=True, read_only=True)
    flow_data = JSONField()

    class Meta(BaseMindMapSerializer.Meta):
        fields = BaseMindMapSerializer.Meta.fields + ['nodes']

class MindMapUpdateNodeSerializer(serializers.ModelSerializer):
    id = serializers.CharField(required=False) 
    parent = serializers.CharField(allow_null=True, required=False)
    
    class Meta:
        model = Node
        fields = ['id', 'title', 'parent', 'flow_data']

class MindMapUpdateSerializer(BaseMindMapSerializer):
    nodes = MindMapUpdateNodeSerializer(many=True, required=False)

    class Meta(BaseMindMapSerializer.Meta):
        fields = ['nodes', 'flow_data']

    def update(self, instance, validated_data):
        user = self.context['request'].user
        if instance.user != user:
            raise serializers.ValidationError("You can only update your own mind maps.")

        if 'nodes' in validated_data:
            self.update_nodes(instance, validated_data['nodes'])

        if 'flow_data' in validated_data:
            instance.flow_data = validated_data['flow_data']
            instance.save()

        return instance

    @transaction.atomic
    def update_nodes(self, mind_map, nodes_data):
        existing_nodes = {str(node.id): node for node in mind_map.nodes.select_related('parent').all()}
        new_nodes = {}
        parent_updates = []
        nodes_to_update = []
        nodes_to_create = []

        for node_data in nodes_data:
            node_id = str(node_data.get('id'))
            parent_id = node_data.pop('parent', None)

            if node_id in existing_nodes:
                node = existing_nodes[node_id]
                for attr, value in node_data.items():
                    setattr(node, attr, value)
                nodes_to_update.append(node)
                del existing_nodes[node_id]
            else:
                node = Node(mind_map=mind_map, **node_data)
                new_nodes[node_id] = node
                nodes_to_create.append(node)

            if parent_id:
                parent_updates.append((node, parent_id))

        # Bulk create new nodes
        Node.objects.bulk_create(nodes_to_create)
        
        # Bulk update existing nodes
        Node.objects.bulk_update(nodes_to_update, fields=['title'])

        # Update parent relationships
        parent_dict = {str(node.id): node for node in mind_map.nodes.all()}
        for node, parent_id in parent_updates:
            parent_node = parent_dict.get(parent_id)
            if parent_node:
                node.parent = parent_node

        # Bulk update parent relationships
        Node.objects.bulk_update([node for node, _ in parent_updates], fields=['parent'])

        # Delete nodes that are no longer present in the input data
        Node.objects.filter(id__in=[node.id for node in existing_nodes.values()]).delete()

    def to_representation(self, instance):
        return {"message": "Mind map updated successfully"}
    
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
