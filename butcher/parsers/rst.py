from typing import Generator, Iterable

from lxml.html import HtmlElement

from butcher.codegen.generators.pythonize import pythonize_name
from butcher.parsers.consts import REF_LINKS, SYMBOLS_MAP


def node_to_rst(node: HtmlElement) -> str:
    result = "".join(_node_to_rst(node))
    for a, b in {
        "*True*": ":code:`True`",
        "*False*": ":code:`False`",
        "_*": "_ *",
        **SYMBOLS_MAP,
    }.items():
        result = result.replace(a, b)
    return result


def _nodes_to_rst(nodes: Iterable[HtmlElement]) -> Generator[str, None, None]:
    for node in nodes:
        yield from _node_to_rst(node)


def _node_to_rst(node: HtmlElement) -> str:
    # TODO: Blockquote's
    tag = node.tag
    tail = ""
    if tag in {"p", "td"}:
        yield node.text or ""
    elif tag == "a":
        href = node.attrib["href"]
        if (
            node.text
            and href.startswith("#")
            and "-" not in href
            and f"#{node.text.lower()}" == href
        ):
            ref_name = node.text
            ref_group = "types" if ref_name[0].isupper() else "methods"
            yield f":class:`aiogram.{ref_group}.{pythonize_name(ref_name)}.{ref_name[0].upper()}{ref_name[1:]}`"
        elif href in REF_LINKS:
            yield f":ref:`{node.text or href} <{REF_LINKS[href]}>`"
        else:
            node.make_links_absolute()
            href = node.attrib["href"]
            yield f"`{node.text or href} <{href}>`_"
    elif tag == "img":
        yield node.attrib["alt"]
    elif tag in {"br", "blockquote"}:
        yield "\n"
    elif tag == "ul":
        if node.text:
            yield node.text
    elif tag == "li":
        yield " - "
        if node.text:
            yield node.text
    elif tag == "strong":
        yield "**"
        tail = "**"
        yield node.text
    elif tag == "em":
        yield "*"
        tail = "*"
        yield node.text
    elif tag == "code":
        yield f":code:`{node.text_content()}`"

    if tag == "blockquote":
        value = "".join(_nodes_to_rst(node))
        value.split("\n")
        value = " " + "\n ".join(value.split("\n"))
        yield value.rstrip() + "\n"
    else:
        yield from _nodes_to_rst(node)

    if tail:
        yield tail
    if node.tail:
        yield node.tail
