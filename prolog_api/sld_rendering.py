from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import webbrowser


class SvgLayoutConfig:
    node_width: int = 460
    min_node_height: int = 96
    x_spacing: int = 36
    y_spacing: int = 140
    margin: int = 40
    font_size: int = 12
    line_height: int = 18
    text_padding: int = 12
    max_text_chars: int = 58


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
    top_offset = config.margin + (42 if title else 0)
    _layout_tree(tree, 0, 0, config, nodes, top_offset)

    width = int(max(node["x"] for node in nodes) + config.node_width / 2 + config.margin)
    height = int(max(node["y"] + node["height"] for node in nodes) + config.margin)

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        """<style>
  .node rect { fill: #f8fafc; stroke: #1f2937; stroke-width: 1.6px; rx: 8px; filter: drop-shadow(0px 2px 4px rgba(0, 0, 0, 0.10)); }
  .node.success rect { fill: #ecfdf5; stroke: #15803d; }
  .node.failed rect { fill: #fef2f2; stroke: #b91c1c; }
  .node.cut rect { fill: #eff6ff; stroke: #2563eb; }
  .node.prolog_goal rect { fill: #f0fdf4; stroke: #16a34a; }
  .text { font-family: Arial, sans-serif; fill: #0f172a; }
  .title { font-weight: bold; font-size: 18px; }
  .edge { stroke: #475569; stroke-width: 1.4px; }
  .edge-label { fill: #334155; font-size: 11px; font-style: normal; }
  .result { fill: #0f172a; font-size: 12px; font-weight: bold; }
  .note { fill: #475569; font-size: 11px; }
</style>""",
    ]

    if title:
        svg_parts.append(
            f'<text x="{config.margin}" y="{config.margin + 18}" class="text title">{_escape_svg(title)}</text>'
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
    y = top_offset + depth * (config.min_node_height + config.y_spacing)
    node["y"] = y

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
    label = child.get("edge_label", "")

    if not label:
        return edge

    label_x = (x1 + x2) / 2
    label_y = (y1 + y2) / 2 - 8

    return (
        edge
        + f'\n<text class="edge-label" x="{label_x}" y="{label_y}" text-anchor="middle">{_escape_svg(label)}</text>'
    )


def _svg_node(node: Dict[str, Any], config: SvgLayoutConfig) -> str:
    x = node["x"] - config.node_width / 2
    y = node["y"]
    height = node["height"]
    status_class = _status_class(node)

    label_lines = node.get("lines") or _node_label_lines(node, config)

    content = [
        f'<g class="node {status_class}">',
        f'<rect x="{x}" y="{y}" width="{config.node_width}" height="{height}" />',
    ]

    text_y = y + config.text_padding + config.line_height

    for line in label_lines:
        content.append(
            f'<text class="text" x="{x + config.text_padding}" y="{text_y}" font-size="{config.font_size}">{_escape_svg(line)}</text>'
        )
        text_y += config.line_height

    content.append("</g>")
    return "\n".join(content)


def _node_label_lines(node: Dict[str, Any], config: SvgLayoutConfig) -> List[str]:
    label_lines = [f"Goal: {node.get('goal', '')}"]

    clause = node.get("clause")
    if clause:
        label_lines.append(f"Clause: {clause}")

    if node.get("line_number") is not None:
        label_lines.append(f"Line: {node['line_number']}")

    if node.get("substitution"):
        label_lines.append(f"σ: {node['substitution']}")

    if node.get("standardization"):
        label_lines.append(f"std: {node['standardization']}")

    if node.get("result"):
        label_lines.append(f"Result: {node['result']}")

    if node.get("backtracking"):
        label_lines.append(f"Backtracking: {node['backtracking']}")

    answers = node.get("answers") or []
    if answers:
        label_lines.append(f"Answers: {_format_answers(answers)}")

    wrapped: List[str] = []
    for line in label_lines:
        wrapped.extend(_wrap_line(line, config.max_text_chars))
    return wrapped


def _format_answers(answers: List[Dict[str, Any]]) -> str:
    if len(answers) == 1:
        answer = answers[0]
        if not answer:
            return "true"
        if len(answer) == 1:
            key, value = next(iter(answer.items()))
            return f"{key} = {value}"
        return ", ".join(f"{key} = {value}" for key, value in answer.items())
    return str(answers)


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
