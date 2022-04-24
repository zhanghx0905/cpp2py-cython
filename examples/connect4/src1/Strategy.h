#ifndef STRATEGY_H_
#define STRATEGY_H_

#include "Point.h"

#ifdef _MSC_VER
extern "C" __declspec(dllexport)
#endif // _MSC_VER
    Point* getPoint(const int M, const int N, const int* top, const int* _board,
        const int lastX, const int lastY, const int noX, const int noY);

#ifdef _MSC_VER
extern "C" __declspec(dllexport)
#endif // _MSC_VER
    void clearPoint(Point* p);

void clearArray(int M, int N, int** board);

#endif