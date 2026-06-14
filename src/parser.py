from src.graph import Graph


class ParserError(Exception):
    def __init__(self, message: str, line_number: int):
        super().__init__(f"Line {line_number}: {message}")


class Parser:
    def parse(self, filepath: str) -> Graph:
        pass

    def _parse_metadata(self, raw: str) -> dict[str, str]:
        pass
