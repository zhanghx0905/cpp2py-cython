#include "uct.h"
#include <cmath>

MemoryPool _pool; // static memory

auto now = high_resolution_clock::now;

Point UCT::search(){
    auto beg = now();
	srand((uint)time(nullptr));
    int search_num = 0;
    while (search_num < SEARCH_LIMIT) {
        if (search_num % 1000 == 0 &&
            duration<double>(now() - beg).count() > TIME_LIMIT)
            break;

        Node* vl = treePolicy(_root);
        double reward = valuePolicy(vl->player);
         
        backUp(vl, reward);
        _board.reinit();
        _winner = -1;
        search_num++;
        _sqrt_InN = sqrtl(log(search_num));
    }
    //_pool.clear();
    Point action = finalAction(_root);
    _lastAct = action.y;
#if OUTPUT || _DEBUG
    _board.print();
    int sum = 0;
    for (int i = _root->children.size() - 1; i >= 0; --i) {
        printf("%d: %.4lf %d\n", _root->children[i]->action.y,
            _root->children[i]->UCB(_sqrt_InN), _root->children[i]->N);
        sum += _root->children[i]->N;
    }
    printf("%d %d\n", search_num, sum);
    printf("action: %d %d\n\n", action.x, action.y);
#endif
    return action;
}
	

void UCT::init(int M, int N, int noX, int noY, int lastY,
	const int* board, int player){
	_board.init(M, N, noX, noY, board);
	_M = M, _N = N;
	_winner = -1;
	_player = player;
    int steps = 0;
    for (int i = 0; i < M * N; i++) {
        if (board[i]) steps++;
    }
    if (steps < 2)
        _root = getRoot();
    else
        moveRoot(lastY);
    
}

void UCT::moveRoot(int lastY)
{
    int moves[2] = { _lastAct, lastY };
    for (int move = 0; move < 2; move++) {
        Node* tmp = _root;
        bool mark = false; 
        for (uint i = 0; i < tmp->children.size(); i++) {
            if (moves[move] == tmp->children[i]->action.y) {
                _root = tmp->children[i];
                _root->parent = nullptr;
                for (uint j = i + 1; j < tmp->children.size(); j++) {
                    tmp->children[j - 1] = tmp->children[j];
                }
                tmp->children.pop_back();
                mark = true;
                break;
            }
        }
        if (!mark) { // 因为剪枝，可能找不到对应子节点
            _root = getRoot();
            return;
        }
        _pool.recycle(tmp);
    }
}

Node* UCT::getRoot(){
    Node* root = _pool.newNode();
    root->player = getNextPlayer(_player);
    addAct(root);
    return root;
}

void UCT::addAct(Node* v){
    int next_player = getNextPlayer(v->player);
    bool lose = false;
    for (int i = 0; i < _N; i++) {
        if (!_board.full(i)) {
            // 判断我方是否获胜
            _board.place(i, next_player);
            if (_board.judgeWin(i)) {
                _board.remove(i, next_player);
                v->next_actions.clear();
                v->next_actions.push_back(i);
                break;
            }
            _board.remove(i, next_player);
            // 判断对方是否获胜
            _board.place(i, v->player);
            if (_board.judgeWin(i)) {
                _board.remove(i, v->player);
                if (!lose) {
                    v->next_actions.clear();
                    lose = true;
                }
                v->next_actions.push_back(i);
                continue;
            }
            _board.remove(i, v->player);
            // 无胜无负，将节点加入待扩展数组中
            if (!lose)
                v->next_actions.push_back(i);
        }
    }
}

Point UCT::finalAction(Node* v){
    int max = -1;
    Node* child = nullptr;
    for (uint i = 0; i < v->children.size(); i++) {
        auto& it = v->children[i];
        if (it->N > max) {
            max = it->N;
            child = it;
        }
    }
    if (child)
        return child->action;
    return { -1,-1 };
}

Node* UCT::treePolicy(Node* v) {
    while (_winner == -1) {
        if (!v->next_actions.empty() && _pool.unfull()) {
            return expand(v);
        }
        else {
            if (!v->children.empty()) {
                v = bestChild(v);
                updateBoard(v->action.y, v->player);
            }
            else break;
        }
    }
    return v;
}

Node* UCT::expand(Node* v){
    int y = v->next_actions.pop_back();
    Point action(_board.getTop(y)-1, y);
    Node* child = _pool.newNode(v, getNextPlayer(v->player), action);
    v->children.push_back(child);
    updateBoard(y, child->player);
    if (_winner == -1) {
        addAct(child);
    }
    return child;
}

Node* UCT::bestChild(Node* v) {
    double max_ucb = -1e5;
    Node* max_node = nullptr;
    for (uint i = 0; i < v->children.size(); ++i) {
        auto& it = v->children[i];
        double ucb = it->UCB(_sqrt_InN);
        if (!max_node || ucb > max_ucb) {
            max_ucb = ucb;
            max_node = it;
        }
    }
    return max_node;
}

double UCT::valuePolicy(int player){
    int current_player = getNextPlayer(player);
    int feasible_act[MAX_SIZE] = {}, feasible_num = 0;
    int choice, chosen_y;
    int scores[MAX_SIZE], total_score;
    for (int i = 0; i < _N; ++i) {
        if (!_board.full(i)) {
            feasible_act[feasible_num++] = i;
        }
    }
    while (_winner == -1){
        total_score = 0;
        for (choice = 0; choice < feasible_num; ++choice) {
            chosen_y = feasible_act[choice];
            scores[choice] = _board.valueJudge(_board.getTop(chosen_y) - 1, chosen_y, current_player) +
                _board.valueJudge(_board.getTop(chosen_y) - 1, chosen_y, getNextPlayer(current_player));
           total_score += scores[choice];
        }
        {
            int randnum = rand() % total_score;
            int limit = 0;
            for (choice = 0; choice < feasible_num; ++choice) {
                limit += scores[choice];
                if (randnum < limit) {
                    chosen_y = feasible_act[choice];
                    break;
                }
            }
        }
        updateBoard(chosen_y, current_player);
        if (_board.full(chosen_y)){
            feasible_num--;
            memmove(feasible_act + choice,
                feasible_act + choice + 1, sizeof(int) * (feasible_num - choice));
        }
        current_player = getNextPlayer(current_player);
    }
    if (_winner == player)
        return 1;
    else if (_winner == 0)
        return 0;
    return -1;
}

void UCT::backUp(Node* v, double reward){
    while (v){
        v->N++;
        v->Q += reward;
        v = v->parent;
        reward = -reward;
    }
}

void UCT::updateBoard(const int& y, int player) {
    _board.place(y, player);
    if (_board.judgeWin(y))
        _winner = player;
    else if (_board.isTie())
        _winner = 0;
}