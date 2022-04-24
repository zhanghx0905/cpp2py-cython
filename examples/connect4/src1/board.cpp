#include "board.h"


inline void Board::clear() {
    CLEAR(boardX, 0);
    CLEAR(boardY, 0);
    CLEAR(boardDiagL, 0);
    CLEAR(boardDiagR, 0);
}

inline bool Board::inLine(const int& a) const{
    return (a & (a >> 2) & (a >> 4) & (a >> 6)) ? true : false;
}

inline int Board::getPos(const int& x, const int& y) const{
    if (x == noX && y == noY)
        return -1;
    for (int player = 1; player <= 2; player++)
        if (boardY[y] & (1 << (2 * x + player)))
            return player;
    return 0;
}

void Board::init(const int _M, const int _N, const int _noX, const int _noY,
    const int* _board) {
    clear();
    N = _N, M = _M, noX = _noX, noY = _noY;
    for (int i = 0; i < N; i++) top[i] = M;
    if (noX == M - 1) top[noY] = M - 1;
    for (int i = 0; i < N; i++)
        for (int j = M - 1; j >= 0; j--)
            if (_board[j * N + i])
                place(i, _board[j * N + i]);
    COPY(initTop, top);
    COPY(initX, boardX);
    COPY(initY, boardY);
    COPY(initDiagL, boardDiagL);
    COPY(initDiagR, boardDiagR);
}

void Board::reinit() {
    COPY(top, initTop);
    COPY(boardX, initX);
    COPY(boardY, initY);
    COPY(boardDiagL, initDiagL);
    COPY(boardDiagR, initDiagR);
}

void Board::place(const int& Y, const int& player) {
    int X = top[Y] - 1;
    boardX[X] |= (1 << (Y * 2 + player));
    boardY[Y] |= (1 << (X * 2 + player));
    boardDiagL[Y - X + M] |= (1 << (Y * 2 + player));
    boardDiagR[X + Y] |= (1 << (Y * 2 + player));
    top[Y]--;
    if (Y == noY && top[Y] - 1 == noX) top[Y]--;
}

void Board::remove(const int& Y, const int& player)
{
    if (Y == noY && top[Y] == noX) top[Y]++;
    int X = top[Y];
    boardX[X] &= ~(1 << (Y * 2 + player));
    boardY[Y] &= ~(1 << (X * 2 + player));
    boardDiagL[Y - X + M] &= ~(1 << (Y * 2 + player));
    boardDiagR[X + Y] &= ~(1 << (Y * 2 + player));

    top[Y]++;
}

bool Board::judgeWin(const int& Y) const{
    int X = top[Y];
    if (X == noX && Y == noY) X++;
    if (X == M)
        return false;
    return inLine(boardX[X]) || inLine(boardY[Y]) ||
        inLine(boardDiagL[Y - X + M]) || inLine(boardDiagR[X + Y]);
}

bool Board::isTie()const {
    for (int i = 0; i < N; i++) {
        if (top[i] > 0) {
            return false;
        }
    }
    return true;
}

int Board::valueJudge(const int& x, const int& y, const int& player)const  {
    //ºáÏò¼ì²â
    int i, j, score = 0;
    bool blank = false;
    int count = 1, countl = 1, countr = 1;
    for (i = y - 1; i >= 0; i--) {
        int p = getPos(x, i);
        if (p != player) { // Ïò×óÊÔÌ½
            if (!p)
                blank = true;
            break;
        }
    }
    count += (y - i - 1);
    countr += (y - i - 1);
    if (blank) {
        for (i = i - 1; i >= 0; i--)
            if (getPos(x, i) != player) {
                break;
            }
        countl += (y - i - 2);
    }
    blank = false;
    for (i = y + 1; i < N; i++) {
        int p = getPos(x, i);
        if (p != player) {
            if (!p)
                blank = true;
            break;
        }
    }
    count += (i - y - 1);
    countl += (i - y - 1);
    if (blank) {
        for (i = i + 1; i < N; ++i)
            if (getPos(x, i) != player) {
                break;
            }
        countr += (i - y - 2);
    }
    score += getScore(count, countl, countr);

    //×ÝÏò¼ì²â
    count = 1;
    for (i = x + 1; i < M; i++)
        if (getPos(i, y) != player)
            break;
    count += (i - x - 1);
    if (x + count >= 4)
        score += getScore(count, count, count);

    //×óÏÂ-ÓÒÉÏ
    count = 1, countl = 1, countr = 1;
    blank = false;
    for (i = x + 1, j = y - 1; i < M && j >= 0; i++, j--) {
        int p = getPos(i, j);
        if (p != player) {
            if (!p)
                blank = true;
            break;
        }
    }
    count += (y - j - 1);
    countr += (y - j - 1);
    if (blank) {
        for (i = i + 1, j = j - 1; i < M && j >= 0; i++, j--)
        {
            if (getPos(i, j) != player)
                break;
        }
        countl += (y - j - 2);
    }
    blank = false;
    for (i = x - 1, j = y + 1; i >= 0 && j < N; i--, j++) {
        int p = getPos(i, j);
        if (p != player) {
            if (!p)
                blank = true;
            break;
        }
    }
    count += (j - y - 1);
    countl += (j - y - 1);
    if (blank) {
        for (i = i - 1, j = j + 1; i >= 0 && j < N; i--, j++) {
            if (getPos(i, j) != player)
                break;
        }
        countr += (j - y - 2);
    }
    score += getScore(count, countl, countr);

    //×óÉÏ-ÓÒÏÂ
    count = 1, countl = 1, countr = 1;
    blank = false;
    for (i = x - 1, j = y - 1; i >= 0 && j >= 0; i--, j--) {
        int p = getPos(i, j);
        if (p != player) {
            if (!p)
                blank = true;
            break;
        }
    }
    count += (y - j - 1);
    countr += (y - j - 1);
    if (blank) {
        for (i = i - 1, j = j - 1; i >= 0 && j >= 0; i--, j--) {
            if (getPos(i, j) != player)
                break;
        }
        countl += (y - j - 2);
    }
    blank = false;
    for (i = x + 1, j = y + 1; i < M && j < N; i++, j++) {
        int p = getPos(i, j);
        if (p != player) {
            if (!p)
                blank = true;
            break;
        }
    }
    count += (j - y - 1);
    countl += (j - y - 1);
    if (blank) {
        for (i = i + 1, j = j + 1; i < M && j < N; i++, j++) {
            if (getPos(i, j) != player)
                break;
        }
        countr += (j - y - 2);
    }
    score += getScore(count, countl, countr);

    return score;
}


void Board::print() const{
    for (int j = 0; j < M; j++) { // X
        for (int i = 0; i < N; i++) { // Y
            if (j == noX && i == noY)
                printf("X ");
            else {
                int p = getPos(j, i);
                if (p == 0) printf(". ");
                else if (p == 1) printf("B ");
                else printf("A ");
            }
        }
        printf("\n");
    }
}