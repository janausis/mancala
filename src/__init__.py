from time import sleep
from typing import List, Optional, Dict
import pygame
import sys
from mancala.mancala import Mancala

# ----------------------------
# COLORS
# ----------------------------
COL_BG = (30, 30, 40)
COL_TEXT = (230, 230, 230)

COL_P0_ACTIVE = (220, 0, 0)
COL_P1_ACTIVE = (0, 0, 230)
COL_P0_INACTIVE = (220, 150, 150)
COL_P1_INACTIVE = (150, 150, 230)

COL_STEAL_GAIN = (50, 220, 80)   # green flash
COL_STEAL_LOSS = (220, 80, 60)   # red flash

COL_HIGHLIGHT = (70, 70, 70)
COL_BORDER = (20, 20, 20)

COL_RESET = (80, 40, 60)
COL_WHITE = (255, 255, 255)

# ----------------------------
# ANIMATION SETTINGS
# ----------------------------
FLASH_DURATION = 1000        # ms for pit flashes
EXTRA_TURN_DURATION = 1000  # ms for extra turn text
STEAL_DURATION = 1000  # ms

# ----------------------------
# Pygame UI
# ----------------------------
pygame.init()
FONT = pygame.font.SysFont(None, 26)
BIG = pygame.font.SysFont(None, 36)

WIDTH, HEIGHT = 900, 500
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
CLOCK = pygame.time.Clock()

PIT_RADIUS = 36
HOUSE_W, HOUSE_H = 90, 160
MARGIN = 20
BOARD_TOP = (HEIGHT - HOUSE_H) / 2

# ----------------------------
# Animation state
# ----------------------------
pit_flash: Dict[int, dict] = {}   # {idx: {"start":ms, "type":"gain"/"loss"}}
EXTRA_TURN_START = None
STEAL_START = None


def flash_pit(idx: int, gain=True):
    """Trigger a flash animation for a pit."""
    pit_flash[idx] = {
        "start": pygame.time.get_ticks(),
        "type": "gain" if gain else "loss"
    }


