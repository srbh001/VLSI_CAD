import re
import time
import sys
from enum import Enum
from collections import defaultdict
import json
import copy

import textwrap


from atpg.parser import Parser


inversion = {"D": "~D", "~D": "D", "x": "x"}


class Objective:
    def __init__(self, gate_no, value, fault):
        self.Gate_No = gate_no
        self.Value = value
        self.Fault = fault


class Fault:
    def __init__(self, gate_no, error):
        self.gate_no = gate_no
        self.error = error


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
        self,
        gate_level_map,
        gates_map,
        wires_map,
        primary_inputs,
        primary_outputs,
        state_vars,
    ):
        self.gate_level_map = gate_level_map
        self.gates_map = gates_map
        self.wires_map = wires_map
        self.wires_val = {}
        self.objective = {}

        self.PI = primary_inputs
        self.PO = primary_outputs
        self.max_levels = max([i for i in self.gate_level_map])
        self.state_vars = state_vars

        for wire in self.wires_map:
            self.wires_val[wire] = "x"

    def get_objective(self, gate_no, error):
        """Returns the objective for the gate"""

        if error == "D":
            objective = Objective(gate_no, "1", "D")
        elif error == "~D":
            objective = Objective(gate_no, "1", "~D")
        else:
            raise ValueError("[ERROR]: Invalid Error Type: ", error)
        return objective

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

    def try_sensitize(
        self, fault, fault_location, pi_values, pis, value, i=0, results=None
    ):
        """
        Recursively try to sensitize the fault by assigning '1' and '0' to the inputs.

        Args:
            fault (Fault): The fault object to be sensitized.
            fault_location (str): The location of the fault in the circuit.
            pi_values (dict): Dictionary of current primary input values.
            pis (list): List of primary inputs to test from the backtrace.
            value (str): The desired value at the fault location ('1' for 'D', '0' for '~D').
            i (int): The current index of the primary input to process (default is 0).

        Returns:
            dict: Updated pi_values if fault is sensitized, None otherwise.
        """
        # Base case: If we have processed all inputs, return None (no solution found)
        #
        if not results:
            results = []

        print("[INFO]: Try-Sensitize: current PIs vals", pi_values)
        print("[INFO]: Fault Location and Value: ", fault_location, value)
        if i >= len(pis):
            return None

        input_pi = pis[i]

        # Try setting the PI to "1" first
        new_pi_values = pi_values.copy()
        new_pi_values[input_pi] = "1"

        simulated_values = self.implication_with_fault(new_pi_values, fault=None)

        if str(simulated_values[fault_location]) == value:
            pi_values[input_pi] = "1"
            pi_values_to_add = [pi_values]
            results.extend(pi_values_to_add)
            # return pi_values  # Return the updated pi_values
        elif simulated_values[fault_location] == "x":
            pi_values = self.try_sensitize(
                fault, fault_location, new_pi_values, pis, value, i + 1, results
            )
            if pi_values:
                results.extend(pi_values)
                # return pi_values

        new_pi_values[input_pi] = "0"
        simulated_values = self.implication_with_fault(new_pi_values, fault=None)

        if str(simulated_values[fault_location]) == value:
            # pi_values[input_pi] = "0"
            results.extend([new_pi_values])
        elif simulated_values[fault_location] == "x":
            pi_values = self.try_sensitize(
                fault, fault_location, new_pi_values, pis, value, i + 1, results
            )
            if pi_values:
                results.extend(pi_values)

        return results

    def sensitize_fault(self, fault_location, fault_value):
        """
        Generate a test vector to sensitize a fault at the specified location.

        Args:
            fault_location (str): The wire or gate where the fault is located.
            fault_value (str): The value of the fault (e.g., "D" or "~D").

        Returns:
            dict: A dictionary containing the primary input values needed to sensitize the fault.
        """
        fault = Fault(fault_location, fault_value)

        pi_values = {pi: "x" for pi in self.PI}

        po_values = {po: "x" for po in self.PO}

        objectives = {}

        if self.x_path_check(fault_location):
            pis = self.backtrace(
                Objective(
                    fault_location, fault_value, "D" if fault_value == "D" else "~D"
                )
            )

            value = "1" if fault_value == "D" else "0"
            objectives[fault_location] = value

            pi_values = self.try_sensitize(fault, fault_location, pi_values, pis, value)

        return pi_values

    def implication_with_fault(self, pi_values, fault=None):
        """
        Implication with fault: Propagate the fault to the primary outputs to determine if the fault is detectable.

        """

        dict_inputs = pi_values.copy()
        primary_inputs = self.PI
        if fault is not None:
            dict_inputs[fault.gate_no] = fault.error
        gate_level_map = copy.deepcopy(self.gate_level_map)
        gates_map = copy.deepcopy(self.gates_map)

        state_vars = self.state_vars

        simulated_values = Parser.evaluate_graph(
            primary_inputs, gate_level_map, gates_map, dict_inputs, state_vars
        )
        print("[INFO]: Simulated Values: ", simulated_values)

        return simulated_values

    def propagate_values_to_pos(self, fault, sensitization_inputs):
        """Search for inputs which propagate the Error to the Primary Output"""
        fault_location = fault.gate_no
        fault_value = fault.error

        po_values = {po: "x" for po in self.PO}

        for inputs in sensitization_inputs:
            if self.try_propagate_to_pos(fault, inputs):
                print("[INFO]: Fault successfully propagated with inputs:", inputs)
                return inputs  # Return the successful input configuration

        print("[ERROR]: Unable to propagate fault to primary outputs")
        return None  # If propagation is not successful

    def try_propagate_to_pos(self, fault, inputs):
        """
        Attempt to propagate the fault by changing the 'x' values in the input.
        First try setting each 'x' to '0', and if that fails, try '1'.
        """

        for wire, value in inputs.items():
            if value == "x":
                inputs[wire] = "0"
                simulated_values = self.implication_with_fault(inputs, fault)
                if self.check_primary_output_fault_propagation(simulated_values):
                    return True

                inputs[wire] = "1"
                simulated_values = self.implication_with_fault(inputs, fault)
                if self.check_primary_output_fault_propagation(simulated_values):
                    return True

                inputs[wire] = "x"

        return False

    def check_primary_output_fault_propagation(self, simulated_values):
        pos = self.PO

        for po in pos:
            if simulated_values[po] == "D" or simulated_values[po] == "~D":
                return True

        return False

    def give_objective(gate_type):
        if gate_type == "AND":
            return ["1"]
        elif gate_type == "OR":
            return ["0"]
        elif gate_type == "NAND":
            return ["1"]
        elif gate_type == "NOR":
            return ["0"]
        elif gate_type == "XOR":
            return ["1", "0"]
        elif gate_type == "XNOR":
            return ["1", "0"]

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
