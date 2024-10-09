from django.db import transaction
from ..models import Node


class UpdateMindMapNodes:
    @staticmethod
    @transaction.atomic
    def run(mind_map, nodes_data):
        existing_nodes = {
            str(node.id): node for node in mind_map.nodes.select_related("parent").all()
        }
        new_nodes = {}
        parent_updates = []
        nodes_to_update = []
        nodes_to_create = []

        for node_data in nodes_data:
            node_id = str(node_data.get("id"))
            parent_id = node_data.pop("parent", None)

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

        Node.objects.bulk_create(nodes_to_create)
        Node.objects.bulk_update(nodes_to_update, fields=["flow_data"])

        parent_dict = {str(node.id): node for node in mind_map.nodes.all()}
        for node, parent_id in parent_updates:
            parent_node = parent_dict.get(parent_id)
            if parent_node:
                node.parent = parent_node

        Node.objects.bulk_update(
            [node for node, _ in parent_updates], fields=["parent"]
        )
        Node.objects.filter(
            id__in=[node.id for node in existing_nodes.values()]
        ).delete()
