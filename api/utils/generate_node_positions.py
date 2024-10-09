import math


def generate_node_positions(parent_node, new_nodes_count, existing_nodes):
    new_nodes = []
    radius = 150
    angle_step = (2 * math.pi) / new_nodes_count

    for i in range(new_nodes_count):
        angle = i * angle_step
        x = parent_node["position"]["x"] + radius * math.cos(angle)
        y = parent_node["position"]["y"] + radius * math.sin(angle)

        new_nodes.append({"position": {"x": x, "y": y}, "height": 32, "width": 100})

    all_nodes = existing_nodes + new_nodes
    iterations = 0
    max_iterations = 100

    while iterations < max_iterations:
        has_collision = False

        for i in range(len(new_nodes)):
            for j in range(len(all_nodes)):
                if new_nodes[i].get("id") != all_nodes[j].get(
                    "id"
                ) and detect_collision(new_nodes[i], all_nodes[j]):
                    resolve_collision(new_nodes[i], all_nodes[j])
                    has_collision = True

        if not has_collision:
            break
        iterations += 1

    return new_nodes


def detect_collision(node1, node2):
    return (
        node1["position"]["x"] < node2["position"]["x"] + node2["width"]
        and node1["position"]["x"] + node1["width"] > node2["position"]["x"]
        and node1["position"]["y"] < node2["position"]["y"] + node2["height"]
        and node1["position"]["y"] + node1["height"] > node2["position"]["y"]
    )


def resolve_collision(node1, node2):
    overlap_x = min(
        node1["position"]["x"] + node1["width"] - node2["position"]["x"],
        node2["position"]["x"] + node2["width"] - node1["position"]["x"],
    )
    overlap_y = min(
        node1["position"]["y"] + node1["height"] - node2["position"]["y"],
        node2["position"]["y"] + node2["height"] - node1["position"]["y"],
    )

    if overlap_x < overlap_y:
        if node1["position"]["x"] < node2["position"]["x"]:
            node1["position"]["x"] -= overlap_x / 2
            node2["position"]["x"] += overlap_x / 2
        else:
            node1["position"]["x"] += overlap_x / 2
            node2["position"]["x"] -= overlap_x / 2
    else:
        if node1["position"]["y"] < node2["position"]["y"]:
            node1["position"]["y"] -= overlap_y / 2
            node2["position"]["y"] += overlap_y / 2
        else:
            node1["position"]["y"] += overlap_y / 2
            node2["position"]["y"] -= overlap_y / 2
