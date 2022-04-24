#pragma once
#include <cstdio>
#include <algorithm>

#include "config.h"

class Board {
	int M, N, noX, noY;
	int top[MAX_SIZE], initTop[MAX_SIZE];
	int boardX[MAX_SIZE], initX[MAX_SIZE];
	int boardY[MAX_SIZE], initY[MAX_SIZE];
	int boardDiagL[MAX_SIZE * 3], initDiagL[MAX_SIZE * 3];
	int boardDiagR[MAX_SIZE * 3], initDiagR[MAX_SIZE * 3];
	inline void clear();
	inline bool inLine(const int& a) const;
	inline int getPos(const int& x, const int& y) const;
public:
	void init(const int _M, const int _N, const int _noX, const int _noY,
		const int* _board);
	void reinit();
	void place(const int& Y, const int& player);
	void remove(const int& Y, const int& player);

	bool judgeWin(const int& Y)const;
	bool isTie() const;
	int valueJudge(const int& x, const int& y, const int& player) const;

	int getTop(const int& Y)const { return top[Y]; }
	bool full(const int& Y)const { return top[Y] == 0; }
	void print() const;
};

inline int getScore(int count, int countl, int countr) {
	if (count >= 4)
		return 10000;
	switch (std::max(countl, countr)) {
	case 1:
		return 1;
	case 2:
		return 2;
	default:
		return 5;
	}
}