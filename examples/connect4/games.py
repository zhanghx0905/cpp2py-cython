"""
A demo

Fight against connect4 MCTS-based AI using Python
"""

import os

from random import randint

import numpy as np
from cpp2py import make_cython_extention, Config

try:
    import ai1
except ImportError:
    make_cython_extention(
        Config(
            ["src1/Point.h", "src1/Strategy.h"],
            "ai1",
            sources=[
                "src1/board.cpp",
                "src1/Judge.cpp",
                "src1/Strategy.cpp",
                "src1/uct.cpp",
            ],
            encoding="gbk",
        )
    )

    import ai1
try:
    import ai2
except ImportError:
    make_cython_extention(
        Config(
            ["src2/Point.h", "src2/Strategy.h"],
            "ai2",
            incdirs=["src2"],
            sources=[
                "src2/AI_Engine.cpp",
                "src2/Judge.cpp",
                "src2/Strategy.cpp",
                "src2/Node.cpp",
            ],
        )
    )
    import ai2

P1 = 1
P2 = 2

doc = """
    重力四子棋游戏说明

    每次只能选择在一个列中下一个棋子；

    由于重力作用，所下的棋子会下落到该列的最下方；

    某一随机位置无法落子；

    一方棋子在任意直线方向上连成4个棋子即获胜;

    按下任意键开始游戏"""


class Board:

    directions = [[[1, 0]], [[0, 1], [0, -1]], [[1, 1], [-1, -1]], [[1, -1], [-1, 1]]]
    printer = {0: "○", P1: "●", P2: "▲"}

    def __init__(self) -> None:
        self.M = randint(8, 10)
        self.N = randint(8, 10)
        self.noX = randint(0, self.M - 1)
        self.noY = randint(0, self.N - 1)
        self.top = np.ones(self.N, np.int32) * self.M
        if self.noX == self.M - 1:
            self.top[self.noY] -= 1
        self.board = np.zeros(self.M * self.N, np.int32)
        self.next_player = 1
        self.lastX = self.lastY = -1

    def move(self, x, y, player):
        assert self.next_player == player
        self.top[y] -= 1
        if self.top[y] == self.noX + 1 and y == self.noY:
            self.top[y] -= 1
        self.board[x * self.N + y] = player
        self.lastX = x
        self.lastY = y
        self.next_player = 3 - player

    def display(self):
        os.system("clear")
        print("P1 棋子 ●\tP2 棋子 ▲")

        def printt(*args):
            print(*args, end="  ")

        for i in range(self.M):
            for j in range(self.N):
                if i == self.noX and j == self.noY:
                    printt("✕")
                else:
                    printt(self.printer[self.board[i * self.N + j]])
            print()
        for j in range(self.N):
            printt(f"{j}")
        print()
        print(f"现在轮到: P{self.next_player}")

    def judge_win(self, x, y) -> bool:
        player = self.board[x * self.N + y]
        for dirs in self.directions:
            cnt = 1
            for dir in dirs:
                i, j = x, y
                while True:
                    i += dir[0]
                    j += dir[1]
                    if (
                        not self.M > i >= 0
                        or not self.N > j >= 0
                        or self.board[i * self.N + j] != player
                    ):
                        break
                    cnt += 1
            if cnt >= 4:
                return True
        return False

    def is_tie(self):
        return not self.top.any()


def machine_move(game: Board, player, get_point):
    if player == P1:
        board = (3 - game.board) % 3
    else:
        board = game.board
    p = get_point(
        game.M, game.N, game.top, board, game.lastX, game.lastY, game.noX, game.noY
    )
    return p.x, p.y


def human_move(game: Board):
    y = int(input("选择一列落子："))
    x = game.top[y] - 1
    return x, y


if __name__ == "__main__":
    input(doc)
    game = Board()
    game.display()

    while True:
        for player, ai in zip([P1, P2], [ai1, ai2]):
            x, y = machine_move(game, player, ai.get_point)
            game.move(x, y, player)
            game.display()
            if game.judge_win(x, y):
                print(f"游戏结束, P{player} 赢了")
                exit(0)
            if game.is_tie():
                print("游戏结束, 平局")
                exit(0)
