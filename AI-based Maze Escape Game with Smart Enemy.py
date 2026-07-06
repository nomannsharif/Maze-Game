# ========== MEMBER 1: The Set Designer
import pygame
import networkx as nx
import random
import heapq
import math

WIDTH, HEIGHT = 800, 880
ROWS, COLS = 10, 10
TILE_SIZE = WIDTH // COLS
FPS = 120

HUD_HEIGHT_BUFFER = 80

BG_GRADIENT_START = (180, 200, 220)
BG_GRADIENT_END = (220, 235, 245)
PATH_COLOR = (255, 255, 255)
WALL_COLOR = (45, 65, 85)
PLAYER_COLOR = (50, 150, 220)
ENEMY_COLOR = (220, 70, 50)
EXIT_COLOR = (60, 180, 120)
TEXT_COLOR = (30, 45, 60)
SHADOW_COLOR = (0, 0, 0, 80)

WALL_THICKNESS = 15

ENEMY_MOVE_DELAY = 250

STUCK_THRESHOLD = 10
STUCK_UNSTUCK_MOVES = 2

PATROL_HUD_COLOR = (50, 150, 200)
SEARCH_HUD_COLOR = (255, 180, 50)
CHASE_HUD_COLOR = (200, 50, 50)
HUD_TEXT_COLOR = (255, 255, 255)

WIN_SCREEN_COLOR = (50, 180, 100)
LOSE_SCREEN_COLOR = (180, 50, 50)
MESSAGE_TEXT_COLOR = (255, 255, 255)


def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(graph, start, goal):
    queue = [(0, start)]
    came_from = {start: None}
    cost_so_far = {start: 0}

    while queue:
        current_priority, current = heapq.heappop(queue)

        if current == goal:
            break

        for neighbor in graph.neighbors(current):
            new_cost = cost_so_far[current] + 1

            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                priority = new_cost + heuristic(goal, neighbor)
                heapq.heappush(queue, (priority, neighbor))
                came_from[neighbor] = current

    path = []
    curr = goal
    if goal not in came_from:
        return []

    while curr != start:
        path.append(curr)
        curr = came_from.get(curr)
        if curr is None:
            return []
    path.reverse()
    return path


def generate_maze(rows, cols):
    maze_graph = nx.Graph()
    for r in range(rows):
        for c in range(cols):
            maze_graph.add_node((r, c))

    visited = set()
    stack = []

    spanning_tree_edges = set()

    start_cell = (random.randint(0, rows - 1), random.randint(0, cols - 1))
    visited.add(start_cell)
    stack.append(start_cell)

    while stack:
        current_cell = stack[-1]
        r, c = current_cell

        neighbors_to_explore = []
        potential_neighbors = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]

        for nr, nc in potential_neighbors:
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited:
                neighbors_to_explore.append((nr, nc))

        if neighbors_to_explore:
            next_cell = random.choice(neighbors_to_explore)

            maze_graph.add_edge(current_cell, next_cell)
            spanning_tree_edges.add(tuple(sorted((current_cell, next_cell))))

            visited.add(next_cell)
            stack.append(next_cell)
        else:
            stack.pop()

    full_grid_edges = set()
    for r_idx in range(rows):
        for c_idx in range(cols):
            if r_idx + 1 < rows:
                full_grid_edges.add(tuple(sorted(((r_idx, c_idx), (r_idx + 1, c_idx)))))
            if c_idx + 1 < cols:
                full_grid_edges.add(tuple(sorted(((r_idx, c_idx), (r_idx, c_idx + 1)))))

    unused_edges = list(full_grid_edges - spanning_tree_edges)

    num_edges_to_add_back = int(len(unused_edges) * 0.25)

    random.shuffle(unused_edges)

    for i in range(min(num_edges_to_add_back, len(unused_edges))):
        u, v = unused_edges[i]
        maze_graph.add_edge(u, v)

    return maze_graph

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Maze Escape: AI Challenge")
clock = pygame.time.Clock()

game_state = "RUNNING"

PATROL = "PATROL"
CHASE = "CHASE"
SEARCH = "SEARCH"

maze = None
player_pos = None
exit_pos = None
enemy_pos = None
enemy_state = None
chase_path = []
last_known_player_pos = None
last_enemy_move_time = 0
visited_cells_tracker = {}
enemy_stuck_frames = 0


