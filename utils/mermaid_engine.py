"""Native pure-Python Mermaid diagram parser, layout engine, and vector renderer for PyQt6."""

from collections import defaultdict, deque
from dataclasses import dataclass
import math
import re
from typing import Dict, List, Optional, Tuple

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetricsF,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
    QTextDocument,
)

MERMAID_OPEN_RE = re.compile(r"^\s*```mermaid\s*$", re.IGNORECASE)
MERMAID_CLOSE_RE = re.compile(r"^\s*```\s*$")

_MERMAID_CACHE: Dict[Tuple[str, int], QPixmap] = {}

NODE_PALETTE = [
    ("#1e2a3a", "#0a84ff"),  # Blue
    ("#26223a", "#5e5ce6"),  # Indigo
    ("#1d3128", "#30d158"),  # Green
    ("#362a1d", "#ff9f0a"),  # Amber
    ("#35202b", "#ff375f"),  # Rose
    ("#1e3136", "#64d2ff"),  # Cyan
]


@dataclass
class MermaidRegion:
    """Represents a fenced ```mermaid ... ``` block in a QTextDocument."""

    start_block: int
    end_block: int
    source: str


def find_mermaid_regions(doc: QTextDocument) -> List[MermaidRegion]:
    """Scan a QTextDocument for fenced ```mermaid ... ``` blocks."""
    regions: List[MermaidRegion] = []
    total = doc.blockCount()
    i = 0
    while i < total:
        text = doc.findBlockByNumber(i).text()
        if MERMAID_OPEN_RE.match(text):
            lines: List[str] = []
            j = i + 1
            closed = False
            while j < total:
                jt = doc.findBlockByNumber(j).text()
                if MERMAID_CLOSE_RE.match(jt):
                    closed = True
                    break
                lines.append(jt)
                j += 1
            if closed and lines:
                regions.append(
                    MermaidRegion(
                        start_block=i,
                        end_block=j,
                        source="\n".join(lines).strip(),
                    )
                )
                i = j + 1
                continue
        i += 1
    return regions


@dataclass
class FlowNode:
    """Node in a Mermaid flowchart or state diagram."""

    node_id: str
    label: str
    shape: str = "rect"  # rect, round, stadium, diamond, circle, cylinder, hex, start_end
    width: float = 90.0
    height: float = 40.0
    x: float = 0.0
    y: float = 0.0
    color_idx: int = 0


@dataclass
class FlowEdge:
    """Directed or undirected edge in a Mermaid flowchart."""

    src: str
    dst: str
    label: str = ""
    style: str = "solid"  # solid, dashed, thick
    has_arrow: bool = True


def _parse_node_token(token: str) -> Tuple[str, Optional[str], Optional[str]]:
    """Parse a single node token like 'A[Start]', 'B{Check?}', 'C((End))', or 'A'."""
    token = token.strip()
    if token == "[*]":
        return "[*]", "", "start_end"

    patterns = [
        (r"^([A-Za-z0-9_.-]+)\(\((.+)\)\)$", "circle"),
        (r"^([A-Za-z0-9_.-]+)\(\[(.+)\]\)$", "stadium"),
        (r"^([A-Za-z0-9_.-]+)\[\((.+)\)\]$", "cylinder"),
        (r"^([A-Za-z0-9_.-]+)\[\[(.+)\]\]$", "subroutine"),
        (r"^([A-Za-z0-9_.-]+)\{\{(.+)\}\}$", "hex"),
        (r"^([A-Za-z0-9_.-]+)\{(.+)\}$", "diamond"),
        (r"^([A-Za-z0-9_.-]+)\((.+)\)$", "round"),
        (r"^([A-Za-z0-9_.-]+)\[(.+)\]$", "rect"),
    ]
    for pat, shape in patterns:
        m = re.match(pat, token)
        if m:
            nid = m.group(1)
            lbl = m.group(2).strip().strip('"').strip("'")
            return nid, lbl, shape

    return token.strip('"').strip("'"), None, None


