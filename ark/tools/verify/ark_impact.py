"""
ARK Impact Analyzer
Анализирует влияние изменений в .ark спецификациях.

Отслеживает:
  - Какие острова затронуты изменением типа/контракта
  - Какие мосты нужно обновить
  - Какой код нужно перегенерировать
  - Какие верификации перепроверить
"""

import json
import sys
from pathlib import Path
from typing import Optional


def build_dependency_graph(ast_json: dict) -> dict:
    """Build a graph of dependencies between entities"""
    graph = {
        "nodes": {},    # name → {kind, ports_in, ports_out, data_types, ...}
        "edges": [],    # {from, to, kind, port}
    }

    for item in ast_json.get("items", []):
        kind = item.get("kind")
        name = item.get("name", item.get("target", "?"))

        if kind in ("abstraction", "class"):
            node = {
                "kind": kind,
                "name": name,
                "inherits": item.get("inherits", []),
                "data_types": [df["type"] for df in item.get("data_fields", [])],
                "in_types": [],
                "out_types": [],
                "strategies": [],
                "invariant_count": len(item.get("invariants", [])),
                "process_count": len(item.get("processes", [])),
            }
            for port in item.get("in_ports", []):
                node["in_types"].extend(f["type"] for f in port.get("fields", []))
            for port in item.get("out_ports", []):
                node["out_types"].extend(f["type"] for f in port.get("fields", []))
            for proc in item.get("processes", []):
                for m in proc.get("meta", []):
                    if isinstance(m, dict) and m.get("key") == "strategy":
                        v = m["value"]
                        if isinstance(v, dict):
                            node["strategies"].append(v.get("name", str(v)))

            graph["nodes"][name] = node

            # Inheritance edges
            for parent in item.get("inherits", []):
                graph["edges"].append({
                    "from": name, "to": parent,
                    "kind": "inherits"
                })

        elif kind == "island":
            node = {
                "kind": "island",
                "name": name,
                "strategy": item.get("strategy", "code"),
                "contains": item.get("contains", []),
                "in_types": [],
                "out_types": [],
            }
            for port in item.get("in_ports", []):
                node["in_types"].extend(f["type"] for f in port.get("fields", []))
            for port in item.get("out_ports", []):
                node["out_types"].extend(f["type"] for f in port.get("fields", []))
            graph["nodes"][name] = node

            # Contains edges
            for contained in item.get("contains", []):
                graph["edges"].append({
                    "from": name, "to": contained,
                    "kind": "contains"
                })

        elif kind == "bridge":
            from_port = item.get("from_port", "")
            to_port = item.get("to_port", "")
            from_island = from_port.split(".")[0] if "." in from_port else from_port
            to_island = to_port.split(".")[0] if "." in to_port else to_port

            graph["edges"].append({
                "from": from_island, "to": to_island,
                "kind": "bridge", "name": name,
                "from_port": from_port, "to_port": to_port,
                "has_contract": item.get("contract") is not None
            })

        elif kind == "registry":
            for entry in item.get("entries", []):
                ename = entry.get("name", "?")
                graph["edges"].append({
                    "from": "Registry:" + name,
                    "to": ename,
                    "kind": "registers"
                })

        elif kind == "verify":
            target = item.get("target", "?")
            graph["edges"].append({
                "from": "Verify:" + target,
                "to": target,
                "kind": "verifies",
                "check_count": len(item.get("checks", []))
            })

    return graph


