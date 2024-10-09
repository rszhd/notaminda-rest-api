import json
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework import serializers
from django.db import transaction
import uuid

from ..models import MindMap, Node
from ..serializers import UserSerializer
from ..utils.json_field_serializer import JSONFieldSerializer
from ..services import UpdateMindMapNodes


class NodeSerializer(serializers.ModelSerializer):
    flow_data = JSONFieldSerializer()

    class Meta:
        model = Node
        fields = ["id", "title", "parent", "flow_data", "created_at"]


class MindMapSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    project_data = serializers.SerializerMethodField()

    class Meta:
        model = MindMap
        fields = ["id", "title", "user", "created_at", "user", "project_data"]

    def get_project_data(self, obj):
        nodes = Node.objects.filter(mind_map=obj).values("id", "parent_id", "flow_data")
        root_node = Node.objects.get(mind_map=obj, parent_id__isnull=True)
        node_list = []
        relationship_list = []

        def get_parent_id(node, root_node):
            if node["parent_id"] == root_node.id:
                return "root"
            elif node["parent_id"] is not None:
                return str(node["parent_id"])
            else:
                return None

        for node in nodes:
            node_data = {
                "dbId": str(node["id"]),
                "id": (
                    "root" if str(node["id"]) == str(root_node.id) else str(node["id"])
                ),
                "parent_id": get_parent_id(node, root_node),
                "flow_data": (
                    json.loads(node["flow_data"]) if node["flow_data"] else None
                ),
            }
            node_list.append(node_data)

            relationship = {
                "id": str(uuid.uuid4()),
                "source": node_data["parent_id"],
                "target": node_data["id"],
            }
            relationship_list.append(relationship)

        return {"nodes": node_list, "relationships": relationship_list}


class MindMapListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MindMap
        fields = ["id", "title", "created_at"]


class MindMapUpdateNodeSerializer(serializers.ModelSerializer):
    id = serializers.CharField(required=False)
    parent = serializers.CharField(allow_null=True, required=False)

    class Meta:
        model = Node
        fields = ["id", "parent", "flow_data"]


class MindMapUpdateSerializer(serializers.ModelSerializer):
    nodes = MindMapUpdateNodeSerializer(many=True, required=False)

    class Meta:
        model = MindMap
        fields = ["nodes"]

    def update(self, instance, validated_data):
        if "nodes" in validated_data:
            UpdateMindMapNodes.run(instance, validated_data["nodes"])

        return instance

    def to_representation(self, instance):
        return {"message": "Mind map updated successfully"}


class MindMapCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MindMap
        fields = ["id", "title"]

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user

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
                flow_data=json.dumps(flow_data, cls=DjangoJSONEncoder),
            )

        return {"id": mind_map.id, "title": mind_map.title}
