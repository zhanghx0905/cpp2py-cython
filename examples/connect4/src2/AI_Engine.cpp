//
//  AI_Engine.cpp
//  Strategy
//
//  Created by 乐阳 on 2020/4/1.
//  Copyright © 2020 Yongfeng Zhang. All rights reserved.
//

#include "AI_Engine.h"


void AI_Engine::Init(int m, int n, int nx, int ny){
    M = m;
    N = n;
    noX = nx;
    noY = ny;
    clear();
    _board = new int[m*n];
    _top = new int[n];
    board = new int[M*N];
    top = new int[N];
    for(int i=0;i<M*N;i++){
        board[i] = _board[i] = 0;
    }
    for(int i=0;i<N;i++){
        if(nx == M-1 && ny==i){
            top[i] = _top[i] = M-1;
        }
        else{
            top[i] = _top[i] = M;
        }
    }
    _root = new MCST_Node(-1, -1, USER);
    srand((int)time(NULL));
}

void AI_Engine::clear(){
    if (_board!=nullptr){
        delete []_board;
    }
    if (_top!=nullptr){
        delete []_top;
    }
    if (board!=nullptr){
        delete []board;
    }
    if (top!=nullptr){
        delete []top;
    }
    if (_root!=nullptr){
        _root->freeBelow();
        delete _root;
    }
}

AI_Engine::~AI_Engine(){
    clear();
}

void AI_Engine::put(int* b, int* t, int x, int y, type player){
    //player: user1, machine2
    //走一步
    b[x*N+y] = (int)player;
    if(x-1 == noX && y == noY){
        t[y] = noX;
    }
    else{
        t[y]=x;
    }
}

//随机挑一步，返回列号
int AI_Engine::randput(int* t){
    int cnt = 0;
    for(int i=0;i<N;i++){
        if(t[i]>0) cnt++;
    }

    int choice = rand()%cnt + 1;
    int ans = 0;
    for(;ans<N;ans++){
        if(t[ans]>0) choice--;
        if(choice == 0){
            break;
        }
    }
    return ans;
}


std::pair<int,int> AI_Engine::makeMove(int lastX, int lastY){
    if (lastX != -1){
        put(_board, _top, lastX, lastY, USER);
    }
    moveRoot(lastX, lastY);//总是从USER移动到MACHINE

    clock_t start = clock();
    int cnt = 0;
    while(1){
        MonteCarloSearch();
        cnt ++;
        if(cnt%1000 == 0 && clock() - start > TIME_LIMIT*CLOCKS_PER_SEC){
            break;
        }
    }
    int bx, by;
    //迫手检查
    std::pair<int, int> force = checkForce(_board,_top,MACHINE);
    if(force.first!=-1){
        bx = force.first;
        by = force.second;
    }
    else{
        MCST_Node* best = _root->bestChild(0);
        if(best == nullptr){//走投无路
            by = randput(_top);
            bx = _top[by] - 1;
        }
        else{
            bx = best->mx;
            by = best->my;
        }

    }
    put(_board,_top, bx, by, MACHINE);
    moveRoot(bx, by);
    return std::make_pair(bx, by);
}


void AI_Engine::MonteCarloSearch(){
    //载入当前局面
    memcpy(board, _board, M*N*sizeof(int));
    memcpy(top, _top, N*sizeof(int));
    MCST_Node* v = treePolicy(); //寻找待扩展节点
    int gain;
    if(v->terminal != 0){
        gain = v->terminal - 2;
    }
    else{
        gain = defaultPolicy(v); //蒙特卡洛模拟
    }
    v->Backward(gain); //反向传播收益
}


MCST_Node* AI_Engine::treePolicy(){
    MCST_Node* current = _root;
    while(current->terminal == 0){//v不为终止节点
        MCST_Node* new_node = Expand(current);
        if (new_node != nullptr){
            //new_node->report();
            return new_node;
        }
        else{
            MCST_Node* bchild = current->bestChild(1.0);
            if(bchild == nullptr){
                current->terminal = 1;//该节点没有可能获胜
            }
            else if (bchild->terminal == 1){
                current->terminal = 3;//该节点必获胜
            }
            else{
                current = bchild;
                put(board, top, current->mx, current->my, type(3-current->player));//走步的性质与父节点相同
            }
        }
    }
    return current;
}



