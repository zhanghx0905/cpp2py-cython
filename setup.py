import os

from setuptools import setup

if __name__ == "__main__":
    setup(
        name="cpp2py",
        version="0.1",
        scripts=[f"bin{os.sep}cpp2py"],
        packages=["cpp2py", "cpp2py.generator", "cpp2py.parser"],
        package_data={"cpp2py": ["template_data/*.j2"]},
        requires=["numpy", "cython", "Jinja2"],
    )
