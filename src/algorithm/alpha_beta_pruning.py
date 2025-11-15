# alpha_beta_pruning.py
import math
from mancala.mancala import Mancala
from typing import Optional, Tuple


# ==========================================
# Evaluation Function
# ==========================================
def evaluate(state: Mancala, player: int) -> int:
    """
    Simple but strong heuristic:
    - difference in house stones (most important)
    - difference in total stones on board (less important)
    - prefer moves that give extra turns later in the tree
    """
    if state.check_game_over():
        w = state.get_winner()
        if w == player:
            return 999999
        elif w == -1:
            return 0
        else:
            return -999999

    p0 = state.board[state.player0_house]
    p1 = state.board[state.player1_house]

    score_house = (p0 - p1) if player == 0 else (p1 - p0)

    # Optional: slight influence from stones on board
    board_p0 = sum(state.board[0:state.player0_house])
    board_p1 = sum(state.board[state.player0_house + 1: state.player1_house])
    score_board = (board_p0 - board_p1) if player == 0 else (board_p1 - board_p0)

    return score_house * 10 + score_board


# ==========================================
# Alpha-Beta Pruning
# ==========================================
def alpha_beta(
        state: Mancala,
        depth: int,
        alpha: float,
        beta: float,
        maximizing: bool,
        player: int
) -> int:
    """
    Standard minimax with alpha-beta pruning.
    Returns evaluation score.
    """

    # terminal or depth limit
    if depth == 0 or state.check_game_over():
        return evaluate(state, player)

    legal = state.legal_moves()
    if not legal:
        return evaluate(state, player)

    if maximizing:
        best = -math.inf
        for move in legal:
            new_state = clone_state(state)
            new_state.make_move(move)

            # If extra turn, same maximizing player moves again
            next_maximizing = (new_state.current_player == player)

            score = alpha_beta(
                new_state,
                depth - 1,
                alpha,
                beta,
                next_maximizing,
                player
            )

            best = max(best, score)
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best

    else:
        best = math.inf
        for move in legal:
            new_state = clone_state(state)
            new_state.make_move(move)

            next_maximizing = (new_state.current_player == player)

            score = alpha_beta(
                new_state,
                depth - 1,
                alpha,
                beta,
                next_maximizing,
                player
            )
            best = min(best, score)
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best


# ==========================================
# Choose Best Move
# ==========================================
def choose_best_move(state: Mancala, depth: int = 8) -> int:
    """
    Returns the best pit index for the AI to play.
    """
    player = state.current_player
    legal = state.legal_moves()

    best_move = None

    if player == 0:
        best_score = -math.inf
    else:
        best_score = -math.inf  # AI always maximizes relative to itself

    for move in legal:
        new_state = clone_state(state)
        new_state.make_move(move)

        maximizing = (new_state.current_player == player)

        score = alpha_beta(
            new_state,
            depth - 1,
            -math.inf,
            math.inf,
            maximizing,
            player
        )

        # Higher is always better for AI
        if score > best_score:
            best_score = score
            best_move = move

    return best_move


# ==========================================
# Small utility
# ==========================================
def clone_state(state: Mancala) -> Mancala:
    """
    Deep copy Mancala state manually because the class doesn't implement copy().
    """
    new = Mancala(stones_per_pit=0, pits_per_player=state.pits)
    new.board = state.board.copy()
    new.current_player = state.current_player
    new.player0_house = state.player0_house
    new.player1_house = state.player1_house
    return new
