#pragma once

struct Value {
    static int alive;
    int number;
    Value(int n) : number(n) { ++alive; }
    Value(const Value& other) : number(other.number) { ++alive; }
    ~Value() { --alive; }
};
int Value::alive = 0;

struct Owner {
    Value member;
    Owner(int n) : member(n) {}
    Value* borrowed() { return &member; }
};

int live_count() { return Value::alive; }
Value copy_value(int n) { return Value(n); }
Value* make_owned(int n) { return new Value(n); }
Value* echo(Value* value) { return value; }
Value* null_value() { return nullptr; }
int* null_number() { return nullptr; }

int sum(const int* values, int count) {
    int result = 0;
    for (int i = 0; i < count; ++i) result += values[i];
    return result;
}

int string_bytes(char** words, int count) {
    int result = 0;
    for (int i = 0; i < count; ++i)
        for (int j = 0; words[i][j]; ++j) ++result;
    return result;
}

void fail_with_strings(char** words) { throw 1; }
