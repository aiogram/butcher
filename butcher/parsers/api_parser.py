import logging
from datetime import date

import requests
from lxml import etree, html
from lxml.html import HtmlElement

from butcher.common_types import AnyDict
from butcher.parsers.consts import ANCHOR_HEADER_PATTERN, READ_MORE_PATTERN, SYMBOLS_MAP
from butcher.parsers.rst import node_to_rst

logger = logging.getLogger(__name__)


def parse_content(content: HtmlElement) -> AnyDict:
    groups = []

    group = None

    version = None
    release_date = None

    for item in content.xpath("//a[@class='anchor']"):  # type: HtmlElement
        parent_tag: HtmlElement = item.getparent()
        anchor_name = item.get("name", None)

        matches = ANCHOR_HEADER_PATTERN.match(parent_tag.tag)
        if not matches or not anchor_name:
            continue
        level = int(matches.group(1))
        title = item.tail

        if level == 3:
            if group:
                optimize_group(groups, group)

            logger.debug("Parse group %r (#%s)", title, anchor_name)
            group = {
                "title": title,
                "anchor": anchor_name,
                "children": [],
            }
            groups.append(group)

        if group and group["anchor"] == "recent-changes" and not version:
            if level != 4:
                continue

            release_date = parse_release_date(str(title))
            version = item.getparent().getnext().text_content().rsplit(" ", maxsplit=1)[-1]

        if level == 4 and len(title.split()) > 1:
            continue

        elif anchor_name not in [
            "recent-changes",
            "authorizing-your-bot",
            "making-requests",
            "using-a-local-bot-api-server",
        ]:
            child = _parse_child(parent_tag, anchor_name)
            group["children"].append(child)

    if group:  # Optimize last group
        optimize_group(groups, group)

    return {
        "api": {
            "version": version,
            "release_date": release_date,
        },
        "items": groups,
    }


def parse_release_date(value: str) -> date:
    month, day, year = map(str.strip, value.replace(",", "").split())
    return date(
        month=[
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ].index(month)
        + 1,
        day=int(day),
        year=int(year),
    )


def parse_docs(url: str) -> AnyDict:
    raw_content = load_page(url=url)
    content = to_html(content=raw_content, url=url)
    return parse_content(content=content)


def load_page(url: str) -> str:
    logger.debug("Load page %r", url)
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def to_html(content: str, url: str) -> HtmlElement:
    page = html.fromstring(content, url)
    for br in page.xpath("*//br"):
        br.tail = "\n" + br.tail if br.tail else "\n"

    return page


def optimize_group(groups: list[AnyDict], group: AnyDict):
    if not group["children"]:
        logger.debug("Remove empty %s", group)
        groups.remove(group)
        return

    if not group["children"][0]["annotations"]:
        logger.debug("Update group %r description from first child element", group["title"])
        group["description"] = group["children"][0]["description"]
        group["children"].pop(0)


def _parse_child(start_tag: HtmlElement, anchor: str):
    name = str(start_tag.text_content())
    description = []
    html_description = []
    rst_description = []
    annotations = []

    is_method = name[0].islower()

    logger.debug("Parse block: %r (#%s)", name, anchor)

    for item in _parse_tags_group(start_tag):
        if item.tag == "table":
            for raw in _parse_table(item):
                if is_method:
                    normalize_method_annotation(raw)
                else:
                    normalize_type_annotation(raw)
                annotations.append(raw)

        elif item.tag == "p":
            description.extend(item.text_content().splitlines())
            html_description.append(node_to_html(item))
            rst_description.append(node_to_rst(item))
        elif item.tag == "blockquote":
            description.extend(_parse_blockquote(item))
            html_description.append(node_to_html(item))
            rst_description.append(node_to_rst(item))
        elif item.tag == "ul":
            description.extend(_parse_list(item))
            html_description.append(node_to_html(item))
            rst_description.append(node_to_rst(item))

    description = normalize_description("\n".join(description))
    html_description = "".join(html_description).strip()
    rst_description = "".join(rst_description).strip()
    block = {
        "anchor": anchor,
        "name": name,
        "description": description,
        "html_description": html_description,
        "rst_description": rst_description,
        "annotations": annotations,
        "category": "types" if name[0].isupper() else "methods",
    }
    logger.debug("%s", block)
    return block


def _parse_tags_group(start_tag: HtmlElement):
    tag: HtmlElement = start_tag.getnext()
    while tag is not None and tag.tag not in ["h3", "h4"]:
        yield tag
        tag: HtmlElement = tag.getnext()


def _parse_table(table: HtmlElement):
    head, body = table.getchildren()  # type: HtmlElement, HtmlElement
    header = [item.text_content() for item in head.getchildren()[0]]

    for body_item in body:
        item_dict = dict(zip(header, body_item))
        item = {k.lower(): v.text_content() for k, v in item_dict.items()}
        item |= {
            "html_description": node_to_html(item_dict["Description"]),
            "rst_description": node_to_rst(item_dict["Description"]),
        }
        yield item


def _parse_blockquote(blockquote: HtmlElement):
    for item in blockquote.getchildren():
        yield from item.text_content().splitlines()


def _parse_list(data: HtmlElement):
    for item in data.getchildren():
        yield " - " + item.text_content()


def node_to_html(item: HtmlElement) -> str:
    return etree.tostring(item).decode().strip()


def normalize_description(text: str) -> str:
    for bad, good in SYMBOLS_MAP.items():
        text = text.replace(bad, good)
    text = READ_MORE_PATTERN.sub("", text)
    text.strip()
    return text


def normalize_annotation(item: dict):
    item["description"] = normalize_description(item["description"])
    item["type"] = str(item["type"])


def normalize_method_annotation(item: dict):
    normalize_annotation(item)
    item["required"] = {"Optional": False, "Yes": True}[item["required"]]
    item["name"] = item.pop("parameter")

    item["name"] = str(item["name"])


def normalize_type_annotation(item: dict):
    normalize_annotation(item)

    item["name"] = item.pop("field", item.pop("parameter", None))

    if item["description"].startswith("Optional"):
        item["required"] = False
        item["description"] = item["description"][10:]
    else:
        item["required"] = True

    item["name"] = str(item["name"])
