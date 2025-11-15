import enum
from typing import List, Optional, Dict, Tuple
import threading
import queue
import sys

import pygame

from mancala.mancala import Mancala
from algorithm.alpha_beta_pruning import choose_best_move, clone_state


# ----------------------------
# COLORS / CONFIG
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
EXTRA_TURN_DURATION = 1000   # ms
STEAL_DURATION = 1000        # ms


class PlayMode(enum.Enum):
    HUMAN_VS_HUMAN = "HUMAN_VS_HUMAN"
    HUMAN_VS_AI = "HUMAN_VS_AI"
    AI_VS_AI = "AI_VS_AI"


class MancalaUI:
    """Encapsulates Pygame UI and animation logic for Mancala."""

    def __init__(
        self,
        play_mode: PlayMode = PlayMode.AI_VS_AI,
        abp_depth: int = 8,
        width: int = 830,
        height: int = 500,
    ):
        # config
        self.play_mode = play_mode
        self.abp_depth = abp_depth

        # Pygame initialization
        pygame.init()
        self.font = pygame.font.SysFont(None, 26)
        self.big_font = pygame.font.SysFont(None, 36)

        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()

        # layout
        self.pit_radius = 36
        self.house_w, self.house_h = 90, 160
        self.margin = 20
        self.board_top = int((self.height - self.house_h) / 2)

        # animation / runtime state (instance-scoped)
        self.pit_flash: Dict[int, dict] = {}
        self.extra_turn_start: Optional[int] = None
        self.steal_start: Optional[int] = None
        self.animating: bool = False

        # queue for frames/events produced by background workers
        self.anim_queue: "queue.Queue[Tuple]" = queue.Queue()
        self.state_lock = threading.Lock()

    # ---- small helpers ----
    def flash_pit(self, idx: int, gain: bool = True) -> None:
        """Trigger a flash animation for a pit index."""
        self.pit_flash[idx] = {"start": pygame.time.get_ticks(), "type": "gain" if gain else "loss"}

    def _render_flash_color(self, base: Tuple[int, int, int], idx: int, now: int) -> Optional[Tuple[int, int, int]]:
        info = self.pit_flash.get(idx)
        if not info:
            return None
        t = now - info["start"]
        if t > FLASH_DURATION:
            self.pit_flash.pop(idx, None)
            return None
        fade = 1 - (t / FLASH_DURATION)
        fc = COL_STEAL_GAIN if info["type"] == "gain" else COL_STEAL_LOSS
        return (
            int(base[0] + (fc[0] - base[0]) * fade),
            int(base[1] + (fc[1] - base[1]) * fade),
            int(base[2] + (fc[2] - base[2]) * fade),
        )

    def draw_board(
        self,
        state: Mancala,
        highlight: Optional[List[int]] = None,
        board_snapshot: Optional[List[int]] = None,
        current_player_override: Optional[int] = None,
    ) -> Tuple[Dict[int, pygame.Rect], pygame.Rect]:
        """Draw the board and return interactive pit rects and the reset rect.

        `board_snapshot` can be passed to render an intermediate animation frame.
        """
        if highlight is None:
            highlight = []

        now = pygame.time.get_ticks()
        self.screen.fill(COL_BG)

        board = board_snapshot if board_snapshot is not None else state.board
        curr = current_player_override if current_player_override is not None else state.current_player

        # header
        turn_col = COL_P0_ACTIVE if curr == 0 else COL_P1_ACTIVE
        self.screen.blit(self.big_font.render("Mancala (Kalah rules)", True, COL_TEXT), (20, 10))
        self.screen.blit(self.font.render(f"Turn: Player {curr + 1}", True, turn_col), (350, 12))

        p = state.pits
        top_y = self.board_top
        bottom_y = self.board_top + self.house_h - 40
        start_x = self.margin + self.house_w + 40 + self.pit_radius

        # houses
        left_house = pygame.Rect(self.margin, self.board_top, self.house_w, self.house_h)
        right_house = pygame.Rect(start_x + p * (self.pit_radius * 2 + 20) - 20, self.board_top, self.house_w, self.house_h)

        pygame.draw.rect(self.screen, COL_P1_ACTIVE, left_house, border_radius=12)
        pygame.draw.rect(self.screen, COL_P0_ACTIVE, right_house, border_radius=12)

        left_count = str(board[state.player1_house])
        right_count = str(board[state.player0_house])

        self.screen.blit(self.big_font.render(left_count, True, COL_WHITE), (left_house.centerx - 12, left_house.centery - 18))
        self.screen.blit(self.big_font.render(right_count, True, COL_WHITE), (right_house.centerx - 12, right_house.centery - 18))

        self.screen.blit(self.font.render("House P2", True, COL_TEXT), (left_house.x + 8, left_house.y + self.house_h - 26))
        self.screen.blit(self.font.render("House P1", True, COL_TEXT), (right_house.x + 8, right_house.y + self.house_h - 26))

        pit_positions: Dict[int, Tuple[int, int]] = {}

        # top row (player 1 pits visually)
        for i in range(p):
            idx = state.player1_house - 1 - i
            x = start_x + i * (self.pit_radius * 2 + 20)
            y = top_y + 12
            pit_positions[idx] = (x, y)

            base = COL_P1_ACTIVE if curr == 1 else COL_P1_INACTIVE
            flash_col = self._render_flash_color(base, idx, now)
            color = flash_col if flash_col else (COL_HIGHLIGHT if idx in highlight else base)

            pygame.draw.circle(self.screen, color, (x, y), self.pit_radius)
            self.screen.blit(self.font.render(str(board[idx]), True, COL_WHITE), (x - 8, y - 10))

        # bottom row (player 0 pits)
        for i in range(p):
            idx = i
            x = start_x + i * (self.pit_radius * 2 + 20)
            y = bottom_y + 40
            pit_positions[idx] = (x, y)

            base = COL_P0_ACTIVE if curr == 0 else COL_P0_INACTIVE
            flash_col = self._render_flash_color(base, idx, now)
            color = flash_col if flash_col else (COL_HIGHLIGHT if idx in highlight else base)

            pygame.draw.circle(self.screen, color, (x, y), self.pit_radius)
            self.screen.blit(self.font.render(str(board[idx]), True, COL_WHITE), (x - 8, y - 10))

        # interactive rects
        interactive: Dict[int, pygame.Rect] = {}
        for idx, (x, y) in pit_positions.items():
            r = pygame.Rect(x - self.pit_radius, y - self.pit_radius, self.pit_radius * 2, self.pit_radius * 2)
            pygame.draw.circle(self.screen, COL_BORDER, (x, y), self.pit_radius, 2)
            interactive[idx] = r

        # reset button
        reset_rect = pygame.Rect(self.width - 140, self.height - 48, 120, 36)
        pygame.draw.rect(self.screen, COL_RESET, reset_rect, border_radius=8)
        self.screen.blit(self.font.render("Reset", True, COL_WHITE), (reset_rect.x + 34, reset_rect.y + 8))

        # extra turn animation
        if self.extra_turn_start is not None:
            elapsed = now - self.extra_turn_start
            if elapsed > EXTRA_TURN_DURATION:
                self.extra_turn_start = None
            else:
                n = elapsed / EXTRA_TURN_DURATION
                if n < 0.35:
                    scale = n / 0.35
                else:
                    scale = max(0.0, 1 - (n - 0.35) / 0.65)
                size = int(20 + 60 * scale)
                font = pygame.font.SysFont(None, size)
                surf = font.render("Extra Turn!", True, (255, 230, 90))
                rect = surf.get_rect(center=(self.width // 2, self.height // 2))
                self.screen.blit(surf, rect)

        # steal animation
        if self.steal_start is not None:
            elapsed = now - self.steal_start
            if elapsed > STEAL_DURATION:
                self.steal_start = None
            else:
                n = elapsed / STEAL_DURATION
                if n < 0.35:
                    scale = n / 0.35
                else:
                    scale = max(0.0, 1 - (n - 0.35) / 0.65)
                size = int(22 + 70 * scale)
                font = pygame.font.SysFont(None, size)
                surf = font.render("Steal!", True, (180, 30, 30))
                rect = surf.get_rect(center=(self.width // 2, self.height // 2))
                self.screen.blit(surf, rect)

        return interactive, reset_rect

    def make_move_async(self, state: Mancala, clicked: Optional[int] = None, is_ai: bool = False, anim_delay: float = 0.3) -> None:
        """Run a move in a background thread and enqueue animation frames/events."""
        if self.animating:
            return
        self.animating = True

        def worker(move_to_play: Optional[int]):
            before_player = state.current_player
            before_board = state.board.copy()

            if is_ai and move_to_play is None:
                cloned = clone_state(state)
                move = choose_best_move(cloned, depth=self.abp_depth)
            else:
                move = move_to_play

            def worker_anim_callback(board_snapshot, last_idx):
                self.anim_queue.put(("frame", board_snapshot.copy(), last_idx))

            state.make_move(move, animate_callback=worker_anim_callback, anim_delay=anim_delay)

            after_board = state.board.copy()
            after_player = state.current_player

            self.anim_queue.put(("done", before_player, before_board, after_board, after_player))

        t = threading.Thread(target=worker, args=(clicked,), daemon=True)
        t.start()

    def run(self) -> None:
        """Main loop. Call to start the UI (blocks)."""
        state = Mancala()
        running = True

        last_board = state.board.copy()

        while running:
            self.clock.tick(120)

            # process animation queue
            while not self.anim_queue.empty():
                item = self.anim_queue.get()
                if item[0] == "frame":
                    _, board_snapshot, _last_idx = item
                    for i in range(len(last_board)):
                        if last_board[i] != board_snapshot[i] and board_snapshot[i] > last_board[i]:
                            self.flash_pit(i, gain=True)
                    last_board = board_snapshot.copy()
                    self.draw_board(state, board_snapshot=board_snapshot)
                    pygame.display.flip()

                elif item[0] == "done":
                    _, before_player, before_board, after_board, after_player = item

                    stolen_pits = []
                    if before_player == 0:
                        my_house = state.player0_house
                        opp_range = range(state.player0_house + 1, state.player1_house)
                    else:
                        my_house = state.player1_house
                        opp_range = range(0, state.player0_house)

                    if after_board[my_house] > before_board[my_house]:
                        for opp in opp_range:
                            if before_board[opp] != 0 and after_board[opp] == 0:
                                stolen_pits.append(opp)

                    if stolen_pits:
                        for opp in stolen_pits:
                            self.flash_pit(opp, gain=False)
                        self.steal_start = pygame.time.get_ticks()

                    if before_player == after_player:
                        self.extra_turn_start = pygame.time.get_ticks()

                    self.animating = False

            # regular draw
            interactive, reset_rect = self.draw_board(state)

            mx, my = pygame.mouse.get_pos()
            hovered = None
            for idx, rect in interactive.items():
                if rect.collidepoint((mx, my)):
                    hovered = idx

            if hovered is not None:
                self.draw_board(state, highlight=[hovered])

            if state.check_game_over():
                w = state.get_winner()
                msg = "Draw!" if w == -1 else f"Player {w+1} wins!"
                self.screen.blit(self.big_font.render(msg, True, COL_WHITE), (360, self.height // 2 - 20))

            pygame.display.flip()

            # event loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

                if reset_rect.collidepoint((mx, my)) and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.animating:
                    state = Mancala()
                    last_board = state.board.copy()
                    self.extra_turn_start = None
                    continue

                if (
                    self.play_mode == PlayMode.HUMAN_VS_HUMAN
                    or (self.play_mode == PlayMode.HUMAN_VS_AI and state.current_player == 0)
                ) and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.animating:
                    mx, my = event.pos
                    clicked = None
                    for idx, rect in interactive.items():
                        if rect.collidepoint((mx, my)):
                            clicked = idx
                            break

                    if clicked is not None and clicked in state.legal_moves():
                        self.make_move_async(state, clicked, is_ai=False)

            # AI moves
            if not state.check_game_over():
                if self.play_mode == PlayMode.HUMAN_VS_AI:
                    if not self.animating and state.current_player == 1:
                        self.make_move_async(state, clicked=None, is_ai=True)

                if self.play_mode == PlayMode.AI_VS_AI:
                    if not self.animating:
                        self.make_move_async(state, clicked=None, is_ai=True)

        pygame.quit()
        sys.exit()


# simple runner convenience
def run(play_mode: PlayMode = PlayMode.HUMAN_VS_AI, abp_depth: int = 5) -> None:
    ui = MancalaUI(play_mode=play_mode, abp_depth=abp_depth)
    ui.run()


if __name__ == "__main__":
    run()
