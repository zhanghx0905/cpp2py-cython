#include <cmath>

class Shape {
public:
    virtual ~Shape() {};
    virtual double area() const = 0;
    virtual double perimeter() const = 0;
};
class Circle : public Shape {
    int radius;

public:
    Circle(double radius)
        : radius(radius) {};
    double area() const { return M_PI * radius * radius; };
    double perimeter() const { return 2 * M_PI * radius; };
};
class Square : public Shape {
    double size;

public:
    Square(double size)
        : size(size) {};
    double area() const { return size * size; };
    double perimeter() const { return 4 * size; };
};

double getArea(Shape* shape)
{
    return shape->area();
}

double getPerimeter(const Shape& shape)
{
    return shape.perimeter();
}