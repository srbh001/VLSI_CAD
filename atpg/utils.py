"""Modules containing helper functions for ATPG."""

GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"

GIN = f"{GREEN}[INFO]:  {RESET} "
ERR = f"{RED}[ERROR]:   {RESET} "
TST = f"{GREEN}[TEST]:  {RESET} "


def print_structured_design(gates_map, wires_map, level_map):
    print("\n=== CIRCUIT HIERARCHY ===")

    for level, gates in level_map.items():
        for gate in gates:
            gates_map[gate]["level"] = int(level)

    for level in sorted(level_map.keys(), key=int):
        print(f"\n── LEVEL {level} ──")
        for gate_id in level_map[level]:
            gate = gates_map[gate_id]
            inputs = [
                f"{inp} (L{find_wire_level(inp, wires_map, gates_map)})"
                for inp in gate["inputs"]
            ]

            print(f"  GATE {gate_id} [{gate['gate_type']}]")
            print(f"    Inputs: {', '.join(inputs)}")
            print(f"    Outputs: {', '.join(gate['outputs'])}")

    print("\n=== WIRE TRACING ===")
    for wire, connections in wires_map.items():
        sources = [k for k, v in connections.items() if v == "output"]
        destinations = [k for k, v in connections.items() if v == "input"]

        source_info = [f"GATE {s} (L{gates_map[int(s)]['level']})" for s in sources]
        dest_info = [f"GATE {d} (L{gates_map[int(d)]['level']})" for d in destinations]

        print(f"\nWire {wire}:")
        if not source_info:
            source_info = ["INPUT"]
        print(f"  Sources: {', '.join(source_info)}")
        print(f"  Destinations: {', '.join(dest_info)}")


def find_wire_level(wire, wires_map, gates_map):
    sources = [k for k, v in wires_map[wire].items() if v == "output"]
    if not sources:
        return -1  # Input wire case
    return max(gates_map[int(s)]["level"] for s in sources)
