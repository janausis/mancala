# mancala_pygame.py
import time
from typing import List

# ----------------------------
# Corrected Mancala game logic
# ----------------------------
class Mancala:
    def __init__(self, stones_per_pit: int = 4, pits_per_player: int = 6):
        # Layout: [P0 pits (0..p-1)], [P0 house], [P1 pits (p+1 .. 2p)], [P1 house]
        self.pits = pits_per_player
        self.board = [stones_per_pit] * pits_per_player + [0] + [stones_per_pit] * pits_per_player + [0]
        self.current_player = 0  # 0 = Player 1 (bottom), 1 = Player 2 (top)
        self.player0_house = pits_per_player
        self.player1_house = 2 * pits_per_player + 1
        self.size = len(self.board)

    def legal_moves(self) -> List[int]:
        if self.current_player == 0:
            return [i for i in range(0, self.player0_house) if self.board[i] > 0]
        else:
            return [i for i in range(self.player0_house + 1, self.player1_house) if self.board[i] > 0]

    def make_move(self, pit_index: int, animate_callback=None, anim_delay: float = 0.3) -> bool:
        if pit_index not in self.legal_moves():
            raise ValueError("Invalid move")
        stones = self.board[pit_index]
        self.board[pit_index] = 0
        idx = pit_index

        # Sow stones, skipping opponent's house (standard Kalah)
        while stones > 0:
            idx = (idx + 1) % self.size
            # skip opponent's house
            if self.current_player == 0 and idx == self.player1_house:
                continue
            if self.current_player == 1 and idx == self.player0_house:
                continue
            self.board[idx] += 1
            stones -= 1
            if animate_callback:
                animate_callback(self.board, idx)
                time.sleep(anim_delay)

        # Last stone rules: extra turn or capture
        extra_turn = False
        if self.current_player == 0 and idx == self.player0_house:
            extra_turn = True
        elif self.current_player == 1 and idx == self.player1_house:
            extra_turn = True
        else:
            # capture if last stone landed in an empty pit on player's side
            if self.current_player == 0 and 0 <= idx <= self.player0_house - 1 and self.board[idx] == 1:
                opposite_idx = self.player1_house - 1 - idx
                captured = self.board[opposite_idx]
                if captured > 0:
                    self.board[self.player0_house] += captured + 1
                    self.board[idx] = 0
                    self.board[opposite_idx] = 0
            elif self.current_player == 1 and self.player0_house + 1 <= idx <= self.player1_house - 1 and self.board[idx] == 1:
                opposite_idx = self.player1_house - 1 - idx
                captured = self.board[opposite_idx]
                if captured > 0:
                    self.board[self.player1_house] += captured + 1
                    self.board[idx] = 0
                    self.board[opposite_idx] = 0

        if not extra_turn:
            self.current_player = 1 - self.current_player

        return self.check_game_over()

    def check_game_over(self) -> bool:
        side1_empty = all(self.board[i] == 0 for i in range(0, self.player0_house))
        side2_empty = all(self.board[i] == 0 for i in range(self.player0_house + 1, self.player1_house))

        if side1_empty or side2_empty:
            # collect remaining stones
            self.board[self.player0_house] += sum(self.board[i] for i in range(0, self.player0_house))
            self.board[self.player1_house] += sum(self.board[i] for i in range(self.player0_house + 1, self.player1_house))
            for i in range(0, self.player0_house):
                self.board[i] = 0
            for i in range(self.player0_house + 1, self.player1_house):
                self.board[i] = 0
            return True
        return False

    def get_winner(self) -> int:
        if not self.check_game_over():
            raise ValueError("Game is not over yet")
        if self.board[self.player0_house] > self.board[self.player1_house]:
            return 0
        elif self.board[self.player1_house] > self.board[self.player0_house]:
            return 1
        else:
            return -1

