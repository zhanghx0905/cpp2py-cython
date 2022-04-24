//
//  Node.cpp
//  Strategy
//
//  Created by 乐阳 on 2020/4/4.
//  Copyright © 2020 Yongfeng Zhang. All rights reserved.
//

#include "Node.h"
int MCST_Node::cnt = 0;
MCST_Node* MCST_Node::bestChild(float C){
    float maxval = -1e9;
    MCST_Node* best = nullptr;
    MCST_Node* current = fchild;
    while(current!=nullptr){
        if (current->terminal == 1){
            //子节点显示必输，证明选该点必赢
            best = current;
            break;
        }
        else if (current->terminal == 3){
            //子节点必赢，说明一定不选
            current = current->next;
            continue;
        }
        float ucb = UCB(current, C);
        if (ucb > maxval){
            best = current;
            maxval = ucb;
        }
        current = current->next;
    }
    return best;//可能为nullptr
}
MCST_Node* MCST_Node::searchChild(short x, short y){
    if(fchild == nullptr) {
        return nullptr;
    }
    else{
        MCST_Node* cur = fchild;
        while(cur != nullptr){
            if (cur->mx == x && cur->my == y){
                return cur;
            }
            else{
                cur = cur->next;
            }
        }
        return nullptr;
    }
}

float MCST_Node::UCB(MCST_Node* child, float C){
    int N = child->n;
    int V = child->v;
    float ans = -V*1.0/N + C*sqrtf(2*logf(this->n) / N);
    return ans;
}

void MCST_Node::Backward(int gain){
    n += 1;
    v += gain;
    if(parent != nullptr){
        parent->Backward(-gain);
    }
}

void MCST_Node::freeBelow(){
    //递归删除子树
    MCST_Node* cur = fchild;
    while(cur!=nullptr){
        MCST_Node* tmp = cur->next;
        cur->freeBelow();
        delete cur;
        cur = tmp;
    }
}

void MCST_Node::report(){
    std::cout<<"Node("<<mx<<","<<my<<"):v="<<v<<",n="<<n<<",player="<<player<<'\n';
}
void MCST_Node::reportTree(){
    report();
    MCST_Node* cur = fchild;
    while(cur!=nullptr){
        cur->reportTree();
        cur = cur->next;
    }
    std::cout<<"end subtree\n";
}
