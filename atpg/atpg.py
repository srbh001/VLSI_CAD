import re
import time
import sys
from enum import Enum
from collections import defaultdict
import json


inversion = {"D": "~D", "~D": "D", "x": "x"}


class ATPG:
    """
    The ATPG (Automatic Test Pattern Generation) class implements the PODEM (Path-Oriented Decision Making) algorithm to generate test vectors for fault detection in digital circuits.

    Attributes:
        levelized_gates (list): A list of gates organized in levelized order based on their evaluation dependencies.
        gates_dict (dict): A mapping of gate numbers to their respective gate types and attributes.
        wires_map (dict): A mapping of wire names or numbers to the connections in the circuit.

    Methods:
        __init__: Initializes the ATPG class with levelized gates, a gate map, and a wire map.

        get_objective: Determines the fault detection objective for a given gate as part of the PODEM algorithm. This involves identifying necessary input conditions to activate and propagate the fault.

        backtrace: Implements the backtrace step of the PODEM algorithm, tracing from a fault objective to determine the required input assignments to achieve fault activation and propagation.

        x_path_check: Checks for the existence of an X-path, a path that may allow fault propagation, which is critical in determining the success of the test vector.

        evaluate_gate: A static method that computes the output of a given gate based on its inputs, supporting five-valued logic (1, 0, D, ~D, x), and is used during fault simulation within the PODEM process.
    """

    def __init__(self, levelized_gates, gates_map, wires_map):
        self.levelized_gates = levelized_gates
        self.gates_dict = gates_map
        self.wires_map = wires_map

    def get_objective(self, gate_type, gate_no, gate_inputs, objective):
        """Returns the objective for the gate"""
        pass

    def backtrace(self, objective):
        pass

    def x_path_check(self, error):
        """ """
        pass

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
                    return "D"
                elif inputs[0] == "D":
                    return 1
                elif inputs[0] == "~D":
                    return 0

            elif inputs[0] == "~D":
                if inputs[1] == 1:
                    return "D"
                elif inputs[1] == 0:
                    return "D"
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