EDGE_SPLIT_RE = re.compile(
    r"(\s*(?:==>|-\.->|-->|---|-\.-[^>]*\.->|--[^>]+-->|==[^=]+==>)\s*(?:\|[^|]*\|)?\s*)"
)


def _parse_edge_operator(op_str: str) -> Tuple[str, bool, str]:
    """Return (style, has_arrow, label) from an edge operator token."""
    op = op_str.strip()
    label = ""

    # Pipe label: -->|Yes|
    pipe_m = re.search(r"\|([^|]+)\|$", op)
    if pipe_m:
        label = pipe_m.group(1).strip().strip('"')
        op = op[: pipe_m.start()].strip()

    # Inline label: -- Yes --> or -. Yes .-> or == Yes ==>
    inline_m = re.match(r"^(?:--|-\.|==)\s*(.+?)\s*(?:-->|\.->|==>)$", op)
    if inline_m:
        label = inline_m.group(1).strip().strip('"')

    if op.startswith("=="):
        return "thick", True, label
    if "-." in op or ".->" in op:
        return "dashed", op.endswith(">"), label
    if op.endswith(">"):
        return "solid", True, label
    return "solid", False, label


def _render_flowchart(source: str, is_state: bool = False) -> QPixmap:
    """Parse and render a Mermaid flowchart/graph or stateDiagram into a QPixmap."""
    lines = [ln.strip() for ln in source.splitlines() if ln.strip() and not ln.strip().startswith("%%")]
    direction = "TD"

    if lines:
        first = lines[0]
        dir_m = re.match(r"^(?:flowchart|graph)\s+(TD|TB|BT|LR|RL)\b", first, re.IGNORECASE)
        if dir_m:
            direction = dir_m.group(1).upper()
            lines = lines[1:]
        elif re.match(r"^(?:flowchart|graph|stateDiagram(?:-v2)?)\b", first, re.IGNORECASE):
            lines = lines[1:]

    nodes: Dict[str, FlowNode] = {}
    edges: List[FlowEdge] = []
    star_counter = 0

    def ensure_node(raw_tok: str) -> str:
        nonlocal star_counter
        nid, lbl, shape = _parse_node_token(raw_tok)
        if nid == "[*]":
            star_counter += 1
            nid = f"__star_{star_counter}__"
            nodes[nid] = FlowNode(node_id=nid, label="", shape="start_end")
            return nid
        if nid not in nodes:
            nodes[nid] = FlowNode(
                node_id=nid,
                label=lbl if lbl is not None else nid,
                shape=shape if shape is not None else ("round" if is_state else "rect"),
                color_idx=len(nodes) % len(NODE_PALETTE),
            )
        else:
            if lbl is not None:
                nodes[nid].label = lbl
            if shape is not None:
                nodes[nid].shape = shape
        return nid

    for raw_line in lines:
        line = raw_line.rstrip(";")
        if line.lower().startswith(("subgraph ", "end", "style ", "classdef ", "class ", "click ")):
            continue

        # State diagram colon label: StateA --> StateB : Label
        colon_label = ""
        if is_state and "-->" in line and ":" in line.split("-->", 1)[1]:
            lhs, rhs = line.split(":", 1)
            line = lhs.strip()
            colon_label = rhs.strip()

        parts = EDGE_SPLIT_RE.split(line)
        if len(parts) >= 3:
            curr_sources = [ensure_node(t) for t in parts[0].split("&") if t.strip()]
            idx = 1
            while idx + 1 < len(parts):
                op_token = parts[idx]
                target_str = parts[idx + 1]
                style, has_arrow, lbl = _parse_edge_operator(op_token)
                if colon_label and not lbl:
                    lbl = colon_label
                targets = [ensure_node(t) for t in target_str.split("&") if t.strip()]
                for s_id in curr_sources:
                    for t_id in targets:
                        edges.append(FlowEdge(src=s_id, dst=t_id, label=lbl, style=style, has_arrow=has_arrow))
                curr_sources = targets
                idx += 2
        else:
            # Standalone node definition
            if line:
                ensure_node(line)

    if not nodes:
        nodes["empty"] = FlowNode(node_id="empty", label="Empty Diagram", shape="round")

    # Measure node sizes
    font = QFont("Cantarell", 10)
    font.setWeight(QFont.Weight.DemiBold)
    fm = QFontMetricsF(font)

    for node in nodes.values():
        if node.shape == "start_end":
            node.width = 22.0
            node.height = 22.0
            continue
        text_w = fm.horizontalAdvance(node.label)
        if node.shape == "diamond":
            node.width = max(84.0, text_w + 48.0)
            node.height = max(50.0, 48.0)
        elif node.shape == "circle":
            d = max(46.0, text_w + 26.0)
            node.width = d
            node.height = d
        else:
            node.width = max(76.0, text_w + 32.0)
            node.height = 38.0

    # Assign topological layers
    in_deg: Dict[str, int] = {nid: 0 for nid in nodes}
    adj: Dict[str, List[str]] = defaultdict(list)
    for e in edges:
        if e.src != e.dst:
            adj[e.src].append(e.dst)
            in_deg[e.dst] = in_deg.get(e.dst, 0) + 1

    layer_map: Dict[str, int] = {}
    queue = deque([nid for nid, deg in in_deg.items() if deg == 0])
    if not queue and nodes:
        queue.append(next(iter(nodes.keys())))

    visited = set()
    while queue:
        u = queue.popleft()
        visited.add(u)
        u_layer = layer_map.get(u, 0)
        layer_map[u] = u_layer
        for v in adj[u]:
            if v not in visited:
                layer_map[v] = max(layer_map.get(v, 0), u_layer + 1)
            in_deg[v] -= 1
            if in_deg[v] <= 0 and v not in visited and v not in queue:
                queue.append(v)

    for nid in nodes:
        if nid not in layer_map:
            layer_map[nid] = 0

    layers: Dict[int, List[str]] = defaultdict(list)
    for nid, lyr in layer_map.items():
        layers[lyr].append(nid)

    sorted_layer_indices = sorted(layers.keys())
    if direction in ("BT", "RL"):
        sorted_layer_indices.reverse()

    is_horizontal = direction in ("LR", "RL")
    layer_gap = 68.0 if is_horizontal else 58.0
    sibling_gap = 28.0 if is_horizontal else 34.0
    pad_x = 24.0
    pad_y = 20.0

    # Compute coordinates
    if is_horizontal:
        layer_widths: List[float] = []
        layer_heights: List[float] = []
        for l_idx in sorted_layer_indices:
            nids = layers[l_idx]
            layer_widths.append(max(nodes[n].width for n in nids))
            layer_heights.append(sum(nodes[n].height for n in nids) + sibling_gap * max(0, len(nids) - 1))

        total_w = sum(layer_widths) + layer_gap * max(0, len(sorted_layer_indices) - 1) + pad_x * 2
        total_h = max(layer_heights, default=60.0) + pad_y * 2

        curr_x = pad_x
        for pos_idx, l_idx in enumerate(sorted_layer_indices):
            nids = layers[l_idx]
            lw = layer_widths[pos_idx]
            lh = layer_heights[pos_idx]
            curr_y = (total_h - lh) / 2.0
            for nid in nids:
                nd = nodes[nid]
                nd.x = curr_x + (lw - nd.width) / 2.0
                nd.y = curr_y
                curr_y += nd.height + sibling_gap
            curr_x += lw + layer_gap
    else:
        layer_widths = []
        layer_heights = []
        for l_idx in sorted_layer_indices:
            nids = layers[l_idx]
            layer_widths.append(sum(nodes[n].width for n in nids) + sibling_gap * max(0, len(nids) - 1))
            layer_heights.append(max(nodes[n].height for n in nids))

        total_w = max(layer_widths, default=120.0) + pad_x * 2
        total_h = sum(layer_heights) + layer_gap * max(0, len(sorted_layer_indices) - 1) + pad_y * 2

        curr_y = pad_y
        for pos_idx, l_idx in enumerate(sorted_layer_indices):
            nids = layers[l_idx]
            lw = layer_widths[pos_idx]
            lh = layer_heights[pos_idx]
            curr_x = (total_w - lw) / 2.0
            for nid in nids:
                nd = nodes[nid]
                nd.x = curr_x
                nd.y = curr_y + (lh - nd.height) / 2.0
                curr_x += nd.width + sibling_gap
            curr_y += lh + layer_gap

    dpr = 2.0
    pix = QPixmap(int(total_w * dpr), int(total_h * dpr))
    pix.setDevicePixelRatio(dpr)
    pix.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # Background card
    painter.setPen(QPen(QColor("#34343a"), 1.0))
    painter.setBrush(QBrush(QColor("#1c1c20")))
    painter.drawRoundedRect(QRectF(1.0, 1.0, total_w - 2.0, total_h - 2.0), 8.0, 8.0)

    # 1. Draw Edges
    label_font = QFont("Cantarell", 9)
    fm_lbl = QFontMetricsF(label_font)

    for edge in edges:
        u = nodes[edge.src]
        v = nodes[edge.dst]
        if is_horizontal:
            if u.x <= v.x:
                p1 = QPointF(u.x + u.width, u.y + u.height / 2.0)
                p2 = QPointF(v.x, v.y + v.height / 2.0)
            else:
                p1 = QPointF(u.x, u.y + u.height / 2.0)
                p2 = QPointF(v.x + v.width, v.y + v.height / 2.0)
        else:
            if u.y <= v.y:
                p1 = QPointF(u.x + u.width / 2.0, u.y + u.height)
                p2 = QPointF(v.x + v.width / 2.0, v.y)
            else:
                p1 = QPointF(u.x + u.width / 2.0, u.y)
                p2 = QPointF(v.x + v.width / 2.0, v.y + v.height)

        pen = QPen(QColor("#8e8e98"), 2.2 if edge.style == "thick" else 1.5)
        if edge.style == "dashed":
            pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        path = QPainterPath()
        path.moveTo(p1)
        if is_horizontal:
            mid_x = (p1.x() + p2.x()) / 2.0
            path.cubicTo(QPointF(mid_x, p1.y()), QPointF(mid_x, p2.y()), p2)
        else:
            mid_y = (p1.y() + p2.y()) / 2.0
            path.cubicTo(QPointF(p1.x(), mid_y), QPointF(p2.x(), mid_y), p2)
        painter.drawPath(path)

        if edge.has_arrow:
            _draw_arrowhead(painter, path.pointAtPercent(0.92), p2, QColor("#8e8e98"))

        if edge.label:
            mid_pt = path.pointAtPercent(0.5)
            lw = fm_lbl.horizontalAdvance(edge.label) + 12.0
            lh = 18.0
            lrect = QRectF(mid_pt.x() - lw / 2.0, mid_pt.y() - lh / 2.0, lw, lh)
            painter.setPen(QPen(QColor("#44444e"), 1.0))
            painter.setBrush(QBrush(QColor("#28282e")))
            painter.drawRoundedRect(lrect, 4.0, 4.0)
            painter.setFont(label_font)
            painter.setPen(QColor("#d1d1d6"))
            painter.drawText(lrect, int(Qt.AlignmentFlag.AlignCenter), edge.label)

    # 2. Draw Nodes
    painter.setFont(font)
    for node in nodes.values():
        nrect = QRectF(node.x, node.y, node.width, node.height)
        fill_hex, border_hex = NODE_PALETTE[node.color_idx]

        if node.shape == "start_end":
            painter.setPen(QPen(QColor("#0a84ff"), 2.0))
            painter.setBrush(QBrush(QColor("#f2f2f7")))
            painter.drawEllipse(nrect.adjusted(3.0, 3.0, -3.0, -3.0))
            continue

        painter.setPen(QPen(QColor(border_hex), 1.6))
        painter.setBrush(QBrush(QColor(fill_hex)))

        if node.shape == "diamond":
            poly = QPolygonF([
                QPointF(nrect.center().x(), nrect.top()),
                QPointF(nrect.right(), nrect.center().y()),
                QPointF(nrect.center().x(), nrect.bottom()),
                QPointF(nrect.left(), nrect.center().y()),
            ])
            painter.drawPolygon(poly)
        elif node.shape == "hex":
            inset = 12.0
            poly = QPolygonF([
                QPointF(nrect.left() + inset, nrect.top()),
                QPointF(nrect.right() - inset, nrect.top()),
                QPointF(nrect.right(), nrect.center().y()),
                QPointF(nrect.right() - inset, nrect.bottom()),
                QPointF(nrect.left() + inset, nrect.bottom()),
                QPointF(nrect.left(), nrect.center().y()),
            ])
            painter.drawPolygon(poly)
        elif node.shape == "circle":
            painter.drawEllipse(nrect)
        elif node.shape == "stadium":
            painter.drawRoundedRect(nrect, nrect.height() / 2.0, nrect.height() / 2.0)
        elif node.shape == "round":
            painter.drawRoundedRect(nrect, 8.0, 8.0)
        else:
            painter.drawRoundedRect(nrect, 4.0, 4.0)

        painter.setPen(QColor("#f2f2f7"))
        painter.drawText(nrect, int(Qt.AlignmentFlag.AlignCenter), node.label)

    painter.end()
    return pix