def analyze_impact(graph: dict, changed_entity: str) -> dict:
    """Analyze what's affected when an entity changes"""
    affected = {
        "directly_affected": [],
        "bridges_affected": [],
        "islands_affected": [],
        "verifications_needed": [],
        "codegen_targets": [],
    }

    # Direct dependents (who inherits from changed?)
    for edge in graph["edges"]:
        if edge["to"] == changed_entity:
            if edge["kind"] == "inherits":
                affected["directly_affected"].append({
                    "entity": edge["from"],
                    "reason": f"inherits from {changed_entity}"
                })
            elif edge["kind"] == "contains":
                affected["islands_affected"].append({
                    "island": edge["from"],
                    "reason": f"contains {changed_entity}"
                })
            elif edge["kind"] == "verifies":
                affected["verifications_needed"].append({
                    "verify": edge["from"],
                    "reason": f"verifies {changed_entity}",
                    "checks": edge.get("check_count", 0)
                })

    # Bridges connected to changed entity or its island
    affected_islands = set([changed_entity])
    for edge in graph["edges"]:
        if edge["kind"] == "contains" and edge["to"] == changed_entity:
            affected_islands.add(edge["from"])

    for edge in graph["edges"]:
        if edge["kind"] == "bridge":
            from_island = edge.get("from_port", "").split(".")[0]
            to_island = edge.get("to_port", "").split(".")[0]
            if from_island in affected_islands or to_island in affected_islands:
                affected["bridges_affected"].append({
                    "bridge": edge.get("name", "?"),
                    "from": edge.get("from_port"),
                    "to": edge.get("to_port"),
                    "has_contract": edge.get("has_contract", False)
                })

    # Codegen targets
    node = graph["nodes"].get(changed_entity)
    if node:
        strategies = node.get("strategies", [node.get("strategy", "code")])
        affected["codegen_targets"].append({
            "entity": changed_entity,
            "targets": ["rust", "cpp"] if "tensor" in strategies else ["rust"],
            "strategies": strategies
        })

    # Transitive: affected entities also need codegen
    for item in affected["directly_affected"]:
        dep_node = graph["nodes"].get(item["entity"])
        if dep_node:
            affected["codegen_targets"].append({
                "entity": item["entity"],
                "targets": ["rust"],
                "reason": "transitive dependency"
            })

    return affected


def print_impact(impact: dict, entity: str):
    """Pretty-print impact analysis"""
    print(f"\n{'='*60}")
    print(f"  Impact Analysis: {entity}")
    print(f"{'='*60}")

    if impact["directly_affected"]:
        print(f"\n  Direct Dependencies:")
        for d in impact["directly_affected"]:
            print(f"    → {d['entity']} ({d['reason']})")

    if impact["islands_affected"]:
        print(f"\n  Islands Affected:")
        for i in impact["islands_affected"]:
            print(f"    → {i['island']} ({i['reason']})")

    if impact["bridges_affected"]:
        print(f"\n  Bridges to Verify:")
        for b in impact["bridges_affected"]:
            contract = "✓ has contract" if b["has_contract"] else "⚠ no contract"
            print(f"    → {b['bridge']}: {b['from']} → {b['to']} ({contract})")

    if impact["verifications_needed"]:
        print(f"\n  Re-verification Needed:")
        for v in impact["verifications_needed"]:
            print(f"    → {v['verify']} ({v['checks']} checks)")

    if impact["codegen_targets"]:
        print(f"\n  Code Regeneration:")
        for c in impact["codegen_targets"]:
            targets = ", ".join(c["targets"])
            print(f"    → {c['entity']} [{targets}]")

    total = (len(impact["directly_affected"]) +
             len(impact["islands_affected"]) +
             len(impact["bridges_affected"]))
    if total == 0:
        print(f"\n  ✓ No dependencies found — safe to change in isolation")


# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ARK Impact Analyzer")
    parser.add_argument("input", help=".ark or .json file")
    parser.add_argument("entity", help="Entity name to analyze impact for")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    filepath = Path(args.input)

    if filepath.suffix == ".ark":
        sys.path.insert(0, str(Path(__file__).parent.parent / "parser"))
        from ark_parser import parse, to_json
        source = filepath.read_text(encoding="utf-8")
        ark_file = parse(source)
        ast_json = json.loads(to_json(ark_file))
    else:
        ast_json = json.loads(filepath.read_text())

    graph = build_dependency_graph(ast_json)
    impact = analyze_impact(graph, args.entity)

    if args.json:
        print(json.dumps(impact, indent=2))
    else:
        print_impact(impact, args.entity)


if __name__ == "__main__":
    main()
