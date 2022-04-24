# CPP2PY: Automatically Generate Cython Wrapper from C/C++ Headers 

Suppose that you have a C++ API like this 

```c++
Point* getPoint(
    const int M, 
    const int N, 
    const int* top, 
    const int* _board, 
	const int lastX, 
    const int lastY, 
    const int noX, 
    const int noY);
```

And you want to call it in Python like this

```python
def get_point(
    M: np.int32,
    N: np.int32,
    top: np.ndarray[Any, np.dtype[np.int32]],
    _board: np.ndarray[Any, np.dtype[np.int32]],
    lastX: np.int32,
    lastY: np.int32,
    noX: np.int32,
    noY: np.int32,
) -> Point: ...
```

Then this tool is for you.

## Usage

TODO: Add more details

```
usage: cpp2py [-h] [--sources [SOURCES ...]] [--modname [MODNAME]] [--outdir [OUTDIR]] [--incdirs [INCDIRS ...]]
              [--verbose] [--clear] [--nobuild] [--genstub] [--encoding ENCODING]
              header [header ...]

positional arguments:
  header                C++ header files

options:
  -h, --help            show this help message and exit
  --sources [SOURCES ...]
                        C++ implementation files
  --modname [MODNAME]   Name of the generated extension module
  --outdir [OUTDIR]     output directory
  --incdirs [INCDIRS ...]
                        Include directories
  --verbose, -v         verbosity level
  --clear               clear intermediate files after building successfully
  --nobuild
  --genstub             generate .pyi stub file
  --encoding ENCODING
```

## Features

- C litral macros are mapped to Python variables.
- C/C++ enums are mapped to Python enums (enum.Enum).
- C/C++ class/struct/union are mapped to Cython extension types.
  - Single & Public inheritence
  - Abstruct class
  - Operator overloading
- C/C++ functions are mapped to Cython cpdef functions.
  - default values (only number/string literals)
- Generate the corresponding Python stub file (.pyi)

| Python type =>   | *C++ type*                                                   | => Python type                 |
| :--------------- | :----------------------------------------------------------- | :----------------------------- |
| ×                | void                                                         | ×                              |
| bool, int, float | bool, char, short, int, long, float, double ...              | bool, int, float               |
| numpy.ndarray    | int *, double *, ...                                         | its pointee                    |
| Iterable         | fixed-size array                                             | list                           |
| enum class       | enum                                                         | enum class                     |
| class            | class/struct/union                                           | class (with construct copying) |
| class            | class/struct/union's pointer                                 | class                          |
| class            | pointer of class/struct/union's pointer                      | ×                              |
| str              | char *, std::string                                          | str                            |
| Mapping/Iterable | std::vector, std::list, std::set, std::unordered_set, std::map, std::unordered_map, std::pair | set, list, dict, tuple         |
| complex          | std::complex                                                 | complex                        |

See [examples](./examples) and [testcases](./test/testcases) for more information.

TODO: Add more details

- `const` qualifier will be ignored

### Unsupported

- C++ Template
- Anonymous enum/union/struct
- C++ Smart pointer

## Requirements
Ubuntu 20.04

**Python 3.10 or newer**

```shell
sudo apt install libclang-12-dev
pip install -r requirement.txt
python setup.py install
```

## Test
```shell
LD_LIBRARY_PATH=. pytest test
```

## Reference

The type conversion module is largely referred to [cythonwrapper](https://github.com/AlexanderFabisch/cythonwrapper). But much more features are implemented in this tool.

