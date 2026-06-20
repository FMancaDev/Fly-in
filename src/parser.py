from src.graph import Graph, Hub, ZoneType, Connection


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

        if "-" nr
