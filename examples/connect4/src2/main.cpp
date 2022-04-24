#include <iostream>
#include "Strategy.h"
using namespace std;
int M=10, N = 10;
int board[100] = {};
int top[10] = {};
int noX = 4, noY = 4;

void put(int* b, int* t, int x, int y, type player){
    //player: user1, machine2
    //走一步
    b[x*N+y] = (int)player;
    if(x-1 == noX && y == noY){
        top[y] = noX;
    }
    else{
        top[y]=x;
    }
}
void printBoard(int* b){
    cout<<"-------------------\n";
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
        std::cout<<i<<' ';
    }
    cout<<"\n-------------------\n";
	return;
}

int main(){
    AI_Engine test;
    test.Init(M, N, noX, noY);

    for(int i=0;i<N;i++){
        top[i] = M;
    }
    while(1){
        int choice;
        cin>>choice;
        put(board, top, top[choice]-1, choice, USER);
        printBoard(board);
        if(userWin1(top[choice],choice, M, N, board)){
            cout<<"You Win!\n";
            break;
        }
        pair<int, int> move = test.makeMove(top[choice], choice);
        cout<<"move: "<<move.first<<' '<<move.second<<endl;
        put(board, top, move.first, move.second, MACHINE);
        printBoard(board);
        if(machineWin1(move.first, move.second,M,N,board)){
            cout<<"Machine Win!!!\n";
            break;
        }
    }
    return 0;
}
