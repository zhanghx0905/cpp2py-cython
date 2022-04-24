//
//  Node.h
//  Strategy
//
//  Created by 乐阳 on 2020/4/4.
//  Copyright © 2020 Yongfeng Zhang. All rights reserved.
//

#ifndef Node_h
#define Node_h
#include <cmath>
#include <iostream>
enum type {USER = 1, MACHINE = 2};
struct MCST_Node {
    MCST_Node *parent=nullptr, *next=nullptr, *fchild=nullptr;
    static int cnt;
    short mx=-1, my=-1;
    int n=0, v=0;//到该节点之后赢了v/n
    type player;//到该节点后轮到player
    short to_expand = 0;//最小可能扩展的列的编号
    short terminal = 0;//在该节点分出胜负
    MCST_Node(short x, short y, type p):mx(x), my(y), player(p){cnt++;}
    ~MCST_Node(){cnt--;}
    MCST_Node* searchChild(short x, short y);
    void Backward(int gain);
    MCST_Node* bestChild(float C);
    float UCB(MCST_Node* child, float C);
    void report();
    void reportTree();
    void freeBelow();
};

#endif /* Node_h */
