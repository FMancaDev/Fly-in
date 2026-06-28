from src.graph import Graph, Hub, ZoneType
from typing import Tuple


class Pathfinder:
    def find_path(
        self,
        graph: Graph,
        start: Hub,
        end: Hub,
        blocked_hubs: set[str] | None = None,
        blocked_connections: set[Tuple[str, str]] | None = None
    ) -> list[Hub]:

        blocked_hubs = blocked_hubs or set()
        blocked_connections = blocked_connections or set()

        distances: dict[str, float] = {
            name: float("inf") for name in graph.hubs
        }
        previous: dict[str, Hub | None] = {
            name: None for name in graph.hubs
        }

        visited: set[str] = set()
        distances[start.name] = 0

        while True:
            current = None
            current_distance = float("inf")

            for name, dist in distances.items():
                if name not in visited and dist < current_distance:
                    current = graph.hubs[name]
                    current_distance = dist

            if current is None:
                break

            if current.name == end.name:
                break

            visited.add(current.name)

            for neighbor in graph.adjacency[current.name]:

                if neighbor.name in visited:
                    continue

                if neighbor.name in blocked_hubs:
                    continue

                if neighbor.zone_type == ZoneType.BLOCKED:
                    continue

                if (
                    (current.name, neighbor.name) in blocked_connections
                    or (neighbor.name, current.name) in blocked_connections
                ):
                    continue

                if neighbor.zone_type == ZoneType.RESTRICTED:
                    cost = 2
                else:
                    cost = 1

                new_dist = distances[current.name] + cost

                if new_dist < distances[neighbor.name]:
                    distances[neighbor.name] = new_dist
                    previous[neighbor.name] = current

        if distances[end.name] == float("inf"):
            return []

        path: list[Hub] = []
        node: Hub | None = end

        while node is not None:
            path.append(node)
            node = previous[node.name]

        return path[::-1]
