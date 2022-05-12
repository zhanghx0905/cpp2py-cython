import os
import re
from contextlib import contextmanager
from functools import lru_cache, partial, reduce
from typing import Dict

from jinja2 import Template
from pkg_resources import resource_filename

_NAMESPACE_PATTERN = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*::")
_CAMEL_PATTERN = re.compile(r"(?<=[a-z])[A-Z]|(?<!^)[A-Z](?=[a-z])")


class PostInitMeta(type):
    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)
        obj.__post_init__()
        return obj


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


def removeprefix(txt: str, prefix: str):
    return txt[len(prefix) :] if txt.startswith(prefix) else txt


def toposort(data: Dict):
    """\
Dependencies are expressed as a dictionary whose keys are items
and whose values are a set of dependent items. Output is a list of
sets in topological order. The first set consists of items with no
dependences, each subsequent set consists of items that depend upon
items in the preceeding sets."""

    # Special case empty input.
    if len(data) == 0:
        return

    # Copy the input so as to leave it unmodified.
    # Discard self-dependencies and copy two levels deep.
    data = {item: {e for e in dep if e != item} for item, dep in data.items()}

    # Find all items that don't depend on anything.
    extra_items_in_deps = reduce(set.union, data.values()) - set(data.keys())
    # Add empty dependences where needed.
    data.update({item: set() for item in extra_items_in_deps})
    while True:
        ordered = {item for item, dep in data.items() if len(dep) == 0}
        if not ordered:
            break
        yield ordered
        data = {
            item: (dep - ordered) for item, dep in data.items() if item not in ordered
        }

    assert len(data) == 0  # assert there is no cicular dep
