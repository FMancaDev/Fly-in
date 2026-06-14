from src.parser import parser
from enum import Enum
from dataclasses import dataclass


class ZoneType(Enum):
    NORNAL = "normal"
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


class Graph:
    def __init__(self) -> None:
        self.hubs: dict[str | Hub] = {}
        self.connections: list[Connection] = []
        self.start_hub: Hub | None = None
        self.end_hub: Hub | None = None
