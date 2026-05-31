"""GraphML export for sitemap visualization."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def sitemap_json_to_graphml(data: dict[str, Any]) -> str:
    root = ET.Element("graphml", xmlns="http://graphml.graphdrawing.org/xmlns")
    ET.SubElement(root, "key", id="d0", **{"for": "node", "attr.name": "label", "attr.type": "string"})
    ET.SubElement(root, "key", id="d1", **{"for": "node", "attr.name": "type", "attr.type": "string"})
    graph = ET.SubElement(root, "graph", id="G", edgedefault="directed")

    pages = data.get("pages", [])
    path_to_id: dict[str, str] = {}
    for i, p in enumerate(pages):
        nid = f"n{i}"
        path_to_id[p.get("path", str(i))] = nid
        node = ET.SubElement(graph, "node", id=nid)
        d0 = ET.SubElement(node, "data", key="d0")
        d0.text = p.get("path", "")
        d1 = ET.SubElement(node, "data", key="d1")
        ptype = "hub" if p.get("path") in data.get("hub_paths", []) else "leaf"
        if p.get("path") in data.get("orphan_paths", []):
            ptype = "orphan"
        if p.get("path") in data.get("auth_gated_paths", []):
            ptype = "auth"
        d1.text = ptype

    for p in pages:
        src = path_to_id.get(p.get("path", ""))
        if not src:
            continue
        for out in p.get("outbound_paths") or []:
            tgt = path_to_id.get(out)
            if tgt:
                ET.SubElement(graph, "edge", source=src, target=tgt)

    return ET.tostring(root, encoding="unicode")


def load_sitemap_graphml(artifacts_root: Path, run_id: str) -> str | None:
    path = artifacts_root / "sitemaps" / f"{run_id}-sitemap.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text())
    return sitemap_json_to_graphml(data)
