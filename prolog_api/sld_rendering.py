from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import webbrowser


class SvgLayoutConfig:
    node_width: int = 260
    node_height: int = 72
    x_spacing: int = 20
    y_spacing: int = 110
    margin: int = 24
    font_size: int = 13
    line_height: int = 18


def save_sld_tree_svg(tree: Dict[str, Any], output_path: str | Path = "sld_tree.svg", title: str | None = None) -> Path:
    path = Path(output_path)
    svg = render_sld_tree_svg(tree, title)
    path.write_text(svg, encoding="utf-8")
    return path


def open_svg_in_browser(path: str | Path) -> None:
    url = Path(path).resolve().as_uri()
    webbrowser.open(url, new=2)


def render_sld_tree_svg(tree: Dict[str, Any], title: str | None = None) -> str:
    config = SvgLayoutConfig()
    nodes: List[Dict[str, Any]] = []
    _layout_tree(tree, 0, 0, config, nodes)

    width = int(max(node["x"] for node in nodes) + config.node_width / 2 + config.margin)
    height = int(max(node["y"] for node in nodes) + config.node_height + config.margin)

    svg_parts = [
        f"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{width}\" height=\"{height}\" viewBox=\"0 0 {width} {height}\">",
        "<style>\n"
        "  .node rect { fill: #f8fafc; stroke: #1f2937; stroke-width: 1.8px; rx: 12px; }\n"
        "  .text { font-family: Arial, sans-serif; fill: #111827; }\n"
        "  .title { font-weight: bold; font-size: 16px; }\n"
        "  .edge { stroke: #4b5563; stroke-width: 1.2px; }\n"
        "  .note { fill: #374151; font-size: 12px; font-style: italic; }\n"
        "</style>",
    ]

    if title:
        svg_parts.append(
            f"<text x=\"{config.margin}\" y=\"{config.margin + 14}\" class=\"text title\">{_escape_svg(title)}</text>"
        )

    for node in nodes:
        for child in node.get("children", []):
            svg_parts.append(_svg_edge(node, child, config))

    for node in nodes:
        svg_parts.append(_svg_node(node, config))

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def _layout_tree(node: Dict[str, Any], depth: int, x_offset: float, config: SvgLayoutConfig, nodes: List[Dict[str, Any]]) -> float:
    children = node.get("children", [])
    y = config.margin + depth * (config.node_height + config.y_spacing)
    node["y"] = y

    if not children:
        node["x"] = x_offset + config.node_width / 2
        nodes.append(node)
        return config.node_width + config.x_spacing

    sub_x = x_offset
    child_centers = []
    for child in children:
        child_width = _layout_tree(child, depth + 1, sub_x, config, nodes)
        child_centers.append(child["x"])
        sub_x += child_width

    node["x"] = sum(child_centers) / len(child_centers)
    nodes.append(node)
    return max(config.node_width + config.x_spacing, sub_x - x_offset)


def _svg_edge(parent: Dict[str, Any], child: Dict[str, Any], config: SvgLayoutConfig) -> str:
    x1 = parent["x"]
    y1 = parent["y"] + config.node_height
    x2 = child["x"]
    y2 = child["y"]
    return f"<line class=\"edge\" x1=\"{x1}\" y1=\"{y1}\" x2=\"{x2}\" y2=\"{y2}\" />"


def _svg_node(node: Dict[str, Any], config: SvgLayoutConfig) -> str:
    x = node["x"] - config.node_width / 2
    y = node["y"]
    label_lines = [f"Goal: {node.get('goal', '')}"]
    clause = node.get("clause")
    if clause:
        label_lines.append(f"Clause: {clause}")
    label_lines.append(f"Status: {node.get('status', 'unknown')}")

    content = [
        f"<g class=\"node\">",
        f"<rect x=\"{x}\" y=\"{y}\" width=\"{config.node_width}\" height=\"{config.node_height}\" />",
    ]

    text_y = y + config.line_height + 6
    for line in label_lines:
        content.append(
            f"<text class=\"text\" x=\"{x + 12}\" y=\"{text_y}\" font-size=\"{config.font_size}\">{_escape_svg(line)}</text>"
        )
        text_y += config.line_height

    content.append("</g>")
    return "\n".join(content)


def _escape_svg(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
