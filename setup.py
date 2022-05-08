import os

from setuptools import setup


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join("..", path, filename))
    return paths


extra_files = package_files("cpp2py/template_data")

if __name__ == "__main__":
    setup(
        name="cpp2py",
        version="0.1",
        scripts=[f"bin{os.sep}cpp2py"],
        packages=["cpp2py", "cpp2py.generator", "cpp2py.parser"],
        package_data={"cpp2py": extra_files},
        requires=["numpy", "cython", "Jinja2"],
    )
