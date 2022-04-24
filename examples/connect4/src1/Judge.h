
#ifndef JUDGE_H_
#define JUDGE_H_


bool userWin(const int x, const int y, const int M, const int N, int* const* board);

bool machineWin(const int x, const int y, const int M, const int N, int* const* board);


bool isTie(const int N, const int* top);

#endif