import os
import re
from contextlib import contextmanager
from functools import lru_cache, partial

from jinja2 import Template
from pkg_resources import resource_filename

_NAMESPACE_PATTERN = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*::")
_CAMEL_PATTERN = re.compile(r"(?<=[a-z])[A-Z]|(?<!^)[A-Z](?=[a-z])")


@contextmanager
def _suppress_stream(file_descriptor: int):
    null_fd = os.open(os.devnull, os.O_RDWR)
    save_fd = os.dup(file_descriptor)
    os.dup2(null_fd, file_descriptor)
    try:
        yield
    finally:
        os.dup2(save_fd, file_descriptor)
        os.close(null_fd)


suppress_stdout = partial(_suppress_stream, 1)


def render(template: str, **kwargs) -> str:
    filename = resource_filename("cpp2py", f"template_data/{template}.j2")
    with open(filename, encoding="utf8") as f:
        j2template = Template(f.read())
    return j2template.render(**kwargs)


@lru_cache
def remove_namespace(typename: str):
    return _NAMESPACE_PATTERN.sub("", typename)


@lru_cache
def camel_to_snake(argname: str):
    return _CAMEL_PATTERN.sub(r"_\g<0>", argname).lower()


def print_header(text: str):
    print(os.linesep.join((f"+{'=' * 78}+", f"|{text.ljust(78)}|", f"+{'=' * 78}+")))
