*This project has been created as part of the 42 curriculum by lucpelle.*

# Fly-in

## Description
**Fly-in** is an autonomous drone routing simulation system developed in Python. The main objective of the project is to route a fleet of multiple drones from a unique starting zone (`start_hub`) to a target destination (`end_hub`) through a dynamic, connected network of zones in the absolute minimum number of simulation turns. 

The system models the network as a graph of zones with various terrain behaviors and capacity limitations, managing simultaneous movements, preventing deadlocks, and optimizing throughput while strictly respecting all spatial and temporal constraints.

## Features & Constraints
- **Object-Oriented & Type-Safe Architecture:** Entirely designed using OOP principles and fully type-hinted, validated statically via `mypy` and linted with `flake8`.
- **Dynamic Zones & Routing Costs:** 
  - `normal`: 1 turn traversal cost.
  - `priority`: 1 turn traversal cost (highly preferred in paths).
  - `restricted`: 2 turns traversal cost (drones spend 1 turn in transit on the link/connection and must enter the zone on the next turn without waiting).
  - `blocked`: Inaccessible zones.
- **Capacity Management:** Respects `max_drones` constraints for individual zones and `max_link_capacity` for simultaneous connection traversals.
- **Dual Visual UI:** Features an interactive Pygame graphical interface tracking real-time positions and a detailed terminal debug logging system.

---

## Instructions

### Installation
Ensure you have Python 3.10+ installed. To install project dependencies (including `pygame`, `mypy`, and `flake8`), run:
```bash
make install
```

### Execution
To run the main simulation visualizer with map menu:
```bash
make run
```

To run the simulation with specific map file:
```bash
make run ARGS=maps/easy_1.txt
```

### Quality Control & Linting
To run static type checking (`mypy`) and coding style standards (`flake8`) as required by the guidelines:
```bash
make lint
```
For strict checking:
```bash
make lint-strict
```

### Cleaning Caches
To clear python cache files and type-checking state artifacts:
```bash
make clean
```

---

## Algorithm explanation

The pathfinding system uses a **Space-Time A\*** algorithm designed to move multiple drones simultaneously without collisions or deadlocks.

### How It Works

1. **Space-Time Expansion:** Instead of just looking for the shortest route on the map, the algorithm searches for a combination of **(Zone, Turn)**. This allows drones to safely follow each other or take the same paths at different times.
2. **Strategic Waiting:** If a path is blocked or a zone is full, the algorithm calculates a "waiting turn" in place. The drone stays in its current area until the bottleneck clears up.
3. **Turn-by-Turn Reservations:** As soon as a valid path is found for a drone, its schedule is booked in advance in shared timetables:
   * **Zones:** A slot is reserved from the turn the drone arrives until the turn it leaves.
   * **Connections:** A slot is reserved during the exact turns the drone is flying through it (which perfectly handles the 2-turn cost of `restricted` zones).

### Optimizations
* **Instant Handover:** When a drone leaves a zone, it frees up capacity *during that exact same turn*, allowing a trailing drone to enter immediately without losing time.
* **Conflict Prevention:** By checking resource availability at specific future turns, the system guarantees zero collisions and zero deadlocks.

## Visual Representation

The simulation includes an interactive graphical interface built with **Pygame** to display the network and animate drone movements in real-time.

### Interface Features

*   **Zones & Hubs:** Rendered as colored circles based on the `color` attribute defined in the map file (e.g., green, red). Hubs without a specified color default to light grey. The current capacity ratio (`current_drones / max_drones`) is displayed directly over each hub.
*   **Connections:** Drawn as lines between zones.
*   **Drones:** Displayed as small distinct drones. Drones currently traveling through a `restricted` zone connection are animated smoothly at the midpoint of the link to signal they are in transit.
*   **Simulation Control:** Features an automatic execution mode that can be toggled to run the simulation step-by-step, updating the display in sync with each turn until the final state is reached.

## Usage Example

### Input Map (`maps/easy_1.txt`)
```text
nb_drones: 2
start_hub: start 0 0 [color=green]
hub: mid 1 0 [color=blue]
end_hub: goal 2 0 [color=green]
connection: start-mid
connection: mid-goal
```

### Output
```text
-- Turn 0 --
D1-mid

-- Turn 1 --
D1-goal D2-mid

-- Turn 2 --
D2-goal

-- Simulation Finished at Turn 2 --
```

## Resources

* **Pathfinding & Graph Theory:** A*'s Algorithm concepts and Space-Time network expansion strategies.
* **Python Standard Library:** [Python `heapq` module documentation](https://docs.python.org/3/library/heapq.html) for priority queue optimization.
* **Graphics:** [Pygame Library Documentation](https://www.pygame.org/docs/) for window rendering, event loops, and coordinate drawing.
* **Code Quality:** [PEP 257 – Docstring Conventions](https://peps.python.org/pep-0257/) and strict `mypy`/`flake8` static analysis guidelines.

---

## AI Usage

Artificial Intelligence was used strategically throughout this project as a collaborative development peer to reduce repetitive tasks and optimize code quality:
* **Debug & Refactor:** Assisted in diagnosing turn-synchronization logic mismatches between the simulator engine and the Pygame rendering loop, ensuring the final turn displays properly.
* **Type-Safety Compliance:** Helped resolve strict `mypy` type annotation errors and structured clean type hints across the object-oriented architecture.


*Every line of code and configuration suggested by AI was thoroughly audited, reviewed with peers, tested against all provided maps, and fully understood before integration.*