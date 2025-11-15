"""Alpha-Beta search utilities for Mancala.

This module provides a simple evaluation function, a standard minimax
with alpha-beta pruning implementation, and a helper to pick the best
move for the current player.
"""
from __future__ import annotations

import math
from typing import Optional

from mancala.mancala import Mancala

# Score constants used by the evaluation function
_WIN_SCORE = 999_999
_LOSE_SCORE = -999_999
_DRAW_SCORE = 0


def evaluate(state: Mancala, player: int) -> int:
    """Evaluate `state` from the point-of-view of `player`.

    Heuristic (descending importance):
    - difference in house stones (multiplied): most important
    - difference in stones on the side's pits: secondary

    Returns a higher value when the position is better for `player`.
    Terminal positions return large +/- constants.
    """
    if state.check_game_over():
        winner = state.get_winner()
        if winner == player:
            return _WIN_SCORE
        if winner == -1:
            return _DRAW_SCORE
        return _LOSE_SCORE

    # stones in each player's store
    p0_house = state.board[state.player0_house]
    p1_house = state.board[state.player1_house]

    # primary score: house difference
    house_diff = (p0_house - p1_house) if player == 0 else (p1_house - p0_house)

    # secondary: difference in stones on the actual pits (not counting houses)
    board_p0 = sum(state.board[0:state.player0_house])
    board_p1 = sum(state.board[state.player0_house + 1 : state.player1_house])
    side_diff = (board_p0 - board_p1) if player == 0 else (board_p1 - board_p0)

    # weight the house difference more strongly
    return int(house_diff * 10 + side_diff)


def clone_state(state: Mancala) -> Mancala:
    """Create an independent copy of a Mancala state for search.

    The Mancala class doesn't implement a copy method, so we construct
    a fresh instance with the same board and metadata.
    """
    new = Mancala(stones_per_pit=0, pits_per_player=state.pits)
    new.board = state.board.copy()
    new.current_player = state.current_player
    new.player0_house = state.player0_house
    new.player1_house = state.player1_house
    return new


def alpha_beta(
    state: Mancala,
    depth: int,
    alpha: float,
    beta: float,
    maximizing: bool,
    player: int,
) -> int:
    """Minimax with alpha-beta pruning.

    - `state`: current game state (will not be mutated by the search)
    - `depth`: remaining search depth (0 = evaluate)
    - `alpha`, `beta`: current bounds
    - `maximizing`: whether this node should maximize for `player`
    - `player`: player index (0 or 1) we evaluate for

    Returns an integer evaluation.
    """
    # Terminal or depth limit
    if depth == 0 or state.check_game_over():
        return evaluate(state, player)

    legal = state.legal_moves()
    if not legal:
        return evaluate(state, player)

    if maximizing:
        value = -math.inf
        for move in legal:
            child = clone_state(state)
            child.make_move(move)

            # if the move gives an extra turn, the same player moves again
            next_max = (child.current_player == player)

            new_depth = depth if child.current_player == state.current_player else depth - 1
            score = alpha_beta(child, new_depth, alpha, beta, next_max, player)
            if score > value:
                value = score
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
        return int(value)

    else:
        value = math.inf
        for move in legal:
            child = clone_state(state)
            child.make_move(move)

            next_max = (child.current_player == player)

            new_depth = depth if child.current_player == state.current_player else depth - 1
            score = alpha_beta(child, new_depth, alpha, beta, next_max, player)
            if score < value:
                value = score
            if value < beta:
                beta = value
            if alpha >= beta:
                break
        return int(value)


def choose_best_move(state: Mancala, depth: int = 8) -> Optional[int]:
    """Return the best legal pit index for the current player, or None if no moves.

    The function performs a depth-limited alpha-beta search. If multiple moves
    share the same score, the first one encountered (leftmost) is returned
    which keeps the behavior deterministic.
    """
    legal = state.legal_moves()
    if not legal:
        return None

    player = state.current_player
    best_move: Optional[int] = None
    best_score = -math.inf

    for move in legal:
        child = clone_state(state)
        child.make_move(move)

        next_max = (child.current_player == player)
        new_depth = depth if child.current_player == state.current_player else depth - 1
        score = alpha_beta(child, new_depth, -math.inf, math.inf, next_max, player)

        if score > best_score:
            best_score = score
            best_move = move

    return best_move


__all__ = ["evaluate", "alpha_beta", "choose_best_move", "clone_state"]