def reset_game():
    global game_state, maze, player_pos, exit_pos, enemy_pos, enemy_state, \
        chase_path, last_known_player_pos, last_enemy_move_time, \
        visited_cells_tracker, enemy_stuck_frames

    game_state = "RUNNING"
    maze = generate_maze(ROWS, COLS)

    player_pos = (0, 0)
    exit_pos = (ROWS - 1, COLS - 1)
    enemy_pos = (ROWS - 1, 0)

    enemy_state = PATROL
    chase_path = []
    last_known_player_pos = None

    last_enemy_move_time = pygame.time.get_ticks()

    visited_cells_tracker = {(r, c): 0 for r in range(ROWS) for c in range(COLS)}
    visited_cells_tracker[enemy_pos] = pygame.time.get_ticks()

    enemy_stuck_frames = 0


reset_game()


# ========== MEMBER 3: The Camera Operator
def draw(maze_graph, player, enemy, current_exit_pos, enemy_current_state):
    y_offset = HUD_HEIGHT_BUFFER

    for y in range(HEIGHT):
        r = int(BG_GRADIENT_START[0] + (BG_GRADIENT_END[0] - BG_GRADIENT_START[0]) * y / HEIGHT)
        g = int(BG_GRADIENT_START[1] + (BG_GRADIENT_END[1] - BG_GRADIENT_START[1]) * y / HEIGHT)
        b = int(BG_GRADIENT_START[2] + (BG_GRADIENT_END[2] - BG_GRADIENT_START[2]) * y / HEIGHT)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    pygame.draw.rect(screen, PATH_COLOR, (0, y_offset, WIDTH, HEIGHT - y_offset))

    for r in range(ROWS):
        for c in range(COLS):
            pygame.draw.rect(screen, PATH_COLOR, (c * TILE_SIZE, r * TILE_SIZE + y_offset, TILE_SIZE, TILE_SIZE))

            if r > 0 and not maze_graph.has_edge((r, c), (r - 1, c)):
                pygame.draw.rect(screen, WALL_COLOR,
                                 (c * TILE_SIZE, r * TILE_SIZE + y_offset - WALL_THICKNESS // 2,
                                  TILE_SIZE, WALL_THICKNESS))
            if c > 0 and not maze_graph.has_edge((r, c), (r, c - 1)):
                pygame.draw.rect(screen, WALL_COLOR,
                                 (c * TILE_SIZE - WALL_THICKNESS // 2, r * TILE_SIZE + y_offset,
                                  WALL_THICKNESS, TILE_SIZE))

    pygame.draw.rect(screen, WALL_COLOR, (0, y_offset, WIDTH, WALL_THICKNESS))
    pygame.draw.rect(screen, WALL_COLOR, (0, HEIGHT - WALL_THICKNESS, WIDTH, WALL_THICKNESS))
    pygame.draw.rect(screen, WALL_COLOR, (0, y_offset, WALL_THICKNESS, HEIGHT - y_offset))
    pygame.draw.rect(screen, WALL_COLOR, (WIDTH - WALL_THICKNESS, 0, WALL_THICKNESS, HEIGHT - y_offset))

    shadow_offset = 5
    shadow_padding = 4

    exit_shadow_rect = pygame.Rect(current_exit_pos[1] * TILE_SIZE + shadow_offset,
                                   current_exit_pos[0] * TILE_SIZE + y_offset + shadow_offset,
                                   TILE_SIZE, TILE_SIZE)
    pygame.draw.rect(screen, SHADOW_COLOR, exit_shadow_rect.inflate(shadow_padding * 2, shadow_padding * 2))

    player_shadow_center = (player[1] * TILE_SIZE + TILE_SIZE // 2 + shadow_offset,
                            player[0] * TILE_SIZE + y_offset + TILE_SIZE // 2 + shadow_offset)
    pygame.draw.circle(screen, SHADOW_COLOR, player_shadow_center, TILE_SIZE // 2)

    enemy_shadow_rect = pygame.Rect(enemy[1] * TILE_SIZE + shadow_offset,
                                    enemy[0] * TILE_SIZE + y_offset + shadow_offset,
                                    TILE_SIZE, TILE_SIZE)
    pygame.draw.rect(screen, SHADOW_COLOR, enemy_shadow_rect.inflate(shadow_padding * 2, shadow_padding * 2))

    object_padding = 8

    exit_rect = pygame.Rect(current_exit_pos[1] * TILE_SIZE, current_exit_pos[0] * TILE_SIZE + y_offset, TILE_SIZE,
                            TILE_SIZE)
    pygame.draw.rect(screen, EXIT_COLOR, exit_rect.inflate(-object_padding * 2, -object_padding * 2))

    pygame.draw.circle(screen, PLAYER_COLOR,
                       (player[1] * TILE_SIZE + TILE_SIZE // 2, player[0] * TILE_SIZE + y_offset + TILE_SIZE // 2),
                       TILE_SIZE // 2 - object_padding)

    enemy_rect = pygame.Rect(enemy[1] * TILE_SIZE, enemy[0] * TILE_SIZE + y_offset, TILE_SIZE, TILE_SIZE)
    pygame.draw.rect(screen, ENEMY_COLOR, enemy_rect.inflate(-object_padding * 2, -object_padding * 2))

    hud_panel_height = 45
    hud_panel_width = WIDTH - WALL_THICKNESS * 4
    hud_panel_x = (WIDTH - hud_panel_width) // 2
    hud_panel_y = (HUD_HEIGHT_BUFFER - hud_panel_height) // 2
    hud_panel_rect = pygame.Rect(hud_panel_x, hud_panel_y, hud_panel_width, hud_panel_height)

    current_hud_panel_color = (200, 200, 200)
    if enemy_current_state == CHASE:
        current_hud_panel_color = CHASE_HUD_COLOR
    elif enemy_current_state == SEARCH:
        current_hud_panel_color = SEARCH_HUD_COLOR
    elif enemy_current_state == PATROL:
        current_hud_panel_color = PATROL_HUD_COLOR

    hud_shadow_offset_val = 5
    hud_shadow_rect = hud_panel_rect.copy()
    hud_shadow_rect.x += hud_shadow_offset_val
    hud_shadow_rect.y += hud_shadow_offset_val
    pygame.draw.rect(screen, SHADOW_COLOR, hud_shadow_rect, border_radius=10)

    hud_panel_surface = pygame.Surface(hud_panel_rect.size, pygame.SRCALPHA)
    hud_panel_surface.fill((0, 0, 0, 0))

    pygame.draw.rect(hud_panel_surface, current_hud_panel_color, hud_panel_surface.get_rect(), border_radius=10)

    screen.blit(hud_panel_surface, hud_panel_rect.topleft)

    try:
        font = pygame.font.SysFont('Arial', 24, bold=True)
    except:
        font = pygame.font.Font(None, 30)

    text_surface = font.render(f"Enemy State: {enemy_current_state}", True, HUD_TEXT_COLOR)

    text_x = hud_panel_rect.left + (hud_panel_rect.width - text_surface.get_width()) // 2
    text_y = hud_panel_rect.top + (hud_panel_rect.height - text_surface.get_height()) // 2
    screen.blit(text_surface, (text_x, text_y))

    pygame.display.flip()


def draw_message_screen(message, sub_message, background_color):
    overlay_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay_surface.fill(background_color + (180,))
    screen.blit(overlay_surface, (0, 0))

    try:
        main_font = pygame.font.SysFont('Arial', 60, bold=True)
    except:
        main_font = pygame.font.Font(None, 70)

    main_text_surface = main_font.render(message, True, MESSAGE_TEXT_COLOR)
    main_text_rect = main_text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
    screen.blit(main_text_surface, main_text_rect)

    try:
        sub_font = pygame.font.SysFont('Arial', 24)
    except:
        sub_font = pygame.font.Font(None, 30)

    sub_text_surface = sub_font.render(sub_message, True, MESSAGE_TEXT_COLOR)
    sub_text_rect = sub_text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
    screen.blit(sub_text_surface, sub_text_rect)

    pygame.display.flip()


# ========== MEMBER 4: The Villain's Actor
def has_line_of_sight(maze_graph, p1, p2):
    if p1[0] == p2[0]:
        for col in range(min(p1[1], p2[1]), max(p1[1], p2[1])):
            if not maze_graph.has_edge((p1[0], col), (p1[0], col + 1)):
                return False
        return True
    elif p1[1] == p2[1]:
        for row in range(min(p1[0], p2[0]), max(p1[0], p2[0])):
            if not maze_graph.has_edge((row, p1[1]), (row + 1, p1[1])):
                return False
        return True

    try:
        path_to_player = astar(maze_graph, p1, p2)
        if 0 < len(path_to_player) <= 4:
            return True
    except nx.NetworkXNoPath:
        pass

    return False


# ========== MEMBER 5: The Director
running = True

while running:
    current_time = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == "RUNNING":
            if event.type == pygame.KEYDOWN:
                new_player_pos = player_pos
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    new_player_pos = (player_pos[0] - 1, player_pos[1])
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    new_player_pos = (player_pos[0] + 1, player_pos[1])
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    new_player_pos = (player_pos[0], player_pos[1] - 1)
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    new_player_pos = (player_pos[0], player_pos[1] + 1)

                if 0 <= new_player_pos[0] < ROWS and \
                        0 <= new_player_pos[1] < COLS and \
                        new_player_pos in maze.neighbors(player_pos):
                    player_pos = new_player_pos
        else:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_game()
                elif event.key == pygame.K_q:
                    running = False

    if game_state == "RUNNING":
        # ========== MEMBER 4: The Villain's Actor
        player_in_los = has_line_of_sight(maze, enemy_pos, player_pos)

        if player_in_los:
            enemy_state = CHASE
            last_known_player_pos = player_pos
            enemy_stuck_frames = 0
        elif enemy_state == CHASE and not player_in_los:
            enemy_state = SEARCH
            enemy_stuck_frames = 0
        elif enemy_state == SEARCH and enemy_pos == last_known_player_pos:
            enemy_state = PATROL
            last_known_player_pos = None
            enemy_stuck_frames = 0
        elif enemy_state == SEARCH and last_known_player_pos is None:
            enemy_state = PATROL
            enemy_stuck_frames = 0

        if current_time - last_enemy_move_time > ENEMY_MOVE_DELAY:
            is_stuck_in_logic = False
            if (enemy_state == CHASE and enemy_pos != player_pos) or \
                    (
                            enemy_state == SEARCH and enemy_pos != last_known_player_pos and last_known_player_pos is not None):
                if not chase_path and enemy_stuck_frames < STUCK_THRESHOLD:
                    enemy_stuck_frames += 1
                if enemy_stuck_frames >= STUCK_THRESHOLD:
                    is_stuck_in_logic = True
                    enemy_state = PATROL
                    enemy_stuck_frames = 0
                    chase_path = []

            if not is_stuck_in_logic:
                if enemy_state == CHASE:
                    try:
                        chase_path = astar(maze, enemy_pos, player_pos)
                        if chase_path:
                            enemy_stuck_frames = 0
                    except nx.NetworkXNoPath:
                        chase_path = []
                        enemy_state = PATROL

                    if chase_path:
                        enemy_pos = chase_path.pop(0)
                        last_enemy_move_time = current_time
                    else:
                        if enemy_pos != player_pos:
                            enemy_state = PATROL
                            chase_path = []

                elif enemy_state == SEARCH:
                    if last_known_player_pos and enemy_pos != last_known_player_pos:
                        try:
                            chase_path = astar(maze, enemy_pos, last_known_player_pos)
                            if chase_path:
                                enemy_stuck_frames = 0
                        except nx.NetworkXNoPath:
                            chase_path = []
                            enemy_state = PATROL
                            last_known_player_pos = None

                        if chase_path:
                            enemy_pos = chase_path.pop(0)
                            last_enemy_move_time = current_time
                        else:
                            enemy_state = PATROL
                            last_known_player_pos = None
                    else:
                        enemy_state = PATROL
                        last_known_player_pos = None

                elif enemy_state == PATROL:
                    visited_cells_tracker[enemy_pos] = current_time

                    valid_neighbors = list(maze.neighbors(enemy_pos))
                    if not valid_neighbors:
                        last_enemy_move_time = current_time
                    else:
                        desirability_scores = []
                        for neighbor in valid_neighbors:
                            last_visit_time = visited_cells_tracker.get(neighbor, 0)
                            score = (current_time - last_visit_time) + 1
                            desirability_scores.append(score)

                        total_score = sum(desirability_scores)
                        if total_score > 0:
                            probabilities = [score / total_score for score in desirability_scores]
                            next_patrol_step = random.choices(valid_neighbors, weights=probabilities, k=1)[0]
                        else:
                            next_patrol_step = random.choice(valid_neighbors)

                        enemy_pos = next_patrol_step
                        last_enemy_move_time = current_time
                        enemy_stuck_frames = 0
            else:
                valid_neighbors = list(maze.neighbors(enemy_pos))
                if valid_neighbors:
                    enemy_pos = random.choice(valid_neighbors)
                    last_enemy_move_time = current_time
                    enemy_stuck_frames = max(0, enemy_stuck_frames - STUCK_UNSTUCK_MOVES)

        # ========== MEMBER 5: The Director
        draw(maze, player_pos, enemy_pos, exit_pos, enemy_state)

        if player_pos == exit_pos:
            game_state = "WIN"
            print("You Win! You escaped the maze!")
        elif player_pos == enemy_pos:
            game_state = "LOSE"
            print("Caught by Enemy! Game Over!")

    else:
        # ========== MEMBER 5: The Director
        if game_state == "WIN":
            draw_message_screen("YOU WIN!", "Press 'R' to Restart or 'Q' to Quit", WIN_SCREEN_COLOR)
        elif game_state == "LOSE":
            draw_message_screen("GAME OVER!", "Press 'R' to Restart or 'Q' to Quit", LOSE_SCREEN_COLOR)

    clock.tick(FPS)

pygame.quit()