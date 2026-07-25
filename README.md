*This project has been created as part of the 42 curriculum by fomanca.*

# Fly-in

## Description

Fly-in is a drone routing simulation written in Python.

The goal is to move all drones from the start hub to the goal hub in the lowest possible number of turns while respecting:

- hub capacities;
- connection capacities;
- restricted zones;
- blocked zones;
- movement duration;
- graph connectivity.

The project includes a parser, a graph representation, a pathfinding system, a turn-based simulation engine, terminal output, and a graphical interface made with Pygame.

## Instructions

Python 3.10 or later is required.

Install the dependencies and create the virtual environment:

```bash
make install
```

Run the simulation in the terminal:

```bash
make run MAP=maps/easy/01_linear_path.txt
```

Run the graphical interface:

```bash
make graphics MAP=maps/easy/01_linear_path.txt
```

Run the program with Python's debugger:

```bash
make debug MAP=maps/easy/01_linear_path.txt
```

Check the project with flake8 and mypy:

```bash
make lint
```

Remove temporary files and caches:

```bash
make clean
```

## Algorithm and implementation strategy

The input file is parsed into a graph made of hubs and connections.

Each hub stores its name, coordinates, capacity, color, and zone type. Each connection stores the two connected hubs and its capacity.

The pathfinding system searches for valid routes between the start and goal hubs. Routes are evaluated according to their length, movement cost, hub restrictions, and available capacity.

Drones are distributed across the selected routes to avoid sending every drone through the same bottleneck.

The simulation runs turn by turn. During each turn, it:

1. updates drones that are already travelling;
2. marks drones that reached their destination hub;
3. checks hub and connection capacities;
4. selects drones that are allowed to move;
5. starts new movements;
6. stops when every drone reaches the goal.

Drones farther along their route are generally given priority so that occupied hubs and connections are released sooner. Drones waiting at the start are ordered consistently to avoid delaying routes with a higher total cost.

## Visual representation

The project provides two forms of visual feedback.

### Terminal

The terminal output shows the simulation turn by turn and can use colors to distinguish states and zone types.

### Pygame interface

The graphical interface displays:

- hubs and connections;
- hub and connection capacities;
- drone IDs;
- drones travelling between hubs;
- delivered drones;
- current turn;
- simulation status;
- play, pause, next-turn, and speed controls;
- a legend for zone colors;
- hub information when the mouse is placed over a hub.

This representation makes it easier to understand drone movement, congestion, restricted zones, and the routes used by each drone.

## Resources

- Python documentation
- Pygame documentation
- Python `heapq` documentation
- Dijkstra's shortest path algorithm
- 42 Fly-in subject

AI was used to help review documentation, suggest test cases, improve code organization, and identify possible issues in the graphical interface. All generated suggestions were reviewed, tested, and adapted before being included in the project.
