# Maze Escape: AI Challenge

A dynamic, grid-based stealth escape game built in Python using **Pygame** and **NetworkX**. Navigate an unpredictable maze, outsmart an adaptive AI enemy utilizing distinct behavioral states, and reach the green exit sector to secure victory.

---

## Game Elements & Visuals

The play area consists of a 10×10 grid with custom-generated geometry. The interface updates its layout and color themes dynamically to mirror the threat level of the enemy tracking you:

*   🔵 **Player (Blue Circle):** Controlled via `WASD` or Arrow Keys.
*   🔴 **Enemy (Red Square):** A relentless tracking agent powered by an automated state machine.
*   🟢 **Exit (Green Square):** Your objective located at the bottom-right corner of the map.
*   📊 **HUD Panel (Top Banner):** Shifts color dynamically to indicate current enemy awareness (**Patrol**, **Search**, or **Chase**).

---

## Deep Dive: Core Mechanics & AI Architecture

### 1. Imperfect-Maze Generation
Rather than creating a perfect maze with exactly one solution, the system uses **Recursive Backtracking** combined with graph theory to construct a spanning tree. It then intentionally adds back **25% of the discarded walls**. This results in loopbacks, wide-open loops, and alternative pathways, allowing both you and the AI to loop around columns and execute tactical escapes.

### 2. Finite State Machine (FSM) Enemy AI
The enemy processes the world in real time across three distinct threat states:

*   **`PATROL` State (Calm Blue):** The enemy moves based on a **Heuristic Heatmap**. It keeps track of the timestamps when it last visited specific tiles and weights its movement choices toward paths it hasn't inspected in a while. This results in highly organic, non-repetitive exploration.
*   **`CHASE` State (Aggressive Red):** Triggered instantly when the player enters the enemy's vertical or horizontal Line of Sight (LoS), or wanders within a 4-step radius. The AI calculates the shortest route via an **A* Pathfinding Algorithm** using Manhattan distance:
    $$f(n) = g(n) + h(n)$$
    It then moves directly along this path toward you.
*   **`SEARCH` State (Alert Yellow):** If you break Line of Sight, the enemy rushes to your **last known position** using A*. It actively searches that area before timing out and reverting to its regular Patrol pattern.
*   **Anti-Stuck Logic:** If path geometry traps the AI or cuts off its pathing loops, an internal `STUCK_THRESHOLD` triggers an emergency fallback mode, forcing it to make random legal moves until its positioning matrix clears up.
