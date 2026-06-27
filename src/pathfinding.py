from src.graph import Graph, Hub, ZoneType


class Pathfinder:
    def find_path(self, graph: Graph, start: Hub, end: Hub) -> list[Hub]:

        distances: dict[str, float] = {
            hub_name: float("inf") for hub_name in graph.hubs}
        previous: dict[str, Hub | None] = {
            hub_name: None for hub_name in graph.hubs}

        visited: set[str] = set()
        distances[start.name] = 0

        while len(visited) < len(graph.hubs):
            current: Hub | None = None
            current_distance = float("inf")

            for hub_name, distance in distances.items():
                if hub_name not in visited and distance < current_distance:
                    current = graph.hubs[hub_name]
                    current_distance = distance

            if current is None:
                break
            if current == end:
                break

            visited.add(current.name)

            for neighbor in graph.adjacency[current.name]:
                if neighbor.name in visited:
                    continue

                if neighbor.zone_type == ZoneType.NORMAL:
                    move_cost = 1
                elif neighbor.zone_type == ZoneType.RESTRICTED:
                    move_cost = 2
                elif neighbor.zone_type == ZoneType.PRIORITY:
                    move_cost = 1
                elif neighbor.zone_type == ZoneType.BLOCKED:
                    continue

                new_distance = (distances[current.name] + move_cost)

                if new_distance < distances[neighbor.name]:
                    distances[neighbor.name] = new_distance
                    previous[neighbor.name] = current

        if distances[end.name] == float("inf"):
            return []

        path: list[Hub] = []
        current: Hub | None = end

        while current is not None:
            path.append(current)
            current = previous[current.name]
        path.reverse()
        return path