def draw_board(state: Mancala, highlight: Optional[List[int]] = None):
    if highlight is None:
        highlight = []

    now = pygame.time.get_ticks()

    SCREEN.fill(COL_BG)

    # --- Title & turn text ---
    turn_col = COL_P0_ACTIVE if state.current_player == 0 else COL_P1_ACTIVE
    SCREEN.blit(BIG.render("Mancala (Kalah rules)", True, COL_TEXT), (20, 10))
    SCREEN.blit(FONT.render(f"Turn: Player {state.current_player + 1}", True, turn_col), (350, 12))

    p = state.pits
    top_y = BOARD_TOP
    bottom_y = BOARD_TOP + HOUSE_H - 40
    start_x = MARGIN + HOUSE_W + 40 + PIT_RADIUS

    # --- Houses ---
    left_house_rect = pygame.Rect(MARGIN, BOARD_TOP, HOUSE_W, HOUSE_H)
    right_house_rect = pygame.Rect(start_x + p * (PIT_RADIUS * 2 + 20) - 20, BOARD_TOP, HOUSE_W, HOUSE_H)

    pygame.draw.rect(SCREEN, COL_P1_ACTIVE, left_house_rect, border_radius=12)
    pygame.draw.rect(SCREEN, COL_P0_ACTIVE, right_house_rect, border_radius=12)

    left_count = str(state.board[state.player1_house])
    right_count = str(state.board[state.player0_house])

    SCREEN.blit(BIG.render(left_count, True, COL_WHITE), (left_house_rect.centerx - 12, left_house_rect.centery - 18))
    SCREEN.blit(BIG.render(right_count, True, COL_WHITE), (right_house_rect.centerx - 12, right_house_rect.centery - 18))

    SCREEN.blit(FONT.render("House P2", True, COL_TEXT), (left_house_rect.x + 8, left_house_rect.y + HOUSE_H - 26))
    SCREEN.blit(FONT.render("House P1", True, COL_TEXT), (right_house_rect.x + 8, right_house_rect.y + HOUSE_H - 26))

    pit_positions = {}

    # ----------------------------
    # Top row (Player 2 pits)
    # ----------------------------
    for i in range(p):
        idx = state.player1_house - 1 - i
        x = start_x + i * (PIT_RADIUS * 2 + 20)
        y = top_y + 12
        pit_positions[idx] = (x, y)

        base = COL_P1_ACTIVE if state.current_player == 1 else COL_P1_INACTIVE

        # Apply flash?
        flash_col = None
        if idx in pit_flash:
            t = now - pit_flash[idx]["start"]
            if t > FLASH_DURATION:
                pit_flash.pop(idx, None)
            else:
                fade = 1 - (t / FLASH_DURATION)
                if pit_flash[idx]["type"] == "gain":
                    fc = COL_STEAL_GAIN
                else:
                    fc = COL_STEAL_LOSS
                flash_col = (
                    base[0] + (fc[0] - base[0]) * fade,
                    base[1] + (fc[1] - base[1]) * fade,
                    base[2] + (fc[2] - base[2]) * fade,
                )

        color = flash_col if flash_col else (COL_HIGHLIGHT if idx in highlight else base)
        pygame.draw.circle(SCREEN, color, (x, y), PIT_RADIUS)
        SCREEN.blit(FONT.render(str(state.board[idx]), True, COL_WHITE), (x - 8, y - 10))

    # ----------------------------
    # Bottom row (Player 1 pits)
    # ----------------------------
    for i in range(p):
        idx = i
        x = start_x + i * (PIT_RADIUS * 2 + 20)
        y = bottom_y + 40
        pit_positions[idx] = (x, y)

        base = COL_P0_ACTIVE if state.current_player == 0 else COL_P0_INACTIVE

        flash_col = None
        if idx in pit_flash:
            t = now - pit_flash[idx]["start"]
            if t > FLASH_DURATION:
                pit_flash.pop(idx, None)
            else:
                fade = 1 - (t / FLASH_DURATION)
                fc = COL_STEAL_GAIN if pit_flash[idx]["type"] == "gain" else COL_STEAL_LOSS
                flash_col = (
                    base[0] + (fc[0] - base[0]) * fade,
                    base[1] + (fc[1] - base[1]) * fade,
                    base[2] + (fc[2] - base[2]) * fade,
                )

        color = flash_col if flash_col else (COL_HIGHLIGHT if idx in highlight else base)
        pygame.draw.circle(SCREEN, color, (x, y), PIT_RADIUS)
        SCREEN.blit(FONT.render(str(state.board[idx]), True, COL_WHITE), (x - 8, y - 10))

    # Borders / clickable regions
    interactive = {}
    for idx, (x, y) in pit_positions.items():
        r = pygame.Rect(x - PIT_RADIUS, y - PIT_RADIUS, PIT_RADIUS * 2, PIT_RADIUS * 2)
        pygame.draw.circle(SCREEN, COL_BORDER, (x, y), PIT_RADIUS, 2)
        interactive[idx] = r

    # Reset button
    reset_rect = pygame.Rect(WIDTH - 140, HEIGHT - 48, 120, 36)
    pygame.draw.rect(SCREEN, COL_RESET, reset_rect, border_radius=8)
    SCREEN.blit(FONT.render("Reset", True, COL_WHITE), (reset_rect.x + 34, reset_rect.y + 8))

    # ----------------------------
    # EXTRA TURN ANIMATION
    # ----------------------------
    global EXTRA_TURN_START
    if EXTRA_TURN_START is not None:
        elapsed = now - EXTRA_TURN_START
        if elapsed > EXTRA_TURN_DURATION:
            EXTRA_TURN_START = None
        else:
            n = elapsed / EXTRA_TURN_DURATION

            # grow → shrink easing
            if n < 0.35:
                scale = n / 0.35
            else:
                scale = max(0, 1 - (n - 0.35) / 0.65)

            size = int(20 + 60 * scale)
            font = pygame.font.SysFont(None, size)

            surf = font.render("Extra Turn!", True, (255, 230, 90))
            rect = surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            SCREEN.blit(surf, rect)

    # ----------------------------
    # STEAL ANIMATION
    # ----------------------------
    global STEAL_START
    if STEAL_START is not None:
        elapsed = now - STEAL_START
        if elapsed > STEAL_DURATION:
            STEAL_START = None
        else:
            n = elapsed / STEAL_DURATION

            # grow then shrink, same as extra turn
            if n < 0.35:
                scale = n / 0.35
            else:
                scale = max(0, 1 - (n - 0.35) / 0.65)

            size = int(22 + 70 * scale)
            font = pygame.font.SysFont(None, size)

            surf = font.render("Steal!", True, (180, 30, 30))
            rect = surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            SCREEN.blit(surf, rect)

    return interactive, reset_rect


