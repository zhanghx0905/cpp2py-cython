# CPP2PY: Automatically Generate Cython Wrapper from C/C++ Headers 

Suppose that you have a C++ API like this 

```c++
Point* getPoint(
    const int M, 
    const int N, 
    const int* top, 
    const int* _board, 
);
```

And you want to call it in Python like this

```python
def get_point(
    M: np.int32,
    N: np.int32,
    top: np.ndarray[Any, np.dtype[np.int32]],
    _board: np.ndarray[Any, np.dtype[np.int32]],
) -> Point: ...
```

Then this tool is for you.

## Usage

Detailed documentation is available [here](./doc/doc.pdf) (in Chinese, as part of my bachelor thesis).

For current setup, compilerless development, and pointer ownership migration, see [the development guide](./doc/development.md).

You can call this tool from the command line (`cpp2py` or `python -m cpp2py`):

```
usage: cpp2py [-h] [--sources [SOURCES [SOURCES ...]]] [--modname [MODNAME]] [--outdir [OUTDIR]] [--incdirs [INCDIRS [INCDIRS ...]]]
              [--globals GLOBALS] [--nobuild] [--cleanup] [--genstub] [--encoding ENCODING] [--verbose]
              header [header ...]

positional arguments:
  header                C++ header files

optional arguments:
  -h, --help            show this help message and exit
  --sources [SOURCES [SOURCES ...]]
                        C++ implementation files
  --modname [MODNAME]   Name of the generated extension module
  --outdir [OUTDIR]     output directory
  --incdirs [INCDIRS [INCDIRS ...]]
                        Include directories for clang parser
  --globals GLOBALS     name of the object that holds global variables and litral macros
  --nobuild             only generate code instead of building simultaneously
  --cleanup             clear intermediate files after building successfully
  --genstub             generate stub file (.pyi)
  --encoding ENCODING   encoding of input files
  --verbose, -v         verbosity leve
```
or in Python API:

```python
from cpp2py import make_cython_extention, Config

make_cython_extention(
    Config(...)
)
```
See [examples](./examples) and [testcases](./test/testcases) for more information.

## Features

- Global vars and literal macros are wrapped in the `cvar` object.
- C/C++ enums are mapped to Python enums (`cpdef enum`).
- C/C++ class/struct/union are mapped to Cython extension types.
  - Methods/Static Methods are wrapped
  - data members are mapped to Python property, static data members are wrapped like global variables 
  - Single & Multiple inheritance
  - Abstract class
  - Operator overloading
- C/C++ functions are mapped to Cython `cpdef` functions.


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
| Iterable[str]    | char**                                                       | str                            |
| Mapping/Iterable | std::vector, std::list, std::set, std::unordered_set, std::map, std::unordered_map, std::pair (only with str or numeric types) | set, list, dict, tuple         |
| complex          | std::complex                                                 | complex                        |

  - default values (number/string/character/bool literals)
  - `void*` can be handled once the underlying type is specified
  - `const` and left reference `&` qualifier will be ignored
- Generate the corresponding Python stub file (.pyi)

- Only the **first wrappable** one of the overloaded functions will be forwarding. However, overloaded functions and methods can be handled by the `renames_dict` field in config.
- Only one of the identifiers with the same name from different namespaces will be wrapped.

### Unsupported

- C++ Template
- C++ Smart pointer
- Anonymous enum/union/struct
- C function pointer

## Install
**Python 3.9 or newer**

```powershell
python -X utf8 -m venv .venv
& .\.venv\Scripts\python.exe -X utf8 -m pip install .
```

The `libclang` dependency supplies a prebuilt parser library on Windows/Linux/macOS. Do not install both `clang` and `libclang` Python distributions in the same environment. Use `--nobuild` / `Config(build=False)` to generate sources without a C++ compiler. Parsing headers that include the STL or a platform SDK still needs those real headers. Compiling a Python extension needs a C++ compiler and the corresponding SDK.

Raw class pointer returns now default to borrowed ownership. Configure `return_policies={"namespace::factory": "owned"}` for APIs that transfer objects allocated with C++ `new`. See the development guide before migrating existing integrations.

## Test
```powershell
python -m pip install -r requirements_dev.txt
python -m pytest
```

The default suite checks parsing, generated Cython, and packaging without a C++ compiler. On a machine with the required native dependencies:

```powershell
python -m pytest test -m integration
```

## Reference

The type conversion module is largely referred to [cythonwrapper](https://github.com/AlexanderFabisch/cythonwrapper). But much more features are implemented in this tool.

