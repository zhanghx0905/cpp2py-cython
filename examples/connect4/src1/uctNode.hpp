#pragma once
#include <cmath>
#include <queue>

#include "config.h"
#include "Point.h"

using std::queue;
// Some inline classes

// Encapsulation of build-in array, not secure
template<typename T, uint N>
class Array {
public:
    Array() {
        for (uint i = 0; i < N; i++) _data[i] = T();
        _size = 0;
    }
    bool empty() { return !_size; }
    void clear() { _size = 0; }
    void push_back(const T& t) { _data[_size++] = t; }
    uint size() { return _size; }
    T& operator[](uint i) { return _data[i]; }
    T pop_back() { return _data[--_size]; }

private:
    T _data[N];
    uint _size;
};

// UCT node
struct Node {
    Point action;
    double Q;
    int N;
    Node* parent;
    int player;
    Array<Node*, MAX_SIZE> children;
    Array<int, MAX_SIZE> next_actions;
    double UCB(double sqrt_lnN) {
        return Q / N + C * sqrt_lnN/ sqrtl(N);
    }
    Node() : action(0, 0), Q(0), N(0), parent(nullptr), player(1) {}
};

// Memory pool to get UCT node efficiently
class MemoryPool {
public:
    MemoryPool() :_capacity(SEARCH_LIMIT), _top(0) {}

    Node* newNode(Node* parent = nullptr, int player = 1, Point action = { -1, -1 }) {
        Node* v = nullptr;
        if (!q.empty()) {
            v = q.front(); q.pop();
            for (uint i = 0; i < v->children.size(); i++)
                recycle(v->children[i]);
        }
        else v = &_space[_top++];
        v->N = 0; v->Q = 0.;
        v->children.clear(); v->next_actions.clear();
        v->parent = parent;
        v->player = player;
        v->action = action;
        return v;
    }
    bool unfull() { return (_top < _capacity); }
    void clear() { _top = 0; }
    void recycle(Node* bin) { 
        q.push(bin);
    }
private:
    queue<Node*> q;
    Node _space[SEARCH_LIMIT];
    int _capacity, _top;
};