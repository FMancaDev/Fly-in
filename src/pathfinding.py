from typing import Tuple
from src.graph import Graph, Hub, ZoneType


class Pathfinder:
    def find_path(
        self,
        graph: Graph,
        start: Hub,
        end: Hub,
        blocked_hubs: set[str] | None = None,
        blocked_connections: set[Tuple[str, str]] | None = None,
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
            current: Hub | None = None
            current_distance = float("inf")

            for name, distance in distances.items():
                if name not in visited and distance < current_distance:
                    current = graph.hubs[name]
                    current_distance = distance

            if current is None or current == end or current_distance == float("inf"):
                break

            visited.add(current.name)

            for neighbour in graph.adjacency[current.name]:
                if neighbour.name in visited:
                    continue

                if neighbour.name in blocked_hubs and neighbour != end:
                    continue

                if neighbour.zone_type == ZoneType.BLOCKED:
                    continue

                if (
                    (current.name, neighbour.name) in blocked_connections
                    or (neighbour.name, current.name) in blocked_connections
                ):
                    continue

                if neighbour.zone_type == ZoneType.RESTRICTED:
                    cost = 2.0
                elif neighbour.zone_type == ZoneType.PRIORITY:
                    cost = 0.5
                else:
                    cost = 1.0

                new_distance = distances[current.name] + cost

                if new_distance < distances[neighbour.name]:
                    distances[neighbour.name] = new_distance
                    previous[neighbour.name] = current

        if distances[end.name] == float("inf"):
            return []

        path: list[Hub] = []
        node: Hub | None = end
        while node is not None:
            path.append(node)
            node = previous[node.name]

        path.reverse()
        return path