def _render_sequence_diagram(source: str) -> QPixmap:
    """Parse and render a Mermaid sequenceDiagram into a QPixmap."""
    participants: List[str] = []
    labels: Dict[str, str] = {}
    events: List[Tuple[str, str, str, str]] = []  # (kind, src, dst, text)

    def ensure_p(pid: str, alias: Optional[str] = None) -> str:
        pid = pid.strip()
        if pid not in participants:
            participants.append(pid)
            labels[pid] = alias.strip() if alias else pid
        elif alias:
            labels[pid] = alias.strip()
        return pid

    for raw in source.splitlines():
        line = raw.strip()
        if not line or line.startswith("%%") or line.lower().startswith("sequencediagram"):
            continue
        pm = re.match(r"^(?:participant|actor)\s+([A-Za-z0-9_.-]+)(?:\s+as\s+(.+))?$", line, re.IGNORECASE)
        if pm:
            ensure_p(pm.group(1), pm.group(2))
            continue

        nm = re.match(r"^Note\s+(?:over|right of|left of)\s+([^:]+):\s*(.+)$", line, re.IGNORECASE)
        if nm:
            targets = [t.strip() for t in nm.group(1).split(",")]
            s = ensure_p(targets[0])
            d = ensure_p(targets[-1])
            events.append(("note", s, d, nm.group(2).strip()))
            continue

        mm = re.match(r"^([A-Za-z0-9_.-]+)\s*(-->>|->>|-->|->)\s*([A-Za-z0-9_.-]+)\s*:\s*(.+)$", line)
        if mm:
            s = ensure_p(mm.group(1))
            op = mm.group(2)
            d = ensure_p(mm.group(3))
            events.append((op, s, d, mm.group(4).strip()))

    if not participants:
        participants = ["A", "B"]
        labels = {"A": "Client", "B": "Server"}

    col_w = 150.0
    pad_x = 30.0
    pad_y = 20.0
    box_h = 34.0
    row_h = 44.0

    total_w = max(240.0, len(participants) * col_w + pad_x * 2)
    total_h = pad_y * 2 + box_h * 2 + max(1, len(events)) * row_h + 24.0

    dpr = 2.0
    pix = QPixmap(int(total_w * dpr), int(total_h * dpr))
    pix.setDevicePixelRatio(dpr)
    pix.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    painter.setPen(QPen(QColor("#34343a"), 1.0))
    painter.setBrush(QBrush(QColor("#1c1c20")))
    painter.drawRoundedRect(QRectF(1.0, 1.0, total_w - 2.0, total_h - 2.0), 8.0, 8.0)

    p_centers: Dict[str, float] = {}
    for idx, pid in enumerate(participants):
        cx = pad_x + col_w * idx + col_w / 2.0
        p_centers[pid] = cx
        # Lifeline
        lifeline_pen = QPen(QColor("#484852"), 1.3)
        lifeline_pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(lifeline_pen)
        painter.drawLine(QPointF(cx, pad_y + box_h), QPointF(cx, total_h - pad_y - box_h))

    # Draw Messages & Notes
    msg_font = QFont("Cantarell", 9)
    painter.setFont(msg_font)
    curr_y = pad_y + box_h + 26.0

    for kind, src, dst, text in events:
        x1 = p_centers[src]
        x2 = p_centers[dst]
        if kind == "note":
            left_x = min(x1, x2) - 45.0
            right_x = max(x1, x2) + 45.0
            nrect = QRectF(left_x, curr_y - 14.0, right_x - left_x, 26.0)
            painter.setPen(QPen(QColor("#ff9f0a"), 1.2))
            painter.setBrush(QBrush(QColor("#33291a")))
            painter.drawRoundedRect(nrect, 4.0, 4.0)
            painter.setPen(QColor("#ffd60a"))
            painter.drawText(nrect, int(Qt.AlignmentFlag.AlignCenter), text)
        else:
            pen = QPen(QColor("#64d2ff" if ">>" in kind else "#98989d"), 1.5)
            if kind.startswith("--"):
                pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            if src == dst:
                path = QPainterPath()
                path.moveTo(x1, curr_y - 6.0)
                path.lineTo(x1 + 28.0, curr_y - 6.0)
                path.lineTo(x1 + 28.0, curr_y + 8.0)
                path.lineTo(x1, curr_y + 8.0)
                painter.drawPath(path)
                _draw_arrowhead(painter, QPointF(x1 + 10.0, curr_y + 8.0), QPointF(x1, curr_y + 8.0), QColor("#64d2ff"))
                painter.setPen(QColor("#e5e5ea"))
                painter.drawText(QPointF(x1 + 34.0, curr_y + 4.0), text)
            else:
                painter.drawLine(QPointF(x1, curr_y), QPointF(x2, curr_y))
                _draw_arrowhead(painter, QPointF(x1, curr_y), QPointF(x2, curr_y), QColor("#64d2ff"))
                painter.setPen(QColor("#e5e5ea"))
                trect = QRectF(min(x1, x2), curr_y - 20.0, abs(x2 - x1), 18.0)
                painter.drawText(trect, int(Qt.AlignmentFlag.AlignCenter), text)
        curr_y += row_h

    # Draw Participant Header & Footer Boxes
    p_font = QFont("Cantarell", 10)
    p_font.setWeight(QFont.Weight.Bold)
    painter.setFont(p_font)
    for idx, pid in enumerate(participants):
        cx = p_centers[pid]
        fill_hex, border_hex = NODE_PALETTE[idx % len(NODE_PALETTE)]
        for top_y in (pad_y, total_h - pad_y - box_h):
            brect = QRectF(cx - 52.0, top_y, 104.0, box_h)
            painter.setPen(QPen(QColor(border_hex), 1.5))
            painter.setBrush(QBrush(QColor(fill_hex)))
            painter.drawRoundedRect(brect, 6.0, 6.0)
            painter.setPen(QColor("#ffffff"))
            painter.drawText(brect, int(Qt.AlignmentFlag.AlignCenter), labels[pid])

    painter.end()
    return pix


