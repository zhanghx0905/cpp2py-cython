#pragma once

#include <chrono>

#include "uctNode.hpp"
#include "board.h"

using namespace std::chrono;

inline int getNextPlayer(const int& player) {
	return (3 - player);
}

class UCT{
public:
	Point search();
	void init(int M, int N, int noX, int noY, int lastY, const int* board, int player);
	void moveRoot(int lastY);
private:

	Board _board;
	int _winner;
	int _player;
	int _M, _N;
	Node* _root;
	double _sqrt_InN;
	int _lastAct;

	Node* getRoot();
	void addAct(Node* v);
	Point finalAction(Node* v);
	Node* treePolicy(Node* v);
	Node* expand(Node* v);
	Node* bestChild(Node* v);
	double valuePolicy(int player);
	void backUp(Node* v, double reward);
	
	void updateBoard(const int& action_y, int player);
};

