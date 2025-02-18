from graphviz import Digraph

# Given levelized dictionary
#
gates_map = {
    "1": {
        "gate_type": "OR",
        "inputs": [
            "b",
            "carryin"
        ],
        "outputs": [
            "_02_"
        ]
    },
    "21": {
        "gate_type": "NAND",
        "inputs": [
            "b",
            "carryin"
        ],
        "outputs": [
            "_03_"
        ]
    },
    "26": {
        "gate_type": "NAND",
        "inputs": [
            "_02_",
            "_03_"
        ],
        "outputs": [
            "_04_"
        ]
    },
    "31": {
        "gate_type": "NAND",
        "inputs": [
            "a",
            "_04_"
        ],
        "outputs": [
            "_05_"
        ]
    },
    "36": {
        "gate_type": "OR",
        "inputs": [
            "a",
            "_04_"
        ],
        "outputs": [
            "_00_"
        ]
    },
    "41": {
        "gate_type": "NAND",
        "inputs": [
            "_05_",
            "_00_"
        ],
        "outputs": [
            "y"
        ]
    },
    "46": {
        "gate_type": "NAND",
        "inputs": [
            "a",
            "_02_"
        ],
        "outputs": [
            "_01_"
        ]
    },
    "51": {
        "gate_type": "NAND",
        "inputs": [
            "_03_",
            "_01_"
        ],
        "outputs": [
            "carryout"
        ]
    }
}

wires_map = {
    "_00_": {
        "36": "output",
        "41": "input"
    },
    "_01_": {
        "46": "output",
        "51": "input"
    },
    "_02_": {
        "1": "output",
        "26": "input",
        "46": "input"
    },
    "_03_": {
        "21": "output",
        "26": "input",
        "51": "input"
    },
    "_04_": {
        "26": "output",
        "31": "input",
        "36": "input"
    },
    "_05_": {
        "31": "output",
        "41": "input"
    },
    "a": {
        "31": "input",
        "36": "input",
        "46": "input"
    },
    "b": {
        "1": "input",
        "21": "input"
    },
    "carryin": {
        "1": "input",
        "21": "input"
    },
    "carryout": {
        "51": "output"
    },
    "y": {
        "41": "output"
    }
}




levelized_dict = {
    "0": [1, 21],
    "1": [46, 26],
    "2": [31, 36, 51],
    "3": [41]
}

# Generate the diagram
def generate_columnar_levels(levelized_dict, filename='columnar_levels'):
    dot = Digraph(format='png')
    dot.attr(rankdir='TB')  # Top-to-Bottom layout for each level

    # Create columns for levels
    max_gates = max(len(nodes) for nodes in levelized_dict.values())  # Maximum gates in any level
    levels = sorted(levelized_dict.keys(), key=int)

    # Create the graph
    for level in levels:
        row = []  # Collect nodes for the current row
        for i in range(max_gates):
            nodes = levelized_dict[level]
            if i < len(nodes):  # If the current row exists in this level
                gate_type = gates_map[str(nodes[i])]["gate_type"]

                node = f'{gate_type} {nodes[i]}'
                dot.node(f'L{level}_G{nodes[i]}', node, shape='box')
                row.append(f'L{level}_G{nodes[i]}')
            # else:  # Add an invisible placeholder to maintain alignment
            #     placeholder = f'Placeholder_{level}_{i}'
            #     dot.node(placeholder, '', shape='none', width='0', height='0')
            #     row.append(placeholder)



    # Render the diagram
    dot.render(filename, cleanup=True)
    print(f"Diagram saved as {filename}.png")

# Generate the diagram
# generate_columnar_levels(levelized_dict)
def generate_columnar_levels_with_spacing(levelized_dict, gates_map, wires_map, filename='columnar_levels_fixed'):
    dot = Digraph(format='png')
    dot.attr(rankdir='LR')  # Left-to-right layout
    dot.attr(splines='ortho')  # Force orthogonal edges for 90-degree turns
    dot.attr(ranksep='1.5', nodesep='1.0')  # Increase spacing between levels and nodes

    # Create nodes for gates
    for level, nodes in levelized_dict.items():
        with dot.subgraph() as sub:
            sub.attr(rank='same')  # Align nodes in the same level
            for gate_id in nodes:
                gate_info = gates_map[str(gate_id)]
                gate_label = f'{gate_info["gate_type"]}\n{gate_id}'
                sub.node(f'G{gate_id}', gate_label, shape='box', margin="0.2,0.2")  # Add padding around the text

    # Create edges for wires with specific entry/exit points
    for wire, connections in wires_map.items():
        for src_gate, src_type in connections.items():
            for dst_gate, dst_type in connections.items():
                if src_type == 'output' and dst_type == 'input':
                    dot.edge(
                        f'G{src_gate}', f'G{dst_gate}',
                        xlabel=wire,  # Use xlabel for orthogonal edges
                        tailport='ns',  # Exit from the right side of the source
                        headport='nw'   # Enter from the left side of the destination
                    )

    # Render the diagram
    dot.render(filename, cleanup=True)
    print(f"Diagram saved as {filename}.png")

# Generate the updated diagram
generate_columnar_levels_with_spacing(levelized_dict, gates_map, wires_map)
