import re
import time
import sys
from enum import Enum
from collections import defaultdict
import json

import textwrap

inversion = {"D": "~D", "~D": "D", "x": "x"}


class Objective:
    def __init__(self, gate_no, value, fault):
        self.Gate_No = gate_no
        self.Value = value
        self.Fault = fault


class ATPG:
    """
    The ATPG (Automatic Test Pattern Generation) class implements the PODEM
    (Path-Oriented Decision Making) algorithm to generate test vectors for fault
    detection in digital circuits.

    Attributes:
        gate_level_map (list): A list of gates organized in levelized order
        based on their evaluation dependencies.

        gates_map (dict): A mapping of gate numbers to their respective gate
        types and attributes.

        wires_map (dict): A mapping of wire names or numbers to the connections
        in the circuit.

    Methods:
        __init__: Initializes the ATPG class with levelized gates, a gate map,
        and a wire map.

        get_objective: Determines the fault detection objective for a given
        gate as part of the PODEM algorithm.

        backtrace: Implements the backtrace step of the PODEM algorithm,
        tracing from a fault objective to determine the required input
        assignments to achieve fault activation and propagation.

        x_path_check: Checks for the existence of an X-path, a path that may
        allow fault propagation.

        evaluate_gate: Computes the output of a given
        gate based on its inputs, supporting five-valued logic (1, 0, D, ~D,
        x).
    """

    def __init__(
        self, gate_level_map, gates_map, wires_map, primary_inputs, primary_outputs
    ):
        self.gate_level_map = gate_level_map
        self.gates_map = gates_map
        self.wires_map = wires_map
        self.wires_val = {}
        self.objective = {}

        self.PI = primary_inputs
        self.PO = primary_outputs
        self.max_levels = max([i for i in self.gate_level_map])

        for wire in self.wires_map:
            self.wires_val[wire] = "x"

    def get_objective(self, gate_type, gate_no, gate_inputs, objective):
        """Returns the objective for the gate"""
        pass

    def backtrace(self, objective: Objective):
        """
        objective: Objective (contains Gate_No, Value, Fault)
        Returns:
            List of primary input (PI) gates connected to the given location (Objective Gate_No)
        """
        cs_gates = []
        primary_gates = []
        for pi in self.PI:
            for gate in self.wires_map[pi]:
                if self.wires_map[pi][gate] == "input":
                    primary_gates.append(int(gate))

        # print("[INFO]: backtrace: PI Gates: ", primary_gates)
        primary_inputs = []
        l = objective.Gate_No
        for gate in self.wires_map[l]:
            if self.wires_map[l][gate] == "output":
                cs_gates.append(int(gate))

        while len(cs_gates) > 0:
            # print("[INFO]: backtrace: Current State Gates: ", cs_gates)

            for gate in cs_gates:
                inputs = self.gates_map[gate]["inputs"]

                if gate in primary_gates:
                    for i in inputs:
                        if (
                            self.wires_val[i] == "x"
                            and i not in primary_inputs
                            and i in self.PI
                        ):
                            primary_inputs.append(i)

                for i in inputs:
                    new_gates = [
                        int(g)
                        for g in self.wires_map[i]
                        if self.wires_map[i][g] == "output"
                    ]
                    cs_gates.extend(new_gates)
                cs_gates.remove(gate)

        return primary_inputs

    def x_path_check(self, location):
        """
        Check if there exists an X-path (fault propagation path) from the given wire location to any primary output.

        Args:
            location (int): The wire number where the X-path check starts.

        Returns:
            bool:
                - True if an X-path exists, i.e., there is a fault propagation path from the given wire location
                  to a primary output and the output value is 'x'.
                - False if no such path exists.

        """
        cs_gates = []

        po_gates = []

        for po in self.PO:
            for gate in self.wires_map[po]:
                if self.wires_map[po][gate] == "output":
                    po_gates.append(int(gate))
        # print("[INFO]: X-path: PO Gates: ", po_gates)
        l = location
        for gate in self.wires_map[l]:
            if self.wires_map[l][gate] == "input":
                cs_gates.append(int(gate))

        while len(cs_gates) > 0:
            # print("[Info] X-path: Current State Gates: ", cs_gates)
            for gate in cs_gates:
                # print(self.gates_map)
                op = self.gates_map[gate]["outputs"][0]

                op_val = self.wires_val[op]

                if gate in po_gates and op_val == "x":
                    return True

                l = op

                cs_gates_to_add = [
                    int(g) for g in self.wires_map[l] if self.wires_map[l][g] == "input"
                ]
                # print("[Info] X-path: Gates to Add: ", cs_gates_to_add)

                cs_gates.remove(gate)

                if cs_gates_to_add:
                    cs_gates.extend(cs_gates_to_add)
        return False

    @staticmethod
    def evaluate_gate(gate, inputs=[]):
        """
        Evaluate the output of a single gate given its inputs.
        Also, supports the 'x', 'D', or '~D' state for the input.
        """

        if gate == "BUF":
            return inputs[0]

        elif gate == "NOT":
            if inputs[0] == "x" or inputs[0] == "D" or inputs[0] == "~D":
                return inversion[inputs[0]]

            return 1 - inputs[0]

        elif gate == "NAND":
            if inputs[0] == 0 or inputs[1] == 0:
                return 1

            elif inputs[0] == "x" or inputs[1] == "x":
                if "D" == inputs[0] or "D" == inputs[1]:
                    return "~D"
                return "x"

            elif inputs[0] == "D" or inputs[1] == "D":
                return "D"  # already took care of case where it is independent of D.

            elif inputs[0] == "~D" or inputs[1] == "~D":
                return "D"

            return 1 - (inputs[0] & inputs[1])

        elif gate == "AND":
            if inputs[0] == 0 or inputs[1] == 0:
                return 0

            elif inputs[0] == "D" or inputs[1] == "D":
                return "D"

            elif inputs[0] == "x" or inputs[1] == "x":
                return "x"

            elif inputs[0] == "~D" or inputs[1] == "~D":
                return "~D"  # only possible other input is 1

            return inputs[0] & inputs[1]

        elif gate == "OR":
            if inputs[0] == 1 or inputs[1] == 1:
                return 1

            elif inputs[0] == "~D" or inputs[1] == "~D":
                return "~D"

            elif inputs[0] == "x" or inputs[1] == "x":
                return "x"

            elif inputs[0] == "D" or inputs[1] == "x":
                return "D"

            return 0

        elif gate == "XOR":
            if inputs[0] == "x" or inputs[1] == "x":
                return "x"

            elif inputs[0] == "D":
                if inputs[1] == 1:
                    return "~D"
                elif inputs[1] == 0:
                    return "D"
                elif inputs[1] == "D":
                    return 0
                elif inputs[1] == "~D":
                    return 1
            elif inputs[1] == "D":
                if inputs[0] == 1:
                    return "~D"
                elif inputs[0] == 0:
                    return "D"
                elif inputs[0] == "D":
                    return 0
                elif inputs[0] == "~D":
                    return 1

            elif inputs[1] == "~D":
                if inputs[0] == 1:
                    return "D"
                elif inputs[0] == 0:
                    return "~~D"
                elif inputs[0] == "D":
                    return 1
                elif inputs[0] == "~D":
                    return 0

            elif inputs[0] == "~D":
                if inputs[1] == 1:
                    return "D"
                elif inputs[1] == 0:
                    return "~~D"
                elif inputs[1] == "D":
                    return 1
                elif inputs[1] == "~D":
                    return 0

            return inputs[0] ^ inputs[1]
 
        elif gate == "NOR":
            if inputs[0] == 1 or inputs[1] == 1:
                return 0
            elif inputs[0] == "x" or inputs[1] == "x":
                return "x"
            elif input[0] == 0:
                if(input[1] == "D"):
                    return "~D"
                elif(input[1] == "~D"):
                    return "D"
            elif input[1] == 0:
                if(input[0] == "D"):
                    return "~D"
                elif(input[0] == "~D"):
                    return "D"     
                
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

    def __repr__(self):
        debug_info = [
            f"gate_level_map: {self.gate_level_map}",
            f"gates_map: {self.gates_map}",
            f"wires_map: {self.wires_map}",
            f"wires_val: {self.wires_val}",
            f"objective: {self.objective}",
            f"primary_inputs: {self.PI}",
            f"primary_outputs: {self.PO}",
            f"max_levels: {self.max_levels}",
        ]

        # Create the debug output with [DEBUG] prefix and indentation
        indented_info = "\n".join(
            [textwrap.indent(line, "[DEBUG]: ") for line in debug_info]
        )

        return indented_info
