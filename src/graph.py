from enum import Enum
from dataclasses import dataclass


class ZoneType(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


@dataclass
class Hub:
    name: str
    x: int
    y: int
    zone_type: ZoneType
    color: str
    max_drones: int


@dataclass
class Connection:
    hub1: Hub
    hub2: Hub
    max_link_capacity: int


@dataclass
class Drone:
    id: int
    current_hub: Hub | None
    target_hub: Hub | None
    remaining_turns: int = 0
    delivered: bool = False


class Graph:
    def __init__(self) -> None:
        self.hubs: dict[str, Hub] = {}
        self.connections: list[Connection] = []
        self.adjacency: dict[str, list[Hub]] = {}

        self.start_hub: Hub | None = None
        self.end_hub: Hub | None = None

    def build_adjacency(self) -> None:
        self.adjacency = {}

        for hub_name in self.hubs:
            self.adjacency[hub_name] = []

        for connection in self.connections:
            self.adjacency[connection.hub1.name].append(connection.hub2)
            self.adjacency[connection.hub2.name].append(connection.hub1)
