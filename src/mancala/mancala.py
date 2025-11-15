"""Core Mancala (Kalah) game logic.

Provides a small, self-contained `Mancala` class that models the board
and rules used by the UI and the AI search code.
"""
from typing import List, Optional, Callable
import time


class Mancala:
    """Simple Kalah (Mancala) implementation.

    Board layout (for pits_per_player == p):
      indices:  0 .. p-1         p      p+1 .. 2p      2p+1
                P0 pits      P0 house    P1 pits     P1 house

    Player 0 (bottom) controls pits 0..p-1 and house at index p.
    Player 1 (top) controls pits p+1..2p and house at index 2p+1.
    """

    def __init__(self, stones_per_pit: int = 4, pits_per_player: int = 6):
        self.pits = pits_per_player
        self.board: List[int] = [stones_per_pit] * pits_per_player + [0] + [stones_per_pit] * pits_per_player + [0]
        self.current_player: int = 0  # 0 = Player 1 (bottom), 1 = Player 2 (top)
        self.player0_house: int = pits_per_player
        self.player1_house: int = 2 * pits_per_player + 1
        self.size: int = len(self.board)

    def legal_moves(self) -> List[int]:
        """Return a list of pit indices that the current player may select."""
        if self.current_player == 0:
            return [i for i in range(0, self.player0_house) if self.board[i] > 0]
        return [i for i in range(self.player0_house + 1, self.player1_house) if self.board[i] > 0]

    def make_move(self, pit_index: int, animate_callback: Optional[Callable[[List[int], int], None]] = None, anim_delay: float = 0.3) -> bool:
        """Execute a move from `pit_index`.

        - If `animate_callback` is provided, it will be called after each stone is sown
          with the (current) board and the index where the stone landed. The callback
          must be quick; this function will sleep for `anim_delay` seconds after each
          callback to pace animations.

        Returns:
          bool: True if the game is now over, False otherwise.
        """
        if pit_index not in self.legal_moves():
            raise ValueError("Invalid move: pit not selectable for current player")

        stones = self.board[pit_index]
        self.board[pit_index] = 0
        idx = pit_index

        # Sow stones, skipping the opponent's house
        while stones > 0:
            idx = (idx + 1) % self.size
            if self.current_player == 0 and idx == self.player1_house:
                continue
            if self.current_player == 1 and idx == self.player0_house:
                continue
            self.board[idx] += 1
            stones -= 1

            if animate_callback:
                animate_callback(self.board, idx)
                time.sleep(anim_delay)

        # Determine capture or extra turn
        extra_turn = False
        if self.current_player == 0 and idx == self.player0_house:
            extra_turn = True
        elif self.current_player == 1 and idx == self.player1_house:
            extra_turn = True
        else:
            # capture rule: last stone landed in an empty pit on player's side
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
        """Return True if the game is over. If it is, collect remaining stones
        from the non-empty side into the appropriate house (mutates the board).
        """
        side1_empty = all(self.board[i] == 0 for i in range(0, self.player0_house))
        side2_empty = all(self.board[i] == 0 for i in range(self.player0_house + 1, self.player1_house))

        if side1_empty or side2_empty:
            # collect remaining stones into houses
            self.board[self.player0_house] += sum(self.board[i] for i in range(0, self.player0_house))
            self.board[self.player1_house] += sum(self.board[i] for i in range(self.player0_house + 1, self.player1_house))
            for i in range(0, self.player0_house):
                self.board[i] = 0
            for i in range(self.player0_house + 1, self.player1_house):
                self.board[i] = 0
            return True
        return False

    def get_winner(self) -> int:
        """Return the winner: 0 (player0), 1 (player1), or -1 for draw.

        This method does not modify the board. It expects that the game is in a
        terminal state (one side empty). If the game is not over it raises ValueError.
        """
        side1_empty = all(self.board[i] == 0 for i in range(0, self.player0_house))
        side2_empty = all(self.board[i] == 0 for i in range(self.player0_house + 1, self.player1_house))

        if not (side1_empty or side2_empty):
            raise ValueError("Game is not over yet")

        # compute final scores without mutating board
        final_p0 = self.board[self.player0_house] + sum(self.board[i] for i in range(0, self.player0_house))
        final_p1 = self.board[self.player1_house] + sum(self.board[i] for i in range(self.player0_house + 1, self.player1_house))

        if final_p0 > final_p1:
            return 0
        if final_p1 > final_p0:
            return 1
        return -1

