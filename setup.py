from pathlib import Path

from setuptools import find_packages, setup

ROOT = Path(__file__).parent
extra_files = [
    path.relative_to(ROOT / "cpp2py").as_posix()
    for path in (ROOT / "cpp2py/template_data").rglob("*.j2")
]

if __name__ == "__main__":
    setup(
        name="cpp2py",
        version="0.1",
        description="Generate Cython wrappers from C/C++ headers",
        python_requires=">=3.9",
        entry_points={"console_scripts": ["cpp2py=cpp2py.cli:main"]},
        packages=find_packages(include=["cpp2py", "cpp2py.*"]),
        package_data={"cpp2py": extra_files},
        install_requires=(ROOT / "requirements.txt")
        .read_text(encoding="utf8")
        .splitlines(),
    )
