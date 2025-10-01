from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple


Player = str  # "X" or "O"


def other_player(player: Player) -> Player:
    return "O" if player == "X" else "X"


@dataclass
class MoveResult:
    board: List[str]
    winner: Optional[Player]
    is_draw: bool


class TicTacToe:
    def __init__(self) -> None:
        self.board: List[str] = [" "] * 9

    def clone(self) -> "TicTacToe":
        clone = TicTacToe()
        clone.board = self.board.copy()
        return clone

    def available_moves(self) -> List[int]:
        return [i for i, cell in enumerate(self.board) if cell == " "]

    def make_move(self, index: int, player: Player) -> MoveResult:
        if index < 0 or index >= 9:
            raise ValueError("Move index must be in range 0..8")
        if self.board[index] != " ":
            raise ValueError("Cell is already occupied")
        if player not in ("X", "O"):
            raise ValueError("Player must be 'X' or 'O'")

        self.board[index] = player
        winner = self._check_winner()
        is_draw = winner is None and all(c != " " for c in self.board)
        return MoveResult(self.board.copy(), winner, is_draw)

    def is_terminal(self) -> bool:
        return self._check_winner() is not None or all(c != " " for c in self.board)

    def evaluate(self, maximizing_player: Player) -> int:
        winner = self._check_winner()
        if winner == maximizing_player:
            return 1
        if winner == other_player(maximizing_player):
            return -1
        return 0

    def _check_winner(self) -> Optional[Player]:
        lines: Tuple[Tuple[int, int, int], ...] = (
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # cols
            (0, 4, 8), (2, 4, 6),             # diagonals
        )
        for a, b, c in lines:
            if self.board[a] != " " and self.board[a] == self.board[b] == self.board[c]:
                return self.board[a]
        return None


def minimax_best_move(game: TicTacToe, current_player: Player, ai_player: Player) -> int:
    best_score = float("-inf")
    best_move = -1
    for move in game.available_moves():
        game_after_move = game.clone()
        game_after_move.make_move(move, current_player)
        score = _minimax(game_after_move, other_player(current_player), ai_player, is_max_turn=False, alpha=float("-inf"), beta=float("inf"))
        if score > best_score:
            best_score = score
            best_move = move
    return best_move


def _minimax(game: TicTacToe, player_to_move: Player, ai_player: Player, is_max_turn: bool, alpha: float, beta: float) -> float:
    if game.is_terminal():
        return game.evaluate(ai_player)

    if is_max_turn:
        value = float("-inf")
        for move in game.available_moves():
            next_state = game.clone()
            next_state.make_move(move, player_to_move)
            value = max(value, _minimax(next_state, other_player(player_to_move), ai_player, is_max_turn=False, alpha=alpha, beta=beta))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = float("inf")
        for move in game.available_moves():
            next_state = game.clone()
            next_state.make_move(move, player_to_move)
            value = min(value, _minimax(next_state, other_player(player_to_move), ai_player, is_max_turn=True, alpha=alpha, beta=beta))
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value


def format_board(board: List[str]) -> str:
    rows = [
        f" {board[0]} | {board[1]} | {board[2]} ",
        "---+---+---",
        f" {board[3]} | {board[4]} | {board[5]} ",
        "---+---+---",
        f" {board[6]} | {board[7]} | {board[8]} ",
    ]
    return "\n".join(rows)


