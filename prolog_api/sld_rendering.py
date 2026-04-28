from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import webbrowser


class SvgLayoutConfig:
    node_width: int = 500
    min_node_height: int = 96
    x_spacing: int = 42
    y_spacing: int = 190
    margin: int = 40
    font_size: int = 12
    line_height: int = 18
    text_padding: int = 14
    max_text_chars: int = 62


def save_sld_tree_svg(
    tree: Dict[str, Any],
    output_path: str | Path = "sld_tree.svg",
    title: str | None = None,
) -> Path:
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
    top_offset = config.margin + (46 if title else 0)
    _layout_tree(tree, 0, 0, config, nodes, top_offset)

    width = int(max(node["x"] for node in nodes) + config.node_width / 2 + config.margin)
    height = int(max(node["y"] + node["height"] for node in nodes) + config.margin)

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        """<style>
  .page { fill: #ffffff; }
  .node rect { fill: #ffffff; stroke: #1f2937; stroke-width: 1.5px; rx: 8px; filter: drop-shadow(0px 2px 5px rgba(15, 23, 42, 0.12)); }
  .node.success rect { stroke: #15803d; }
  .node.failed rect { stroke: #b91c1c; }
  .node.cut rect { stroke: #2563eb; }
  .node.prolog_goal rect { stroke: #16a34a; }
  .text { font-family: "Segoe UI", Arial, sans-serif; fill: #111827; }
  .mono { font-family: "Cascadia Mono", Consolas, monospace; fill: #111827; }
  .title { font-family: "Segoe UI", Arial, sans-serif; fill: #111827; font-weight: 650; font-size: 19px; }
  .edge { stroke: #374151; stroke-width: 1.35px; }
  .edge-label { font-family: "Cascadia Mono", Consolas, monospace; fill: #374151; font-size: 11px; }
  .edge-label-bg { fill: #ffffff; stroke: #e5e7eb; stroke-width: 1px; rx: 6px; }
  .status { font-weight: 650; }
</style>""",
        '<rect class="page" x="0" y="0" width="100%" height="100%" />',
    ]

    if title:
        svg_parts.append(
            f'<text x="{config.margin}" y="{config.margin + 18}" class="title">{_escape_svg(title)}</text>'
        )

    for node in nodes:
        for child in node.get("children", []):
            svg_parts.append(_svg_edge(node, child, config))

    for node in nodes:
        svg_parts.append(_svg_node(node, config))

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def _layout_tree(
    node: Dict[str, Any],
    depth: int,
    x_offset: float,
    config: SvgLayoutConfig,
    nodes: List[Dict[str, Any]],
    top_offset: int,
) -> float:
    children = node.get("children", [])
    node["lines"] = _node_label_lines(node, config)
    node["height"] = max(
        config.min_node_height,
        len(node["lines"]) * config.line_height + 2 * config.text_padding,
    )
    node["y"] = top_offset + depth * (config.min_node_height + config.y_spacing)

    if not children:
        node["x"] = x_offset + config.node_width / 2
        nodes.append(node)
        return config.node_width + config.x_spacing

    sub_x = x_offset
    child_centers = []
    for child in children:
        child_width = _layout_tree(child, depth + 1, sub_x, config, nodes, top_offset)
        child_centers.append(child["x"])
        sub_x += child_width

    node["x"] = sum(child_centers) / len(child_centers)
    nodes.append(node)
    return max(config.node_width + config.x_spacing, sub_x - x_offset)


def _svg_edge(parent: Dict[str, Any], child: Dict[str, Any], config: SvgLayoutConfig) -> str:
    x1 = parent["x"]
    y1 = parent["y"] + parent["height"]
    x2 = child["x"]
    y2 = child["y"]
    edge = f'<line class="edge" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" />'
    label_lines = child.get("edge_lines") or ([child["edge_label"]] if child.get("edge_label") else [])
    if not label_lines:
        return edge

    label_x = (x1 + x2) / 2
    first_label_y = (y1 + y2) / 2 - ((len(label_lines) - 1) * config.line_height / 2)
    max_chars = max(len(line) for line in label_lines)
    bg_width = max(80, min(config.node_width, max_chars * 7 + 22))
    bg_height = len(label_lines) * config.line_height + 10
    bg_x = label_x - bg_width / 2
    bg_y = first_label_y - config.line_height + 5

    parts = [
        edge,
        f'<rect class="edge-label-bg" x="{bg_x}" y="{bg_y}" width="{bg_width}" height="{bg_height}" />',
    ]
    for index, line in enumerate(label_lines):
        y = first_label_y + index * config.line_height
        parts.append(
            f'<text class="edge-label" x="{label_x}" y="{y}" text-anchor="middle">{_escape_svg(line)}</text>'
        )
    return "\n".join(parts)