# ================================================================
# MAIN LOOP
# ================================================================
def main():
    global EXTRA_TURN_START
    state = Mancala()
    running = True
    animating = False

    # Snapshot board to track flashes
    last_board = state.board.copy()

    def animate_callback(board_snapshot, last_idx):
        nonlocal last_board

        # detect which pits changed this frame
        for i in range(len(last_board)):
            if last_board[i] != board_snapshot[i]:
                gain = board_snapshot[i] > last_board[i]
                flash_pit(i, gain=gain)

        last_board = board_snapshot.copy()

        draw_board(state)
        pygame.display.flip()

    while running:
        CLOCK.tick(60)
        interactive, reset_rect = draw_board(state)

        mx, my = pygame.mouse.get_pos()
        hovered = None
        for idx, rect in interactive.items():
            if rect.collidepoint((mx, my)):
                hovered = idx

        if hovered is not None:
            draw_board(state, highlight=[hovered])

        # GAME OVER
        if state.check_game_over():
            w = state.get_winner()
            msg = "Draw!" if w == -1 else f"Player {w+1} wins!"
            SCREEN.blit(BIG.render(msg, True, COL_WHITE), (360, HEIGHT // 2 - 20))

        pygame.display.flip()

        # EVENT LOOP
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not animating:
                mx, my = event.pos

                if reset_rect.collidepoint((mx, my)):
                    state = Mancala()
                    last_board = state.board.copy()
                    EXTRA_TURN_START = None
                    continue

                clicked = None
                for idx, rect in interactive.items():
                    if rect.collidepoint((mx, my)):
                        clicked = idx
                        break

                if clicked is not None and clicked in state.legal_moves():
                    animating = True

                    before_player = state.current_player
                    before_board = state.board.copy()

                    state.make_move(clicked, animate_callback=animate_callback, anim_delay=0.2)
                    # --- final capture flash detection (after move finishes) ---
                    steal_happened = False

                    # Detect steal: your house increases AND opposite pit goes to 0
                    # Use the player who made the move (before_player) and compare against before_board
                    if before_player == 0:
                        my_house = state.player0_house
                        opp_range = range(state.player0_house + 1, state.player1_house)  # opponent pits
                    else:
                        my_house = state.player1_house
                        opp_range = range(0, state.player0_house)

                    # If our house increased compared to the board before the move, and any opponent pit
                    # that previously had stones is now 0, we consider it a steal.
                    if state.board[my_house] > before_board[my_house]:
                        for opp in opp_range:
                            if before_board[opp] != 0 and state.board[opp] == 0:
                                steal_happened = True
                                break

                    if steal_happened:
                        global STEAL_START
                        STEAL_START = pygame.time.get_ticks()

                    last_board = state.board.copy()

                    after_player = state.current_player
                    # Detect extra turn
                    if before_player == after_player:
                        EXTRA_TURN_START = pygame.time.get_ticks()

                    animating = False

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