def _render_pie_chart(source: str) -> QPixmap:
    """Parse and render a Mermaid pie chart into a QPixmap."""
    title = ""
    slices: List[Tuple[str, float]] = []

    for raw in source.splitlines():
        line = raw.strip()
        if not line or line.startswith("%%"):
            continue
        tm = re.match(r"^(?:pie\s+)?title\s+(.+)$", line, re.IGNORECASE)
        if tm:
            title = tm.group(1).strip()
            continue
        sm = re.match(r'^"([^"]+)"\s*:\s*([0-9.]+)$', line)
        if sm:
            slices.append((sm.group(1), float(sm.group(2))))

    if not slices:
        slices = [("Empty", 1.0)]

    total_w = 380.0
    total_h = 210.0
    dpr = 2.0
    pix = QPixmap(int(total_w * dpr), int(total_h * dpr))
    pix.setDevicePixelRatio(dpr)
    pix.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    painter.setPen(QPen(QColor("#34343a"), 1.0))
    painter.setBrush(QBrush(QColor("#1c1c20")))
    painter.drawRoundedRect(QRectF(1.0, 1.0, total_w - 2.0, total_h - 2.0), 8.0, 8.0)

    if title:
        tfont = QFont("Cantarell", 11)
        tfont.setWeight(QFont.Weight.Bold)
        painter.setFont(tfont)
        painter.setPen(QColor("#f2f2f7"))
        painter.drawText(QRectF(0, 8, total_w, 22), int(Qt.AlignmentFlag.AlignCenter), title)

    pie_rect = QRectF(28.0, 38.0, 146.0, 146.0)
    total_val = max(1e-6, sum(v for _, v in slices))
    start_angle = 90 * 16

    lfont = QFont("Cantarell", 9)
    painter.setFont(lfont)

    for idx, (lbl, val) in enumerate(slices):
        span_angle = -int(round((val / total_val) * 360 * 16))
        _, color_hex = NODE_PALETTE[idx % len(NODE_PALETTE)]
        painter.setPen(QPen(QColor("#1c1c20"), 1.5))
        painter.setBrush(QBrush(QColor(color_hex)))
        painter.drawPie(pie_rect, start_angle, span_angle)
        start_angle += span_angle

        # Legend item
        ly = 46.0 + idx * 24.0
        if ly < total_h - 16.0:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(color_hex)))
            painter.drawRoundedRect(QRectF(198.0, ly, 12.0, 12.0), 3.0, 3.0)
            pct = (val / total_val) * 100.0
            painter.setPen(QColor("#e5e5ea"))
            painter.drawText(QPointF(218.0, ly + 10.5), f"{lbl} ({pct:.0f}%)")

    painter.end()
    return pix


