from __future__ import annotations

import heapq
from typing import Dict, Set, Tuple

from src.graph import Graph, Hub, ZoneType


Edge = tuple[str, str]


class Pathfinder:
    def _edge_key(self, first: str, second: str) -> Edge:
        return tuple(sorted((first, second)))

    def _movement_cost(self, hub: Hub) -> float:
        if hub.zone_type == ZoneType.RESTRICTED:
            return 2.0
        if hub.zone_type == ZoneType.PRIORITY:
            return 0.99
        return 1.0

    def path_cost(self, path: list[Hub]) -> float:
        return sum(self._movement_cost(hub) for hub in path[1:])

    def find_path(
        self,
        graph: Graph,
        start: Hub,
        end: Hub,
        blocked_hubs: set[str] | None = None,
        blocked_connections: set[Tuple[str, str]] | None = None,
        hub_penalties: dict[str, float] | None = None,
        edge_penalties: dict[Edge, float] | None = None,
    ) -> list[Hub]:
        blocked_hubs = set() if blocked_hubs is None else set(blocked_hubs)
        blocked_connections = (
            set()
            if blocked_connections is None
            else {
                self._edge_key(first, second)
                for first, second in blocked_connections
            }
        )
        hub_penalties = {} if hub_penalties is None else hub_penalties
        edge_penalties = {} if edge_penalties is None else edge_penalties

        distances: Dict[str, float] = {
            name: float("inf") for name in graph.hubs
        }
        previous: Dict[str, str | None] = {
            name: None for name in graph.hubs
        }
        heap: list[tuple[float, str]] = [(0.0, start.name)]
        distances[start.name] = 0.0

        while heap:
            current_distance, current_name = heapq.heappop(heap)

            if current_distance != distances[current_name]:
                continue

            if current_name == end.name:
                break

            for neighbour in graph.adjacency[current_name]:
                if neighbour.zone_type == ZoneType.BLOCKED:
                    continue

                if (
                    neighbour.name in blocked_hubs
                    and neighbour.name != end.name
                ):
                    continue

                edge = self._edge_key(current_name, neighbour.name)

                if edge in blocked_connections:
                    continue

                new_distance = (
                    current_distance
                    + self._movement_cost(neighbour)
                    + hub_penalties.get(neighbour.name, 0.0)
                    + edge_penalties.get(edge, 0.0)
                )

                if new_distance < distances[neighbour.name]:
                    distances[neighbour.name] = new_distance
                    previous[neighbour.name] = current_name
                    heapq.heappush(
                        heap,
                        (new_distance, neighbour.name),
                    )

        if distances[end.name] == float("inf"):
            return []

        names: list[str] = []
        current: str | None = end.name

        while current is not None:
            names.append(current)
            current = previous[current]

        names.reverse()
        return [graph.hubs[name] for name in names]

    def find_paths(
        self,
        graph: Graph,
        start: Hub,
        end: Hub,
        max_paths: int = 16,
    ) -> list[list[Hub]]:
        first_path = self.find_path(graph, start, end)

        if not first_path:
            return []

        paths: list[list[Hub]] = [first_path]
        seen: Set[tuple[str, ...]] = {
            tuple(hub.name for hub in first_path)
        }
        queue: list[list[Hub]] = [first_path]

        while queue and len(paths) < max_paths:
            base_path = queue.pop(0)

            for index in range(len(base_path) - 1):
                alternative = self.find_path(
                    graph,
                    start,
                    end,
                    blocked_connections={
                        (
                            base_path[index].name,
                            base_path[index + 1].name,
                        )
                    },
                )

                if alternative:
                    key = tuple(hub.name for hub in alternative)

                    if key not in seen:
                        seen.add(key)
                        paths.append(alternative)
                        queue.append(alternative)

                        if len(paths) >= max_paths:
                            break

            if len(paths) >= max_paths:
                break

            for hub in base_path[1:-1]:
                alternative = self.find_path(
                    graph,
                    start,
                    end,
                    blocked_hubs={hub.name},
                )

                if not alternative:
                    continue

                key = tuple(item.name for item in alternative)

                if key in seen:
                    continue

                seen.add(key)
                paths.append(alternative)
                queue.append(alternative)

                if len(paths) >= max_paths:
                    break

        paths.sort(
            key=lambda path: (
                self.path_cost(path),
                len(path),
                tuple(hub.name for hub in path),
            )
        )
        return paths
