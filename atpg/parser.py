"""Module which return the levelised gate level map along with the gates map and wires map"""
import os
import re
import time
import sys
from enum import Enum
from collections import defaultdict
import json
import textwrap




from atpg import ATPG

gate = Enum("GATE", ["BUF", "NAND", "NOR", "OR", "NOT", "DFF", "DFFSR"])

comment_re = r"\(\*.*?\*\)"
comment2_re = r"\/\*.*?\*\/"
module_re = r"module\s+(\w+)\s*\(([^)]+)\);"
wire_re = r"wire\s+([\w\d_]+)\s*;"
input_re = r"input\s*(\[\d+:\d+\])?\s*([\w\d_]+)\s*;"
output_re = r"output\s*(\[\d+:\d+\])?\s*([\w\d_]+)\s*;"
assign_re = r"assign\s+(\w+)\s*=\s*(\w+);"
input_output_re = re.compile(r"(input|output|inout)\s*(?:\[\d+:\d+\])?\s*(\w+);")


class Parser:
    def __init__(self, filepath) -> None:
        self.file_path = filepath
        self.INPUTS = {}
        self.gates_level_map = {}
        self.gates_dict = {}
        self.wires_map = {}

    def read_parse_file(self):
        filepath = self.file_path
        gate_level_map = {}
        INPUTS = []
        with open(filepath, "r") as f:
            code = []
            lines = f.readlines()

            code_str = ""
            for line in lines:
                line = re.sub(comment_re, " ", line).strip()
                line = re.sub(comment2_re, " ", line).strip()
                line = line.strip()
                if line:
                    code_str += line
                    code_str += "\n"
                    code.append(line)

            with open(f"{filepath}.cleaned", "w") as f:
                f.write(code_str)
                print("[INFO]: Successfully cleaned the code.")

            # ------------------- PARSING STARTS ----------------------------

            module_name = ""
            wires = []
            inputs = []
            outputs = []
            wires_dict = {}

            for i, line in enumerate(code):
                if "module" in line:
                    module_match = re.search(module_re, line)
                    if module_match and module_name == "":
                        module_name = module_match.group(1)
                        top_level_params = module_match.group(2).split(",")

                if re.search(wire_re, line):
                    wire_name = re.search(wire_re, line).group(1)
                    wires.append(wire_name)
                    wires_dict[wire_name] = {}

                io_match = input_output_re.search(line)
                if io_match:
                    io_type = io_match.group(1)
                    io_name = io_match.group(2)
                    if io_type == "input":
                        if io_name not in inputs and io_name not in wires_dict:
                            inputs.append(io_name)
                            if io_name not in INPUTS:
                                INPUTS.append(io_name)
                            wires_dict[io_name] = {}
                    elif io_type == "output":
                        if io_name not in outputs and io_name not in wires_dict:
                            outputs.append(io_name)
                            wires_dict[io_name] = {}
                    elif io_type == "inout":
                        wires_dict[io_name] = {}

                # TODO: deal with this later
                # assign_match = re.search(assign_re, line)
                # if assign_match:
                #     lhs = assign_match.group(1)
                #     rhs = assign_match.group(2)
                #     wires_dict[lhs] = {"type": "assign", "source": rhs}

            gates_map, wires_map = self.parse_gates(code, wires_dict)
            self.gates_map = gates_map
            self.wires_map = wires_map
            self.INPUTS = INPUTS

            print("-" * 10, "GATES_DICT", "_" * 10)
            print(json.dumps(gates_map, indent=4))
            print("-" * 10, "WIRES_MAP", "_" * 10)
            print(json.dumps(wires_map, indent=4))

            self.gate_level_map = self.level_graph(inputs, outputs, gates_map, wires_map)
            
    
    def simulate(self):
        print("--" * 20)
        print("\n\n Netlist Successfully Parsed.\n Entering Simulation...")
        print("\n   Options Only Enter 0 or 1 for inputs")
        print("   HELP: Enter q to exit\n\n")
        dict_inputs = {}
        if not self.INPUTS:
            print("[ERROR]: Invalid Graph. Error parsing the graph.")
        while True:
            for i in self.INPUTS:
                inp = input(f"Enter the input {i}: ")
                if inp.lower() == "q":
                    return 0
                dict_inputs[i] = int(inp)

            self.evaluate_graph(self.INPUTS, self.gate_level_map, self.gates_map, dict_inputs)



    @staticmethod
    def parse_gates(code, wires_dict):
        gate_re = re.compile(r"(\w+)\s+(\w+)\s*\(\s*")
        wire_re = re.compile(r"\.(\w+)\((\w+)\)")

        gates_dict = {}
        j = 0
        for i, line in enumerate(code):
            gate_match = gate_re.search(line)
            if gate_match:
                gate_type = gate_match.group(1)
                gate_no = j
                j += 1

                if gate_no in gates_dict:
                    gate_no += 1
                    j += 1
                gates_dict[gate_no] = {
                    "gate_type": gate_type,
                    "inputs": [],
                    "outputs": [],
                    "inouts": [],
                }

                gate_params = get_gate_params(gate_type)

                for j in range(i + 1, len(code)):
                    wire_match = wire_re.search(code[j])

                    if wire_match:
                        pin_type = wire_match.group(1)
                        wire_name = wire_match.group(2)

                        if pin_type in gate_params["inputs"]:
                            gates_dict[gate_no]["inputs"].append(wire_name)
                            wires_dict[wire_name][str(gate_no)] = "input"
                        elif pin_type in gate_params["outputs"]:
                            gates_dict[gate_no]["outputs"].append(wire_name)
                            wires_dict[wire_name][str(gate_no)] = "output"
                        elif pin_type in gate_params.get("inouts", []):
                            gates_dict[gate_no]["inouts"].append(wire_name)
                            wires_dict[wire_name][str(gate_no)] = "inout"

                    if ");" in code[j]:
                        break

        return gates_dict, wires_dict

    @staticmethod
    def level_graph(inputs, outputs, gates_dict, wires_map):
        """Returns the levelized map"""
        gate_level_map = {}

        print("--"*10)
        print("[INFO]: LEVELISING THE GATES.\n")
        level = 0
        while outputs:
            print("[LEVEL]:     Current Outputs: ", outputs)
            print("[LEVEL]:     Current Inputs: ", inputs)

            # Iterate over a copy of inputs to avoid modifying the list while iterating
            inputs_to_delete = []
            for input_wire in list(inputs):
                del_input = True

                if level not in gate_level_map:
                    gate_level_map[level] = []

                gates_to_remove = []

                for gate in wires_map[input_wire]:
                    if wires_map[input_wire][gate] == "input":
                        gate_inputs = gates_dict[int(gate)]["inputs"]

                        if all(gate_input in inputs for gate_input in gate_inputs):
                            if level == 0:
                                if int(gate) not in gate_level_map[level]:
                                    gate_level_map[level].append(int(gate))

                                    gates_to_remove.append(gate)

                            else:
                                if (
                                    int(gate) not in gate_level_map[level - 1]
                                    and int(gate) not in gate_level_map[level]
                                ):
                                    gate_level_map[level].append(int(gate))

                                    gates_to_remove.append(gate)
                        else:
                            del_input = False

                for gate in gates_to_remove:
                    wires_map[input_wire].pop(gate)

                # Only remove the input wire if all conditions are met
                if del_input:
                    inputs_to_delete.append(input_wire)

                # Check if the input_wire is also an output and handle it
                if input_wire in outputs:
                    # print("Matched Output:", input_wire)
                    outputs.remove(input_wire)

            for input in inputs_to_delete:
                inputs.remove(input)

            # Prepare new inputs for the next level
            new_inputs = []
            level += 1


            if outputs:
                for gate in gate_level_map[level - 1]:
                    gate_dict = gates_dict[gate]
                    # print("Processing Gate:", gate, gate_dict)
                    for output_wire in gate_dict["outputs"]:
                        if output_wire in outputs:
                            outputs.remove(output_wire)
                        elif output_wire not in new_inputs and output_wire not in inputs:
                            new_inputs.append(output_wire)

            inputs.extend(new_inputs)

            print("[LEVEL]     Current Gate Level Map:")
            non_idented_output= json.dumps(gate_level_map, indent=3)
            print(textwrap.indent(non_idented_output, "[LEVEL]"))
            print("=="*10)

        return gate_level_map

    @staticmethod
    def evaluate_gate_v1(gate, inputs=[]):
        """Evaluate the output of a single gate given its inputs."""

        # Ensure all necessary inputs are provided
        if gate == "BUF":
            return inputs[0]

        elif gate == "NOT":
            return 1 - inputs[0]

        elif gate == "NAND":
            return 1 - (inputs[0] & inputs[1])

        elif gate == "AND":
            return inputs[0] & inputs[1]

        elif gate == "OR":
            return inputs[0] | inputs[1]

        elif gate == "XOR":
            return inputs[0] ^ inputs[1]

        elif gate == "NOR":
            return 1 - (inputs[0] | inputs[1])

        elif gate == "DFF":
            # Assuming the DFF captures input "D" on clock "C" (rising edge), we'll just return the value of D
            return inputs[1]

        elif gate == "DFFSR":
            # DFFSR logic, simplified for now:
            # S = Set, R = Reset, C = Clock, D = Data
            # We'll assume positive logic, i.e., S=1 sets Q to 1, R=1 resets Q to 0, otherwise D determines Q.
            if inputs[1] == 1:
                return 1
            elif inputs[2] == 1:
                return 0
            else:
                return inputs[3]

        else:
            raise ValueError(f"Unknown gate: {gate}")

    @staticmethod
    def evaluate_graph(inputs, gate_level_graph, gates_dict, wires):

        max_level = 2 * max([i for i in gate_level_graph])
        max_height = 4 * max([len(gate_level_graph[i]) for i in gate_level_graph])

        HEIGHT = 2 * max_height

        for level in gate_level_graph:
            for gate in gate_level_graph[level]:
                gi = gates_dict[gate]["inputs"]
                go = gates_dict[gate]["outputs"]
                gtype = gates_dict[gate]["gate_type"]

                gi_values = [wires[i] for i in gi]

                wires[go[0]] = ATPG.evaluate_gate(gtype, gi_values)

                print("   " * (level + 2) + f"{go[0]} :   {wires[go[0]]}")




def get_gate_params(gate):
    """Returns a dict containing the inputs and outputs of the gate."""
    gate_params = {
        "BUF": {"inputs": ["A"], "outputs": ["Y"]},
        "NOT": {"inputs": ["A"], "outputs": ["Y"]},
        "NAND": {"inputs": ["A", "B"], "outputs": ["Y"]},
        "AND": {"inputs": ["A", "B"], "outputs": ["Y"]},
        "OR": {"inputs": ["A", "B"], "outputs": ["Y"]},
        "XOR": {"inputs": ["A", "B"], "outputs": ["Y"]},
        "NOR": {"inputs": ["A", "B"], "outputs": ["Y"]},
        "DFF": {"inputs": ["C", "D"], "outputs": ["Q"]},
        "DFFSR": {"inputs": ["C", "D", "S", "R"], "outputs": ["Q"]},
    }
    return gate_params.get(gate, {"inputs": [], "outputs": []})


if __name__ == '__main__':
    cwd = os.getcwd()
    file_name = './ja_out.v'
    parser = Parser(file_name)
    parser.read_parse_file()
    parser.simulate()