def _draw_arrowhead(painter: QPainter, from_pt: QPointF, to_pt: QPointF, color: QColor) -> None:
    """Draw a filled triangular arrowhead pointing at to_pt."""
    dx = to_pt.x() - from_pt.x()
    dy = to_pt.y() - from_pt.y()
    angle = math.atan2(dy, dx)
    size = 7.5

    p1 = QPointF(
        to_pt.x() - size * math.cos(angle - math.pi / 6),
        to_pt.y() - size * math.sin(angle - math.pi / 6),
    )
    p2 = QPointF(
        to_pt.x() - size * math.cos(angle + math.pi / 6),
        to_pt.y() - size * math.sin(angle + math.pi / 6),
    )

    painter.save()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(color))
    painter.drawPolygon(QPolygonF([to_pt, p1, p2]))
    painter.restore()


def render_mermaid_to_pixmap(source: str) -> QPixmap:
    """Render a Mermaid diagram string into a cached high-DPI QPixmap."""
    clean = source.strip()
    key = (clean, 1)
    cached = _MERMAID_CACHE.get(key)
    if cached is not None:
        return cached

    first_line = clean.splitlines()[0].strip().lower() if clean else ""
    if first_line.startswith("sequencediagram"):
        pix = _render_sequence_diagram(clean)
    elif first_line.startswith("pie"):
        pix = _render_pie_chart(clean)
    elif first_line.startswith("statediagram"):
        pix = _render_flowchart(clean, is_state=True)
    else:
        pix = _render_flowchart(clean, is_state=False)

    if len(_MERMAID_CACHE) > 64:
        _MERMAID_CACHE.clear()
    _MERMAID_CACHE[key] = pix
    return pix
