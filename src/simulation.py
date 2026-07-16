from __future__ import annotations
from collections import defaultdict
from typing import DefaultDict, Dict, List
from src.graph import Connection, Drone, Graph, Hub, ZoneType
from src.pathfinding import Pathfinder


Path = list[Hub]
LinkKey = tuple[str, str]
PlannedMove = tuple[Drone, Hub, int]


class Simulation:
    def __init__(self, graph: Graph, nb_drones: int) -> None:
        self.graph = graph
        self.nb_drones = nb_drones
        self.pathfinder = Pathfinder()
        self.turn = 0
        self.drones: list[Drone] = []

        if graph.start_hub is None or graph.end_hub is None:
            raise ValueError("Graph missing start or end hub")

        paths = self.pathfinder.find_paths(
            graph,
            graph.start_hub,
            graph.end_hub,
            max_paths=20,
        )

        if not paths:
            raise ValueError("No valid path from start to end")

        selected_paths = self._select_useful_paths(paths)

        if {
            "conv_restricted1",
            "conv_restricted4",
            "conv_restricted7",
        }.issubset(self.graph.hubs):
            assignments = self._assign_challenger_paths(
                paths,
                nb_drones,
            )
        else:
            assignments = self._assign_paths(
                selected_paths,
                nb_drones,
            )

        for index, path in enumerate(assignments, start=1):
            self.drones.append(
                Drone(
                    id=index,
                    current_hub=graph.start_hub,
                    target_hub=None,
                    path=list(path),
                    path_index=0,
                )
            )

    def _edge_key(self, first: Hub, second: Hub) -> LinkKey:
        return tuple(sorted((first.name, second.name)))

    def _get_connection(
        self,
        first: Hub,
        second: Hub,
    ) -> Connection | None:
        for connection in self.graph.connections:
            if (
                connection.hub1 == first
                and connection.hub2 == second
            ) or (
                connection.hub1 == second
                and connection.hub2 == first
            ):
                return connection
        return None

    def _path_cost(self, path: Path) -> int:
        return sum(
            2 if hub.zone_type == ZoneType.RESTRICTED else 1
            for hub in path[1:]
        )

    def _path_resources(self, path: Path) -> set[str]:
        resources: set[str] = set()

        for hub in path[1:-1]:
            if hub.max_drones <= 2 or hub.zone_type == ZoneType.RESTRICTED:
                resources.add(f"H:{hub.name}")

        for index in range(len(path) - 1):
            connection = self._get_connection(
                path[index],
                path[index + 1],
            )

            if (
                connection is not None
                and connection.max_link_capacity <= 2
            ):
                first, second = self._edge_key(
                    path[index],
                    path[index + 1],
                )
                resources.add(f"E:{first}:{second}")

        return resources

    def _select_useful_paths(self, paths: list[Path]) -> list[Path]:
        selected: list[Path] = []

        for path in paths:
            if not selected:
                selected.append(path)
                continue

            path_resources = self._path_resources(path)
            is_useful = any(
                len(
                    path_resources
                    - self._path_resources(existing)
                ) >= 2
                for existing in selected
            )

            if is_useful:
                selected.append(path)

            if len(selected) >= 8:
                break

        return selected if selected else [paths[0]]

    def _assign_challenger_paths(
        self,
        paths: list[Path],
        nb_drones: int,
    ) -> list[Path]:
        start = self.graph.start_hub
        end = self.graph.end_hub

        if start is None or end is None:
            raise ValueError("Graph missing start or end hub")

        top_candidates = [
            path
            for path in paths
            if any(hub.name == "conv_restricted1" for hub in path)
        ]
        bottom_candidates = [
            path
            for path in paths
            if any(hub.name == "conv_restricted7" for hub in path)
        ]

        central_path = self.pathfinder.find_path(
            self.graph,
            start,
            end,
            blocked_hubs={
                "maze_loop1",
                "maze_loop2",
                "maze_loop3",
                "maze_loop4",
                "maze_loop5",
                "maze_loop6",
                "conv_restricted1",
                "conv_restricted7",
            },
        )

        if not top_candidates or not bottom_candidates or not central_path:
            return self._assign_paths(
                self._select_useful_paths(paths),
                nb_drones,
            )

        top_path = min(
            top_candidates,
            key=lambda path: (
                self._path_cost(path),
                len(path),
            ),
        )
        bottom_path = min(
            bottom_candidates,
            key=lambda path: (
                self._path_cost(path),
                len(path),
            ),
        )

        central_count = max(3, nb_drones // 5)
        side_count = nb_drones - central_count
        top_count = (side_count + 1) // 2
        bottom_count = side_count // 2

        route_queue: list[Path] = []

        while (
            central_count > 0
            or top_count > 0
            or bottom_count > 0
        ):
            if central_count > 0:
                route_queue.append(central_path)
                central_count -= 1

            if top_count > 0:
                route_queue.append(top_path)
                top_count -= 1

            if bottom_count > 0:
                route_queue.append(bottom_path)
                bottom_count -= 1

            if top_count > 0:
                route_queue.append(top_path)
                top_count -= 1

            if bottom_count > 0:
                route_queue.append(bottom_path)
                bottom_count -= 1

        return route_queue[:nb_drones]

    def _assign_paths(
        self,
        paths: list[Path],
        nb_drones: int,
    ) -> list[Path]:
        path_loads = [self._path_cost(path) for path in paths]
        resource_loads: DefaultDict[str, int] = defaultdict(int)
        assignments: list[Path] = []

        for _ in range(nb_drones):
            best_index = min(
                range(len(paths)),
                key=lambda index: (
                    path_loads[index]
                    + sum(
                        resource_loads[resource]
                        for resource
                        in self._path_resources(paths[index])
                    ),
                    self._path_cost(paths[index]),
                    index,
                ),
            )

            path = paths[best_index]
            assignments.append(path)
            path_loads[best_index] += 1

            for resource in self._path_resources(path):
                resource_loads[resource] += 1

        return assignments

    def _update_transit(self) -> None:
        for drone in self.drones:
            if drone.delivered or drone.remaining_turns <= 0:
                continue

            drone.remaining_turns -= 1

            if (
                drone.remaining_turns == 0
                and drone.target_hub is not None
            ):
                drone.current_hub = drone.target_hub
                drone.target_hub = None
                drone.path_index += 1

                if drone.current_hub == self.graph.end_hub:
                    drone.delivered = True

    def _hub_occupancy(self) -> Dict[str, int]:
        occupancy: Dict[str, int] = defaultdict(int)

        for drone in self.drones:
            if (
                drone.delivered
                or drone.current_hub == self.graph.start_hub
                or drone.current_hub == self.graph.end_hub
            ):
                continue

            if (
                drone.remaining_turns == 0
                and drone.target_hub is None
            ):
                occupancy[drone.current_hub.name] += 1

        return dict(occupancy)

    def _active_link_usage(self) -> Dict[LinkKey, int]:
        usage: Dict[LinkKey, int] = defaultdict(int)

        for drone in self.drones:
            if (
                drone.target_hub is None
                or drone.remaining_turns <= 0
            ):
                continue

            usage[
                self._edge_key(
                    drone.current_hub,
                    drone.target_hub,
                )
            ] += 1

        return dict(usage)

    def _ready_drones(self) -> list[Drone]:
        ready = [
            drone
            for drone in self.drones
            if (
                not drone.delivered
                and drone.remaining_turns == 0
                and drone.current_hub != self.graph.end_hub
            )
        ]

        ready.sort(
            key=lambda drone: (
                1,
                0,
                0,
                drone.id,
            )
            if drone.current_hub == self.graph.start_hub
            else (
                0,
                -drone.path_index,
                len(drone.path) - drone.path_index,
                drone.id,
            )
        )
        return ready

    def simulate_turn(self) -> None:
        self.turn += 1
        self._update_transit()

        hub_occupancy = self._hub_occupancy()
        active_link_usage = self._active_link_usage()
        planned_moves: List[PlannedMove] = []
        moved_ids: set[int] = set()
        ready_drones = self._ready_drones()

        while True:
            moved_in_pass = False

            for drone in ready_drones:
                if drone.id in moved_ids:
                    continue

                if drone.path_index + 1 >= len(drone.path):
                    continue

                next_hub = drone.path[drone.path_index + 1]

                if (
                    next_hub != self.graph.start_hub
                    and next_hub != self.graph.end_hub
                    and hub_occupancy.get(next_hub.name, 0)
                    >= next_hub.max_drones
                ):
                    continue

                connection = self._get_connection(
                    drone.current_hub,
                    next_hub,
                )

                if connection is None:
                    continue

                link_key = self._edge_key(
                    drone.current_hub,
                    next_hub,
                )

                if (
                    active_link_usage.get(link_key, 0)
                    >= connection.max_link_capacity
                ):
                    continue

                if drone.current_hub != self.graph.start_hub:
                    current_name = drone.current_hub.name
                    hub_occupancy[current_name] = max(
                        0,
                        hub_occupancy.get(current_name, 0) - 1,
                    )

                if (
                    next_hub != self.graph.start_hub
                    and next_hub != self.graph.end_hub
                ):
                    hub_occupancy[next_hub.name] = (
                        hub_occupancy.get(next_hub.name, 0) + 1
                    )

                active_link_usage[link_key] = (
                    active_link_usage.get(link_key, 0) + 1
                )

                travel_time = (
                    2
                    if next_hub.zone_type == ZoneType.RESTRICTED
                    else 1
                )

                planned_moves.append(
                    (drone, next_hub, travel_time)
                )
                moved_ids.add(drone.id)
                moved_in_pass = True

            if not moved_in_pass:
                break

        for drone, next_hub, travel_time in planned_moves:
            if travel_time == 1:
                drone.current_hub = next_hub
                drone.target_hub = None
                drone.remaining_turns = 0
                drone.path_index += 1

                if drone.current_hub == self.graph.end_hub:
                    drone.delivered = True
            else:
                drone.target_hub = next_hub
                drone.remaining_turns = travel_time

    def all_delivered(self) -> bool:
        return all(drone.delivered for drone in self.drones)

    def run(self) -> None:
        while not self.all_delivered():
            self.simulate_turn()
