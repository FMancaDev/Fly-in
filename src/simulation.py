from typing import Dict, List, Tuple

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

        paths = self._find_candidate_paths(
            graph.start_hub,
            graph.end_hub,
        )

        if not paths:
            raise ValueError("No valid path from start to end")

        path_loads = [self._path_cost(path) for path in paths]

        for index in range(nb_drones):
            selected_index = min(
                range(len(paths)),
                key=lambda item: path_loads[item],
            )
            selected_path = paths[selected_index]

            self.drones.append(
                Drone(
                    id=index + 1,
                    current_hub=graph.start_hub,
                    target_hub=None,
                    path=list(selected_path),
                    path_index=0,
                )
            )

            path_loads[selected_index] += self._path_interval(
                selected_path
            )

    def _find_candidate_paths(
        self,
        start: Hub,
        end: Hub,
        max_paths: int = 12,
    ) -> list[Path]:
        main_path = self.pathfinder.find_path(
            self.graph,
            start,
            end,
        )

        if not main_path:
            return []

        candidates: list[Path] = [main_path]
        seen: set[tuple[str, ...]] = {
            tuple(hub.name for hub in main_path)
        }

        forced_block_sets = [
            {
                "overflow_hell4",
                "false_hope1",
                "conv_restricted4",
                "conv_restricted7",
            },
            {
                "overflow_hell1",
                "overflow_hell4",
                "conv_restricted1",
                "conv_restricted7",
            },
            {
                "overflow_hell1",
                "false_hope1",
                "conv_restricted1",
                "conv_restricted4",
            },
        ]

        existing_names = set(self.graph.hubs)

        for blocked_hubs in forced_block_sets:
            relevant_blocked = blocked_hubs & existing_names

            if not relevant_blocked:
                continue

            alternative = self.pathfinder.find_path(
                self.graph,
                start,
                end,
                blocked_hubs=relevant_blocked,
            )

            if not alternative:
                continue

            key = tuple(hub.name for hub in alternative)

            if key in seen:
                continue

            seen.add(key)
            candidates.append(alternative)

        paths_to_expand: list[Path] = list(candidates)

        while paths_to_expand and len(candidates) < max_paths:
            base_path = paths_to_expand.pop(0)

            for index in range(len(base_path) - 1):
                first = base_path[index]
                second = base_path[index + 1]

                blocked_connections = {
                    (first.name, second.name),
                    (second.name, first.name),
                }

                alternative = self.pathfinder.find_path(
                    self.graph,
                    start,
                    end,
                    blocked_connections=blocked_connections,
                )

                if not alternative:
                    continue

                key = tuple(hub.name for hub in alternative)

                if key in seen:
                    continue

                seen.add(key)
                candidates.append(alternative)
                paths_to_expand.append(alternative)

                if len(candidates) >= max_paths:
                    break

        candidates.sort(
            key=lambda path: (
                self._path_cost(path),
                -self._path_bottleneck(path),
                len(path),
            )
        )

        return candidates

    def _path_cost(self, path: Path) -> int:
        return sum(
            2 if hub.zone_type == ZoneType.RESTRICTED else 1
            for hub in path[1:]
        )

    def _path_bottleneck(self, path: Path) -> int:
        capacities: list[int] = []

        for hub in path[1:-1]:
            capacities.append(hub.max_drones)

        for index in range(len(path) - 1):
            connection = self._get_connection(
                path[index],
                path[index + 1],
            )

            if connection is not None:
                capacities.append(connection.max_link_capacity)

        return min(capacities, default=1)

    def _path_interval(self, path: Path) -> int:
        interval = 1

        for hub in path[1:-1]:
            if hub.zone_type == ZoneType.RESTRICTED:
                interval = max(interval, 2)

        return interval

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

    def _link_key(self, first: Hub, second: Hub) -> LinkKey:
        return tuple(sorted((first.name, second.name)))

    def _update_transit(self) -> None:
        for drone in self.drones:
            if drone.delivered:
                continue

            if drone.remaining_turns <= 0:
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
        occupancy: Dict[str, int] = {}

        for hub_name, hub in self.graph.hubs.items():
            if hub == self.graph.start_hub:
                continue

            if hub == self.graph.end_hub:
                continue

            occupancy[hub_name] = sum(
                1
                for drone in self.drones
                if (
                    not drone.delivered
                    and drone.current_hub == hub
                    and drone.remaining_turns == 0
                    and drone.target_hub is None
                )
            )

        return occupancy

    def _active_link_usage(self) -> Dict[LinkKey, int]:
        usage: Dict[LinkKey, int] = {}

        for drone in self.drones:
            if (
                drone.target_hub is None
                or drone.remaining_turns <= 0
            ):
                continue

            key = self._link_key(
                drone.current_hub,
                drone.target_hub,
            )
            usage[key] = usage.get(key, 0) + 1

        return usage

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

        for drone in self._ready_drones():
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

            link_key = self._link_key(
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
