from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
import pygame
from src.graph import Drone, Graph, Hub
from src.simulation import Simulation


Color = tuple[int, int, int]
Point = tuple[int, int]


@dataclass
class LegendItem:
    label: str
    color: Color


class Renderer:
    WIDTH = 1500
    HEIGHT = 960

    PANEL_WIDTH = 350
    GRAPH_MARGIN = 65

    HUB_RADIUS = 25
    DRONE_RADIUS = 10

    FPS = 60

    BACKGROUND: Color = (15, 22, 34)
    PANEL_BACKGROUND: Color = (18, 27, 41)
    CARD_BACKGROUND: Color = (22, 32, 48)

    CARD_BORDER: Color = (48, 61, 80)
    CONNECTION_COLOR: Color = (135, 148, 170)
    CONNECTION_TEXT: Color = (220, 225, 235)

    TEXT_COLOR: Color = (235, 239, 247)
    MUTED_TEXT: Color = (170, 180, 195)

    HUB_BORDER: Color = (225, 230, 238)
    DRONE_COLOR: Color = (245, 245, 250)
    DRONE_TEXT: Color = (20, 24, 32)

    FULL_COLOR: Color = (235, 65, 75)
    SUCCESS_COLOR: Color = (50, 215, 100)
    WARNING_COLOR: Color = (245, 200, 35)
    ACCENT_COLOR: Color = (65, 145, 245)

    COLOR_NAMES: dict[str, Color] = {
        "green": (38, 180, 90),
        "red": (205, 45, 50),
        "blue": (55, 120, 220),
        "yellow": (235, 177, 15),
        "orange": (235, 115, 10),
        "purple": (130, 55, 190),
        "violet": (145, 60, 205),
        "cyan": (30, 180, 195),
        "brown": (145, 80, 40),
        "gold": (230, 175, 20),
        "black": (45, 47, 52),
        "gray": (85, 90, 100),
        "grey": (85, 90, 100),
        "maroon": (135, 35, 45),
        "darkred": (150, 35, 40),
        "crimson": (190, 35, 65),
        "pink": (215, 55, 180),
        "magenta": (205, 45, 180),
        "lime": (105, 205, 55),
        "white": (220, 220, 225),
        "none": (95, 100, 110),
    }

    DISPLAY_NAMES: dict[str, str] = {
        "green": "Start",
        "pink": "Goal",
        "magenta": "Goal",
        "purple": "Priority",
        "violet": "Priority",
        "orange": "Restricted",
        "yellow": "Normal",
        "gold": "Normal",
        "black": "Blocked",
        "gray": "Blocked",
        "grey": "Blocked",
        "brown": "Connector",
        "red": "Constricted",
        "darkred": "Constricted",
        "maroon": "Constricted",
        "crimson": "Constricted",
        "blue": "Blue zone",
        "cyan": "Cyan zone",
        "lime": "Lime zone",
        "none": "Default",
    }

    def __init__(
        self,
        graph: Graph,
        simulation: Simulation,
    ) -> None:
        pygame.init()
        pygame.font.init()

        self.graph = graph
        self.simulation = simulation

        self.screen = pygame.display.set_mode(
            (self.WIDTH, self.HEIGHT),
            pygame.RESIZABLE,
        )

        pygame.display.set_caption("Fly-in Simulation")

        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.Font(None, 42)
        self.section_font = pygame.font.Font(None, 28)
        self.font = pygame.font.Font(None, 23)
        self.small_font = pygame.font.Font(None, 18)
        self.hub_font = pygame.font.Font(None, 19)

        self.running = True
        self.paused = True

        self.turn_delay = 700
        self.last_turn_time = pygame.time.get_ticks()

        self.positions: dict[str, Point] = {}
        self.hovered_hub: Hub | None = None

        self._calculate_positions()

    @property
    def graph_width(self) -> int:
        return self.WIDTH - self.PANEL_WIDTH

    def _get_color_name(self, hub: Hub) -> str:
        color = getattr(hub, "color", "none")

        if color is None:
            return "none"

        return str(color).lower()

    def _hub_color(self, hub: Hub) -> Color:
        color_name = self._get_color_name(hub)

        if hub == self.graph.start_hub:
            return self.COLOR_NAMES["green"]

        if hub == self.graph.end_hub:
            return self.COLOR_NAMES["magenta"]

        return self.COLOR_NAMES.get(
            color_name,
            self.COLOR_NAMES["none"],
        )

    def _display_zone_name(self, color_name: str) -> str:
        return self.DISPLAY_NAMES.get(
            color_name,
            color_name.replace("_", " ").title(),
        )

    def _render_text(
        self,
        text: str,
        font: pygame.font.Font,
        color: Color,
        position: Point,
    ) -> pygame.Rect:
        surface = font.render(text, True, color)
        return self.screen.blit(surface, position)

    def _draw_rounded_card(
        self,
        rect: pygame.Rect,
        radius: int = 12,
    ) -> None:
        pygame.draw.rect(
            self.screen,
            self.CARD_BACKGROUND,
            rect,
            border_radius=radius,
        )

        pygame.draw.rect(
            self.screen,
            self.CARD_BORDER,
            rect,
            width=1,
            border_radius=radius,
        )

    def _calculate_positions(self) -> None:
        hubs = list(self.graph.hubs.values())

        if not hubs:
            return

        min_x = min(hub.x for hub in hubs)
        max_x = max(hub.x for hub in hubs)
        min_y = min(hub.y for hub in hubs)
        max_y = max(hub.y for hub in hubs)

        available_width = (
            self.graph_width
            - 2 * self.GRAPH_MARGIN
        )

        available_height = (
            self.HEIGHT
            - 2 * self.GRAPH_MARGIN
        )

        x_range = max(max_x - min_x, 1)
        y_range = max(max_y - min_y, 1)

        self.positions.clear()

        for hub in hubs:
            normalized_x = (hub.x - min_x) / x_range
            normalized_y = (hub.y - min_y) / y_range

            screen_x = int(
                self.GRAPH_MARGIN
                + normalized_x * available_width
            )

            screen_y = int(
                self.HEIGHT
                - self.GRAPH_MARGIN
                - normalized_y * available_height
            )

            self.positions[hub.name] = (
                screen_x,
                screen_y,
            )

    def _hub_usage(self, hub: Hub) -> int:
        usage = 0

        for drone in self.simulation.drones:
            if drone.delivered:
                continue

            if drone.current_hub != hub:
                continue

            if drone.target_hub is None:
                usage += 1

        return usage

    def _connection_usage(self, connection) -> int:
        usage = 0

        connection_hubs = {
            connection.hub1.name,
            connection.hub2.name,
        }

        for drone in self.simulation.drones:
            if drone.delivered:
                continue

            if drone.current_hub is None:
                continue

            if drone.target_hub is None:
                continue

            drone_hubs = {
                drone.current_hub.name,
                drone.target_hub.name,
            }

            if drone_hubs == connection_hubs:
                usage += 1

        return usage

    def _delivered_count(self) -> int:
        return sum(
            1
            for drone in self.simulation.drones
            if drone.delivered
        )

    def _in_transit_count(self) -> int:
        return sum(
            1
            for drone in self.simulation.drones
            if (
                not drone.delivered
                and drone.target_hub is not None
            )
        )

    def _draw_connections(self) -> None:
        for connection in self.graph.connections:
            start = self.positions.get(
                connection.hub1.name
            )
            end = self.positions.get(
                connection.hub2.name
            )

            if start is None or end is None:
                continue

            usage = self._connection_usage(connection)
            capacity = connection.max_link_capacity

            is_full = (
                capacity > 0
                and usage >= capacity
            )

            color = (
                self.FULL_COLOR
                if is_full
                else self.CONNECTION_COLOR
            )

            width = 4 if is_full else 2

            pygame.draw.line(
                self.screen,
                color,
                start,
                end,
                width,
            )

            middle_x = (start[0] + end[0]) // 2
            middle_y = (start[1] + end[1]) // 2

            label = f"{usage}/{capacity}"

            label_surface = self.small_font.render(
                label,
                True,
                self.CONNECTION_TEXT,
            )

            background_rect = label_surface.get_rect(
                center=(middle_x, middle_y)
            )

            background_rect.inflate_ip(8, 4)

            pygame.draw.rect(
                self.screen,
                self.BACKGROUND,
                background_rect,
                border_radius=4,
            )

            self.screen.blit(
                label_surface,
                label_surface.get_rect(
                    center=(middle_x, middle_y)
                ),
            )

    def _draw_hubs(self) -> None:
        for hub in self.graph.hubs.values():
            position = self.positions.get(hub.name)

            if position is None:
                continue

            usage = self._hub_usage(hub)
            capacity = hub.max_drones

            is_full = (
                capacity > 0
                and usage >= capacity
            )

            if hub == self.hovered_hub:
                pygame.draw.circle(
                    self.screen,
                    self.ACCENT_COLOR,
                    position,
                    self.HUB_RADIUS + 7,
                )
            elif is_full:
                pygame.draw.circle(
                    self.screen,
                    self.FULL_COLOR,
                    position,
                    self.HUB_RADIUS + 6,
                )

            pygame.draw.circle(
                self.screen,
                self._hub_color(hub),
                position,
                self.HUB_RADIUS,
            )

            pygame.draw.circle(
                self.screen,
                self.HUB_BORDER,
                position,
                self.HUB_RADIUS,
                1,
            )

            capacity_surface = self.hub_font.render(
                f"{usage}/{capacity}",
                True,
                self.TEXT_COLOR,
            )

            capacity_rect = capacity_surface.get_rect(
                center=position
            )

            self.screen.blit(
                capacity_surface,
                capacity_rect,
            )

    def _drone_position(
        self,
        drone: Drone,
    ) -> Point | None:
        if drone.current_hub is None:
            return None

        current_position = self.positions.get(
            drone.current_hub.name
        )

        if current_position is None:
            return None

        if drone.target_hub is None:
            return current_position

        target_position = self.positions.get(
            drone.target_hub.name
        )

        if target_position is None:
            return current_position

        remaining = max(drone.remaining_turns, 0)

        connection = self._find_connection(
            drone.current_hub,
            drone.target_hub,
        )

        total_turns = 1

        if connection is not None:
            total_turns = max(
                getattr(connection, "weight", 1),
                1,
            )

        progress = 1.0 - min(
            remaining / total_turns,
            1.0,
        )

        x = int(
            current_position[0]
            + (
                target_position[0]
                - current_position[0]
            ) * progress
        )

        y = int(
            current_position[1]
            + (
                target_position[1]
                - current_position[1]
            ) * progress
        )

        return x, y

    def _find_connection(
        self,
        hub1: Hub,
        hub2: Hub,
    ):
        target_names = {
            hub1.name,
            hub2.name,
        }

        for connection in self.graph.connections:
            connection_names = {
                connection.hub1.name,
                connection.hub2.name,
            }

            if connection_names == target_names:
                return connection

        return None

    def _draw_drones(self) -> None:
        grouped: defaultdict[Point, list[Drone]] = defaultdict(list)

        for drone in self.simulation.drones:
            if drone.delivered:
                continue

            position = self._drone_position(drone)

            if position is not None:
                grouped[position].append(drone)

        offsets = [
            (0, 0),
            (-15, -15),
            (15, -15),
            (-15, 15),
            (15, 15),
            (0, -22),
            (0, 22),
            (-22, 0),
            (22, 0),
        ]

        for base_position, drones in grouped.items():
            for index, drone in enumerate(drones):
                offset = offsets[index % len(offsets)]

                position = (
                    base_position[0] + offset[0],
                    base_position[1] + offset[1],
                )

                pygame.draw.circle(
                    self.screen,
                    self.DRONE_COLOR,
                    position,
                    self.DRONE_RADIUS,
                )

                pygame.draw.circle(
                    self.screen,
                    self.DRONE_TEXT,
                    position,
                    self.DRONE_RADIUS,
                    2,
                )

                id_surface = self.small_font.render(
                    str(drone.id),
                    True,
                    self.DRONE_TEXT,
                )

                self.screen.blit(
                    id_surface,
                    id_surface.get_rect(
                        center=position
                    ),
                )

    def _draw_status_card(
        self,
        panel_x: int,
        y: int,
    ) -> int:
        rect = pygame.Rect(
            panel_x + 20,
            y,
            self.PANEL_WIDTH - 40,
            165,
        )

        self._draw_rounded_card(rect)

        delivered = self._delivered_count()
        in_transit = self._in_transit_count()

        status = (
            "PAUSED"
            if self.paused
            else "RUNNING"
        )

        status_color = (
            self.WARNING_COLOR
            if self.paused
            else self.SUCCESS_COLOR
        )

        label_x = rect.x + 20
        value_x = rect.x + 130

        line_y = rect.y + 22

        entries = [
            (
                "Turn:",
                str(self.simulation.turn),
                self.ACCENT_COLOR,
            ),
            (
                "Status:",
                status,
                status_color,
            ),
            (
                "Delivered:",
                (
                    f"{delivered}/"
                    f"{len(self.simulation.drones)}"
                ),
                self.SUCCESS_COLOR,
            ),
            (
                "In transit:",
                str(in_transit),
                self.TEXT_COLOR,
            ),
        ]

        for label, value, value_color in entries:
            self._render_text(
                label,
                self.font,
                self.TEXT_COLOR,
                (label_x, line_y),
            )

            self._render_text(
                value,
                self.font,
                value_color,
                (value_x, line_y),
            )

            line_y += 34

        return rect.bottom + 18

    def _draw_control_icon(
        self,
        center: Point,
        symbol: str,
        color: Color,
    ) -> None:
        pygame.draw.circle(
            self.screen,
            color,
            center,
            15,
        )

        symbol_surface = self.font.render(
            symbol,
            True,
            self.TEXT_COLOR,
        )

        self.screen.blit(
            symbol_surface,
            symbol_surface.get_rect(center=center),
        )

    def _draw_controls_card(
        self,
        panel_x: int,
        y: int,
    ) -> int:
        rect = pygame.Rect(
            panel_x + 20,
            y,
            self.PANEL_WIDTH - 40,
            280,
        )

        self._draw_rounded_card(rect)

        self._render_text(
            "Controls",
            self.section_font,
            self.TEXT_COLOR,
            (rect.x + 20, rect.y + 18),
        )

        controls = [
            ("▶", "SPACE", "Play / Pause", self.ACCENT_COLOR),
            ("→", "RIGHT", "Next turn", self.ACCENT_COLOR),
            ("↑", "UP", "Faster", self.ACCENT_COLOR),
            ("↓", "DOWN", "Slower", self.ACCENT_COLOR),
            ("■", "ESC", "Exit", self.FULL_COLOR),
        ]

        line_y = rect.y + 68

        for symbol, key, action, color in controls:
            icon_center = (
                rect.x + 35,
                line_y + 10,
            )

            self._draw_control_icon(
                icon_center,
                symbol,
                color,
            )

            self._render_text(
                key,
                self.font,
                self.TEXT_COLOR,
                (rect.x + 65, line_y),
            )

            self._render_text(
                action,
                self.font,
                self.TEXT_COLOR,
                (rect.x + 150, line_y),
            )

            line_y += 42

        self._render_text(
            f"Delay: {self.turn_delay} ms",
            self.font,
            self.MUTED_TEXT,
            (rect.x + 20, rect.bottom - 38),
        )

        return rect.bottom + 18

    def _build_legend(self) -> list[LegendItem]:
        items: list[LegendItem] = []
        used_labels: set[str] = set()

        start_item = LegendItem(
            "Start",
            self.COLOR_NAMES["green"],
        )

        goal_item = LegendItem(
            "Goal",
            self.COLOR_NAMES["magenta"],
        )

        items.append(start_item)
        items.append(goal_item)

        used_labels.add("Start")
        used_labels.add("Goal")

        for hub in self.graph.hubs.values():
            if hub == self.graph.start_hub:
                continue

            if hub == self.graph.end_hub:
                continue

            color_name = self._get_color_name(hub)
            label = self._display_zone_name(color_name)

            if label in used_labels:
                continue

            used_labels.add(label)

            items.append(
                LegendItem(
                    label,
                    self._hub_color(hub),
                )
            )

        return items

    def _draw_legend_card(
        self,
        panel_x: int,
        y: int,
    ) -> int:
        legend = self._build_legend()

        columns = 2
        rows = (len(legend) + columns - 1) // columns

        card_height = 60 + rows * 34

        rect = pygame.Rect(
            panel_x + 20,
            y,
            self.PANEL_WIDTH - 40,
            card_height,
        )

        self._draw_rounded_card(rect)

        self._render_text(
            "Legend",
            self.section_font,
            self.TEXT_COLOR,
            (rect.x + 20, rect.y + 16),
        )

        column_width = (rect.width - 40) // columns

        for index, item in enumerate(legend):
            column = index % columns
            row = index // columns

            item_x = (
                rect.x
                + 20
                + column * column_width
            )

            item_y = (
                rect.y
                + 58
                + row * 34
            )

            pygame.draw.circle(
                self.screen,
                item.color,
                (item_x + 10, item_y + 9),
                10,
            )

            pygame.draw.circle(
                self.screen,
                self.HUB_BORDER,
                (item_x + 10, item_y + 9),
                10,
                1,
            )

            self._render_text(
                item.label,
                self.small_font,
                self.TEXT_COLOR,
                (item_x + 28, item_y),
            )

        return rect.bottom + 18

    def _draw_hover_card(
        self,
        panel_x: int,
        y: int,
    ) -> int:
        rect = pygame.Rect(
            panel_x + 20,
            y,
            self.PANEL_WIDTH - 40,
            105,
        )

        self._draw_rounded_card(rect)

        if self.hovered_hub is None:
            self._render_text(
                "Hub information",
                self.section_font,
                self.TEXT_COLOR,
                (rect.x + 20, rect.y + 16),
            )

            self._render_text(
                "Move the mouse over a hub",
                self.small_font,
                self.MUTED_TEXT,
                (rect.x + 20, rect.y + 57),
            )

            return rect.bottom + 18

        hub = self.hovered_hub
        usage = self._hub_usage(hub)
        color_name = self._get_color_name(hub)

        if hub == self.graph.start_hub:
            zone_name = "Start"
        elif hub == self.graph.end_hub:
            zone_name = "Goal"
        else:
            zone_name = self._display_zone_name(color_name)

        pygame.draw.circle(
            self.screen,
            self._hub_color(hub),
            (rect.x + 30, rect.y + 29),
            11,
        )

        self._render_text(
            hub.name,
            self.section_font,
            self.TEXT_COLOR,
            (rect.x + 50, rect.y + 16),
        )

        self._render_text(
            f"Zone: {zone_name}",
            self.small_font,
            self.MUTED_TEXT,
            (rect.x + 20, rect.y + 56),
        )

        self._render_text(
            f"Capacity: {usage}/{hub.max_drones}",
            self.small_font,
            self.MUTED_TEXT,
            (rect.x + 20, rect.y + 79),
        )

        return rect.bottom + 18

    def _draw_finished_card(
        self,
        panel_x: int,
        y: int,
    ) -> None:
        if not self.simulation.all_delivered():
            return

        available_height = self.HEIGHT - y - 16

        if available_height < 55:
            return

        rect = pygame.Rect(
            panel_x + 20,
            y,
            self.PANEL_WIDTH - 40,
            55,
        )

        self._draw_rounded_card(rect)

        self._render_text(
            "Simulation finished!",
            self.font,
            self.SUCCESS_COLOR,
            (rect.x + 20, rect.y + 17),
        )

    def _draw_panel(self) -> None:
        panel_x = self.graph_width

        pygame.draw.rect(
            self.screen,
            self.PANEL_BACKGROUND,
            (
                panel_x,
                0,
                self.PANEL_WIDTH,
                self.HEIGHT,
            ),
        )

        pygame.draw.line(
            self.screen,
            self.CARD_BORDER,
            (panel_x, 0),
            (panel_x, self.HEIGHT),
            1,
        )

        self._render_text(
            "Fly-in",
            self.title_font,
            self.TEXT_COLOR,
            (panel_x + 25, 22),
        )

        y = 78
        y = self._draw_status_card(panel_x, y)
        y = self._draw_controls_card(panel_x, y)
        y = self._draw_legend_card(panel_x, y)
        y = self._draw_hover_card(panel_x, y)

        self._draw_finished_card(panel_x, y)

    # mouse interaction
    def _update_hovered_hub(self) -> None:
        mouse_x, mouse_y = pygame.mouse.get_pos()

        self.hovered_hub = None

        if mouse_x >= self.graph_width:
            return

        for hub in self.graph.hubs.values():
            position = self.positions.get(hub.name)

            if position is None:
                continue

            dx = mouse_x - position[0]
            dy = mouse_y - position[1]

            distance_squared = dx * dx + dy * dy

            if distance_squared <= self.HUB_RADIUS ** 2:
                self.hovered_hub = hub
                return

    def _handle_key(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self.running = False

        elif key == pygame.K_SPACE:
            self.paused = not self.paused
            self.last_turn_time = pygame.time.get_ticks()

        elif key == pygame.K_RIGHT:
            if not self.simulation.all_delivered():
                self.simulation.simulate_turn()

        elif key == pygame.K_UP:
            self.turn_delay = max(
                100,
                self.turn_delay - 100,
            )

        elif key == pygame.K_DOWN:
            self.turn_delay = min(
                3000,
                self.turn_delay + 100,
            )

    def _handle_resize(
        self,
        width: int,
        height: int,
    ) -> None:
        self.WIDTH = max(width, 1000)
        self.HEIGHT = max(height, 700)

        self.screen = pygame.display.set_mode(
            (self.WIDTH, self.HEIGHT),
            pygame.RESIZABLE,
        )

        self._calculate_positions()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                self._handle_key(event.key)

            elif event.type == pygame.VIDEORESIZE:
                self._handle_resize(
                    event.w,
                    event.h,
                )

    def _update(self) -> None:
        self._update_hovered_hub()

        if self.paused:
            return

        if self.simulation.all_delivered():
            self.paused = True
            return

        now = pygame.time.get_ticks()

        if now - self.last_turn_time >= self.turn_delay:
            self.simulation.simulate_turn()
            self.last_turn_time = now

    # rendering
    def _draw(self) -> None:
        self.screen.fill(self.BACKGROUND)

        self._draw_connections()
        self._draw_hubs()
        self._draw_drones()
        self._draw_panel()

        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            self._handle_events()
            self._update()
            self._draw()

            self.clock.tick(self.FPS)

        pygame.quit()
