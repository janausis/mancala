#!/usr/bin/env python3
"""AI vs AI simulator for Mancala.

Run many games headless (no UI) and report wins per player and draws.
This script will show a nice progress bar using `rich` if available, otherwise
falls back to simple stdout progress messages.

Usage:
  python3 src/simulate_ai.py --games 1000 --depth 4
"""
import sys
import argparse
from typing import Dict

# Make local package importable when running script from project root
if "src" not in sys.path:
    sys.path.insert(0, "src")

try:
    from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
    _HAS_RICH = True
except Exception:
    _HAS_RICH = False

from mancala.mancala import Mancala
from algorithm.alpha_beta_pruning import choose_best_move


def run_simulations(games: int = 1000, depth: int = 4, verbose: bool = False) -> Dict[str, int]:
    """Run `games` AI-vs-AI matches and return counts.

    Both players use `choose_best_move` with the same `depth`.
    Returns a dict with keys: 'player0', 'player1', 'draws'.
    """
    counts = {"player0": 0, "player1": 0, "draws": 0}

    if _HAS_RICH and not verbose:
        # show a single determinate progress bar for speed
        with Progress(TextColumn("{task.description}"), BarColumn(), TextColumn("{task.completed}/{task.total}"), TimeRemainingColumn()) as progress:
            task = progress.add_task("Simulating games", total=games)
            for g in range(1, games + 1):
                state = Mancala()
                while not state.check_game_over():
                    move = choose_best_move(state, depth=depth)
                    if move is None:
                        break
                    state.make_move(move)

                try:
                    winner = state.get_winner()
                except ValueError:
                    p0 = state.board[state.player0_house]
                    p1 = state.board[state.player1_house]
                    if p0 > p1:
                        winner = 0
                    elif p1 > p0:
                        winner = 1
                    else:
                        winner = -1

                if winner == 0:
                    counts["player0"] += 1
                elif winner == 1:
                    counts["player1"] += 1
                else:
                    counts["draws"] += 1

                progress.update(task, advance=1)

    else:
        # fallback: simple stdout updates
        for g in range(1, games + 1):
            state = Mancala()
            while not state.check_game_over():
                move = choose_best_move(state, depth=depth)
                if move is None:
                    break
                state.make_move(move)

            try:
                winner = state.get_winner()
            except ValueError:
                p0 = state.board[state.player0_house]
                p1 = state.board[state.player1_house]
                if p0 > p1:
                    winner = 0
                elif p1 > p0:
                    winner = 1
                else:
                    winner = -1

            if winner == 0:
                counts["player0"] += 1
            elif winner == 1:
                counts["player1"] += 1
            else:
                counts["draws"] += 1

            if verbose and (g % max(1, games // 10) == 0):
                print(f"Progress: {g}/{games} games")

    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate AI vs AI Mancala games (headless)")
    parser.add_argument("--games", type=int, default=1000, help="Number of games to run")
    parser.add_argument("--depth", type=int, default=4, help="Search depth for the AI")
    parser.add_argument("--verbose", action="store_true", help="Show progress")
    args = parser.parse_args()

    if _HAS_RICH:
        print("Using rich progress bar")
    else:
        print("rich not available — falling back to simple progress output")


    print("\n" * 5)

    print(f"Running {args.games} AI vs AI games (depth={args.depth})... This may take a while depending on depth.")
    counts = run_simulations(games=args.games, depth=args.depth, verbose=args.verbose)

    total = args.games
    p0 = counts["player0"]
    p1 = counts["player1"]
    draws = counts["draws"]

    print("\nResults:")
    print(f"Player 0 wins: {p0} ({p0/total:.2%})")
    print(f"Player 1 wins: {p1} ({p1/total:.2%})")
    print(f"Draws       : {draws} ({draws/total:.2%})")


if __name__ == "__main__":
    main()
