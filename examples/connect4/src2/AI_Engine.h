//
//  AI_Enigen.h
//  Strategy
//
//  Created by 乐阳 on 2020/4/1.
//  Copyright © 2020 Yongfeng Zhang. All rights reserved.
//
#ifndef AI_Enigen_h
#define AI_Enigen_h

#include <string.h>
#include <iostream>
#include <ctime>

#include <cstdlib>
#include "Judge.h"
#include "Node.h"
#define TIME_LIMIT 2.5



class AI_Engine{
private:
    int M, N;
    int noX, noY;
    MCST_Node* _root = nullptr;
    int *_board=nullptr, *_top=nullptr; //当前局面
    int *board=nullptr, *top=nullptr;//模拟局面
    //top数组记录当前局面每列最上面的节点
public:
    void Init(int m, int n, int nx, int ny);
    ~AI_Engine();
    void clear();
    void put(int* b, int* t, int x, int y, type player);
    int randput(int* t);//随机挑一步，返回列号
    bool valid(int x, int y);
    void moveRoot(int x, int y);
    std::pair<int,int> makeMove(int lastX, int lastY);
    void MonteCarloSearch();
    MCST_Node* treePolicy();
    int defaultPolicy(MCST_Node* node);
    MCST_Node* Expand(MCST_Node* node);
    std::pair<int, int> checkForce(int* b,int*t,type player);
    void printBoard(int* b); 
    void reportTree(){
        _root->reportTree();
    }
};
#endif /* AI_Enigen_h */
