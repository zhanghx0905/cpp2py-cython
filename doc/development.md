# 开发与无编译器验证

本项目有三个阶段：libclang 解析 C/C++ 头文件；Cython 将 `.pyx` 转换成 C++ 源码；C++ 编译器把源码编译并链接成 Python 扩展。前两个阶段可以在没有 C++ 编译器的 Windows 机器上运行。

## Windows 本地环境

以下命令在项目根目录的 PowerShell 中执行，使用隔离环境，Python 版本需为 3.9 或以上。

```powershell
python -X utf8 -m venv .venv
& .\.venv\Scripts\python.exe -X utf8 -m pip install --only-binary=:all: -r requirements_dev.txt
& .\.venv\Scripts\python.exe -X utf8 -m pip install --no-deps -e .
& .\.venv\Scripts\python.exe -X utf8 -m pytest
```

`libclang` 的 PyPI 发行包包含预编译动态库，能提供解析能力；它与不包含动态库的 `clang` 发行包共享 Python 导入名，不要把两者安装进同一个环境。程序在第一次解析时加载动态库，导入 `Config` 和查看 CLI 帮助不会尝试加载它。特殊安装可通过 `Config(libclang_library=...)`、`--libclang-library` 或环境变量 `CPP2PY_LIBCLANG_LIBRARY` 指定库文件；Python 绑定与原生库的版本需要匹配。

仅生成包装文件：

```powershell
& .\.venv\Scripts\python.exe -X utf8 -m cpp2py examples/compilerless/basic.hpp --modname demo --outdir generated/demo --nobuild --genstub
& .\.venv\Scripts\python.exe -X utf8 -m cython --cplus generated/demo/demo.pyx -o generated/demo/demo.cpp
```

第二条命令检查 Cython 声明、类型和生成语法，并生成 C++ 源码；不会编译 C++ 或验证链接、ABI 和析构行为。`.pyi` 可以供编辑器使用，但 `.pyx`、`.cpp` 和 `.pyi` 都不能直接作为已经编译的 Python 扩展导入。

libclang 的动态库不等于 C++ 标准库或操作系统 SDK。如果头文件包含 `<vector>`、`<string>`、`<Windows.h>` 等，本地仍需要真实的相应头文件和正确的目标配置；可以通过 `incdirs` / `libclang_flags` 指定，或把解析和构建放到具备依赖的 CI 机器上。不要用虚假的标准库声明代替真实 SDK 来判断兼容性。

## 构建与完整验证

Windows 原生构建需要 Visual Studio Build Tools 的 C++ 工具及 Windows SDK。只运行 `pip install libclang` 不会获得这些组件。Linux CI 配置在 `.github/workflows/tests.yml` 中：Windows/Linux 矩阵执行不需要编译器的测试，Ubuntu 环境安装 g++ 后执行扩展编译与运行时测试。该工作流在提交推送、PR 或手动触发后运行；本地新增配置不代表远程测试已经通过。

有 C++ 环境时执行：

```powershell
python -m pytest test -m integration -q
```

历史外部库测试还依赖 Linux 的 `make`、`.so` 和 `LD_LIBRARY_PATH`；CI 已配置相应目录。`test/integration/test_memory.py` 是独立的内存生命周期回归测试，可以在具备完整 C++ 环境的 Windows 上单独执行。

构建失败会抛出 `BuildError` 并保留诊断及生成文件。构建使用当前 Python 解释器，不改变调用进程的工作目录；清理仅在成功后删除输出目录里的生成文件。CLI 构建失败返回非零退出码。

## 指针所有权迁移

类按值返回使用 `new T(value)` 拷贝构造，配对 `delete`。生成的 `.pyx` 启用 Cython 3 的 `cpp_locals`，避免 Cython 临时变量重新引入默认构造/赋值要求；生成代码中的容器显式初始化。这一机制依赖 C++17 的 `std::optional`，Cython 官方仍标注为实验特性，因此完整编译和运行时测试也纳入了 CI。

类指针返回默认采用 `borrowed` 策略，不删除 C++ 返回的地址；借用的成员对象保留所属 Python 包装对象，普通函数返回的借用对象保留输入参数。返回空类指针或空数值指针得到 `None`，相应 stub 使用 `Optional`。

只有接口明确移交一个由 C++ `new` 分配的对象时，才指定 `owned`：

```python
from cpp2py import Config, make_cython_extention

config = Config(
    headers=["api.hpp"],
    target="generated/api",
    return_policies={
        "api::createPoint": "owned",
        "api::Point::clone": "owned",
    },
)
make_cython_extention(config)
```

策略键使用原始完整 C++ 函数或方法名，改名配置不改变键。`pointer_return_policy="owned"` 可以整体恢复旧行为，但每个指针返回接口都必须满足所有权移交约定；不能用于静态地址、成员地址、`malloc` 地址或需要专用释放函数的库对象。同名重载目前共用一个策略键。

借用策略也无法延长 C++ 外部管理对象的实际寿命，外部库仍须保证对象可用。`char**` 输入现在由临时 `vector[char*]` 管理指针数组，并持有 UTF-8 字节串；C++ 只可在调用期间使用这些指针，不可保存它们供后续调用，也不应修改字符串存储。数值指针输入要求非空、连续的缓冲区；参数之间的长度关系仍由具体 C++ API 的调用者负责。

如果返回的借用指针指向转换期间创建的临时 STL 容器，仅保留原始 Python 输入无法延长该 C++ 临时容器的寿命，需要专用适配。标量引用、STL 容器变更及 `class**` 输出参数也不会自动回写 Python 输入。

## 测试范围

默认 `pytest` 运行 `test/unit`：真实 libclang 解析、Cython 到 C++ 的转换、构建失败与清理路径、CLI、字面量和安装包资源验证。它不编译或导入扩展。`pytest test -m integration` 执行原有集成测试及新增的原生内存回归。

项目仍只转发第一个可包装重载，类/枚举/全局变量的 Python 名称不能保留所有同名命名空间对象。匿名类型不包装，但不再阻止后续声明的解析。未列入输入头文件的基类会给出明确错误，需补到 `Config.headers`。C++ 模板、智能指针和任意对象所有权关系仍需人工适配。