def _svg_node(node: Dict[str, Any], config: SvgLayoutConfig) -> str:
    x = node["x"] - config.node_width / 2
    y = node["y"]
    content = [
        f'<g class="node {_status_class(node)}">',
        f'<rect x="{x}" y="{y}" width="{config.node_width}" height="{node["height"]}" />',
    ]

    text_y = y + config.text_padding + config.line_height
    for line in node.get("lines") or _node_label_lines(node, config):
        content.append(_svg_text_line(line, x + config.text_padding, text_y, config))
        text_y += config.line_height

    content.append("</g>")
    return "\n".join(content)


def _svg_text_line(line: str, x: float, y: float, config: SvgLayoutConfig) -> str:
    css_class = "text"
    if line.startswith(("?-", "Klausel", "s_", "u_", "Antwort")):
        css_class = "mono"
    if line.startswith(("Erfolg", "Fehlschlag", "Cut")):
        css_class = "text status"
    return f'<text class="{css_class}" x="{x}" y="{y}" font-size="{config.font_size}">{_escape_svg(line)}</text>'


def _node_label_lines(node: Dict[str, Any], config: SvgLayoutConfig) -> List[str]:
    label_lines = [f"?- {node.get('goal', '')}"]

    clause = node.get("clause")
    if clause:
        line_number = node.get("line_number")
        clause_label = f"Klausel ({line_number})" if line_number is not None else "Klausel"
        label_lines.append(f"{clause_label}: {clause}")

    if node.get("result"):
        label_lines.append(_format_result(node))

    if node.get("backtracking"):
        label_lines.append("Backtracking: naechste Klausel")

    answers = node.get("answers") or []
    if answers:
        label_lines.append(f"Antwort: {_format_answers(answers)}")

    wrapped: List[str] = []
    for line in label_lines:
        wrapped.extend(_wrap_line(line, config.max_text_chars))
    return wrapped


def _format_result(node: Dict[str, Any]) -> str:
    status = str(node.get("status") or "")
    result = str(node.get("result") or "")
    if status == "cut":
        return "Cut: erfolgreich"
    if result == "success":
        return "Erfolg"
    if result == "failed":
        return "Fehlschlag"
    return f"Status: {result}"


def _format_answers(answers: List[Dict[str, Any]]) -> str:
    if len(answers) == 1:
        answer = answers[0]
        if not answer:
            return "true"
        if len(answer) == 1:
            key, value = next(iter(answer.items()))
            return f"{key} = {_format_value(value)}"
        return ", ".join(f"{key} = {_format_value(value)}" for key, value in answer.items())
    return str(answers)


def _format_mapping(mapping: Dict[str, Any]) -> str:
    if not mapping:
        return "{}"
    return "{" + ", ".join(f"{key} -> {_format_value(value)}" for key, value in mapping.items()) + "}"


def _format_value(value: Any) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(_format_value(item) for item in value) + "]"
    return str(value)


def _wrap_line(line: str, max_chars: int) -> List[str]:
    if len(line) <= max_chars:
        return [line]

    parts: List[str] = []
    remaining = line
    indent = "  "
    while len(remaining) > max_chars:
        split_at = remaining.rfind(" ", 0, max_chars)
        if split_at <= 0:
            split_at = max_chars
        parts.append(remaining[:split_at])
        remaining = indent + remaining[split_at:].strip()
    if remaining:
        parts.append(remaining)
    return parts


def _status_class(node: Dict[str, Any]) -> str:
    status = str(node.get("status") or node.get("result") or "")
    result = str(node.get("result") or "")
    if status == "cut":
        return "cut"
    if status == "prolog_goal":
        return "prolog_goal"
    if result == "success":
        return "success"
    if result == "failed":
        return "failed"
    return "pending"


def _escape_svg(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
