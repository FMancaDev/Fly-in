from src.graph import Graph, Hub, ZoneType, Connection
from typing import Tuple


class ParserError(Exception):
    def __init__(self, message: str, line_number: int):
        super().__init__(f"Line {line_number}: {message}")


class Parser:
    def parse(self, filepath: str) -> Graph:
        pass

    def _parse_metadata(self, data: str, line_number: int) -> dict[str, str]:
        metadata: dict[str, str] = {}
        data = data.strip("[]")

        for item in data.split():
            if "=" not in item:
                raise ParserError(
                    f"Invalid Metadata Entry '{item}'", line_number
                )
            key, value = item.split("=", 1)
            metadata[key] = value
        return metadata

    def _parse_hub(self, data: str, line_number: int) -> Hub:
        metadata: dict[str, str] = {}

        if "[" in data:
            fixed_part, metadata_part = data.split("[", 1)
            metadata = self._parse_metadata("[" + metadata_part, line_number)
        else:
            fixed_part = data

        parts = fixed_part.split()

        if len(parts) != 3:
            raise ParserError("Invalid Hub Format", line_number)

        name = parts[0]

        try:
            x = int(parts[1])
            y = int(parts[2])
        except ValueError:
            raise ParserError("Hub coordinates must be integers", line_number)

        zone = metadata.get("zone", "normal")
        color = metadata.get("color", "none")

        try:
            max_drones = int(metadata.get("max_drones", "1"))
        except ValueError:
            raise ParserError("max_drones must be an integer", line_number)

        if max_drones <= 0:
            raise ParserError("max_drones must be greater than 0", line_number)

        try:
            zone_type = ZoneType(zone)
        except ValueError:
            raise ParserError(f"Invalid zone type '{zone}'", line_number)

        return Hub(
            name=name,
            x=x,
            y=y,
            zone_type=zone_type,
            color=color,
            max_drones=max_drones,
        )

    def _parse_connection(self, data: str, graph: Graph, line_number: int) -> Connection:
        metadata: dict[str, str] = {}

        if "[" in data:
            fixed_part, metadata_part = data.split("[", 1)
            metadata = self._parse_metadata("[" + metadata_part, line_number)
        else:
            fixed_part = data

        fixed_part = fixed_part.strip()

        if "-" not in fixed_part:
            raise ParserError("Invalid Connection Format", line_number)

        try:
            hub1_name, hub2_name = fixed_part.split("-", 1)
        except ValueError:
            raise ParserError("Invalid Connection Format", line_number)

        hub1_name = hub1_name.strip()
        hub2_name = hub2_name.strip()

        if hub1_name not in graph.hubs:
            raise ParserError(
                f"Unkmow hub '{hub1_name}'",
                line_number
            )

        if hub2_name not in graph.hubs:
            raise ParserError(
                f"Unkmow hub '{hub2_name}'",
                line_number
            )

        hub1 = graph.hubs[hub1_name]
        hub2 = graph.hubs[hub2_name]

        try:
            max_link_capacity = int(
                metadata.get("max_link_capacity", "1")
            )

        except ValueError:
            raise ParserError(
                "max_link_capacity must be an integer",
                line_number
            )

        if max_link_capacity <= 0:
            raise ParserError(
                "max_link_capacity must be greater than 0",
                line_number
            )

        return Connection(
            hub1=hub1,
            hub2=hub2,
            max_link_capacity=max_link_capacity
        )

    def parse(self, filepath: str) -> Tuple[Graph, int]:
        graph = Graph()
        nb_drones: int | None = None

        with open(filepath, "r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                if line.startswith("nb_drones:"):
                    if nb_drones is not None:
                        raise ParserError(
                            "nb_drones defined multiple times",
                            line_number
                        )

                    value = line.removeprefix("nb_drones:").strip()

                    try:
                        nb_drones = int(value)
                    except ValueError:
                        raise ParserError(
                            "nb_drones must be an integer",
                            line_number
                        )

                elif line.startswith("start_hub:"):
                    if graph.start_hub is not None:
                        raise ParserError(
                            "Multiple start hubs defined",
                            line_number
                        )

                    data = line.removeprefix("start_hub:").strip()

                    hub = self._parse_hub(data, line_number)

                    graph.start_hub = hub
                    graph.hubs[hub.name] = hub

                elif line.startswith("end_hub:"):
                    if graph.end_hub is not None:
                        raise ParserError(
                            "Multiple end hubs defined",
                            line_number
                        )

                    data = line.removeprefix("end_hub:").strip()

                    hub = self._parse_hub(data, line_number)

                    graph.end_hub = hub
                    graph.hubs[hub.name] = hub

                elif line.startswith("hub:"):
                    data = line.removeprefix("hub:").strip()

                    hub = self._parse_hub(data, line_number)

                    if hub.name in graph.hubs:
                        raise ParserError(
                            f"Duplicate hub '{hub.name}'",
                            line_number
                        )

                    graph.hubs[hub.name] = hub

                elif line.startswith("connection:"):
                    data = line.removeprefix("connection:").strip()

                    connection = self._parse_connection(
                        data,
                        graph,
                        line_number
                    )
                    graph.connections.append(connection)
                else:
                    raise ParserError(
                        "Unknown line type",
                        line_number
                    )

        if graph.start_hub is None:
            raise ParserError("Missing start_hub", 0)

        if graph.end_hub is None:
            raise ParserError("Missing end_hub", 0)

        if nb_drones is None:
            raise ParserError("Missing nb_drones", 0)

        if nb_drones <= 0:
            raise ParserError(
                "nb_drones must be greater than 0",
                0
            )
        return graph, nb_drones
