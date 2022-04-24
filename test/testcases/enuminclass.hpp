#include <string>

class MyEnumClass
{
public:
    enum class MyEnum
    {
        FIRSTOPTION = 10,
        SECONDOPTION,
        THIRDOPTION
    };

    static std::string enumToString(MyEnum e)
    {
        switch (e)
        {
        case MyEnum::FIRSTOPTION:
            return "first";
        case MyEnum::SECONDOPTION:
            return "second";
        case MyEnum::THIRDOPTION:
            return "third";
        default:
            return "invalid";
        }
    }
};