int AI_Engine::defaultPolicy(MCST_Node* node){
    type cur_player = node->player;
    int gain = -10;

    //检查是不是刚开始就结束了
    if (cur_player == MACHINE){
        if (userWin1(node->mx, node->my, M, N, board)){
            gain = -1;
        }
        else if(isTie(N, top)){
            gain = 0;
        }
    }
    else{
        if (machineWin1(node->mx, node->my, M, N, board)){
            gain = -1;
        }
        else if(isTie(N, top)){
            gain = 0;
        }
    }
    if(gain > -2){
        node->terminal = gain + 2;
        return gain;
    }
    //开始模拟
    bool determined = true;
    while(1){
        int x, y;
        std::pair<int, int> force = checkForce(board, top, cur_player);
        if(force.first!=-1){
            x = force.first;
            y = force.second;
        }
        else{
            determined = false;
            int ry = randput(top);
            x = top[ry] - 1;
            y = ry;
        }

        put(board, top, x, y, cur_player);
        //printBoard(board);
        //查看下完这一步后是否结束
        if (cur_player == MACHINE){
            if (machineWin1(x, y, M, N, board)){
                gain = 1;
            }
            else if(isTie(N, top)){
                gain = 0;
            }
        }
        else{
            if (userWin1(x, y, M, N, board)){
                gain = 1;
            }
            else if(isTie(N, top)){
                gain = 0;
            }
        }
        if (gain > -2){
            if(cur_player != node->player){
                gain = -gain;
            }
            break;
        }
        cur_player = (type) (3 - cur_player);
    }
    if (determined){
        node->terminal = gain + 2;
    }
    return gain;
}


MCST_Node* AI_Engine::Expand(MCST_Node *node){
    for(int i=node->to_expand;i<N;i++){
        if(top[i] > 0){ //可以扩展
            node->to_expand = i + 1;
            MCST_Node* new_node = new MCST_Node(top[i]-1, i, type(3 - node->player));
            new_node->next = node->fchild;
            new_node->parent = node;
            node->fchild = new_node;

            put(board, top, top[i]-1, i, node->player);//按扩展节点走一步
            return new_node;
        }
    }
    return nullptr;
}


void AI_Engine::moveRoot(int x, int y){
    MCST_Node* dst = _root->searchChild(x, y);
    if (dst == nullptr){ //新根没在原来的树里
        MCST_Node* new_root = new MCST_Node(x, y, (type)(3-_root->player));
        _root -> freeBelow();
        delete _root;
        _root = new_root;
        return;
    }
    MCST_Node* cur = _root->fchild;
    while(cur!=nullptr){
        MCST_Node* tmp = cur->next;
        if(cur!=dst){
            cur->freeBelow();
            delete cur;
        }
        cur = tmp;
    }
    delete _root;
    _root = dst;
    _root->parent = nullptr;
    _root->next= nullptr;
}

void AI_Engine::printBoard(int* b){
    int noPos = noX*N+noY;
    for(int i = 0; i < M; i++){
        for(int j = 0; j < N; j++){
            int pos = i * N + j;
            if(b[pos] == 0){
                if(pos == noPos){
                    std::cout << "X ";
                }
                else{
                    std::cout << ". ";
                }
            }
            else if(b[pos] == 2){
                std::cout << "A ";
            }
            else if(b[pos] == 1){
                std::cout << "B ";
            }
        }
        std::cout << std::endl;
    }
    for(int i=0;i<N;i++){
        std::cout<<top[i]<<' ';
    }
    std::cout<<'\n';
    return;
}

std::pair<int,int> AI_Engine::checkForce(int* b, int* t, type player){
    for(int i=0;i<N;i++){
        if(t[i]>0){
            int x = t[i]-1;
            int y = i;
            //我方下完就赢，则下在此处
            b[x*N+y] = (int)player;
            if(player == MACHINE){
                if(machineWin1(x, y, M, N, b)){
                    b[x*N+y] = 0;
                    return std::make_pair(x, y);
                }
            }
            else{//USER
                if(userWin1(x, y, M, N, b)){
                    b[x*N+y] = 0;
                    return std::make_pair(x, y);
                }
            }
            b[x*N+y] = 0;
        }
    }
    for(int i=0;i<N;i++){
        if(t[i]>0){
            int x = t[i]-1;
            int y = i;
            b[x*N+y] = (int)(3-player);
            //对方下完就赢，必须堵上
            if(player == MACHINE){
                if(userWin1(x,y,M,N,b)){
                    b[x*N+y] = 0;
                    return std::make_pair(x, y);
                }
            }
            else{
                if(machineWin1(x, y, M, N, b)){
                    b[x*N+y] = 0;
                    return std::make_pair(x,y);
                }
            }
            b[x*N+y] = 0;
        }
    }
    return std::make_pair(-1, -1);
}
