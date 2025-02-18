import re
import time
import sys
from enum import Enum
from collections import defaultdict
import json
import copy

import textwrap


from atpg.parser import Parser
from atpg.utils import GIN, ERR, TST


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
    Implements the PODEM (Path-Oriented Decision Making) algorithm for generating
    test vectors in digital circuits.

    Attributes:
        gate_level_map (list): Gates organized in evaluation order.
        gates_map (dict): Maps gate numbers to their types and attributes.
        wires_map (dict): Maps wires to circuit connections.
        PI (list): Primary inputs.
        PO (list): Primary outputs.

    Methods:
        get_objective: Determines the fault detection objective for a gate.
        backtrace: Traces from a fault to find required input assignments.
        x_path_check: Checks for a fault propagation path.
        try_sensitize: Attempts to sensitize a fault.
        implication_with_fault: Propagates fault through circuit.
        propagate_values_to_pos: Attempts fault propagation to primary outputs.
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
            raise ValueError(ERR, "ATPG.get_objective: Invalid Error Type: ", error)
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

        print(GIN, "ATPG.try_sensitize: current PIs vals", pi_values)
        print(
            GIN, "ATPG.try_sensitize: Fault Location and Value: ", fault_location, value
        )
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

        elif simulated_values[fault_location] == "x":
            pi_values = self.try_sensitize(
                fault, fault_location, new_pi_values, pis, value, i + 1, results
            )
            if pi_values:
                results.extend(pi_values)

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
        print(GIN, "ATPG.implication_with_fault: Simulated Values: ", simulated_values)

        return simulated_values

    def propagate_values_to_pos(self, fault, sensitization_inputs):
        """Search for inputs which propagate the Error to the Primary Output"""
        fault_location = fault.gate_no
        fault_value = fault.error

        po_values = {po: "x" for po in self.PO}

        for inputs in sensitization_inputs:
            if self.try_propagate_to_pos(fault, inputs):
                print(
                    GIN,
                    "ATPG.propagate_values_to_pos: Fault successfully propagated with inputs:",
                    inputs,
                )
                return inputs  # Return the successful input configuration

        print(
            ERR,
            "ATPG.propagate_values_to_pos: Unable to propagate fault to primary outputs",
        )
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


class SequentialATPG(ATPG):
    def __init__(
        self,
        gate_level_map,
        gates_map,
        wires_map,
        primary_inputs,
        primary_outputs,
        state_vars,
    ):
        self.sequentialATPG = ATPG(
            gate_level_map,
            gates_map,
            wires_map,
            primary_inputs,
            primary_outputs,
            state_vars,
        )
        self.state_vars = state_vars

        self.circuit = self.unroll_circuit()

    @staticmethod
    def sequential_depth(gate_level_map, gates_map):
        """Calculate the depth of a sequential circuit"""
        max_levels = 0

        for level in gate_level_map:
            for gate in gate_level_map[level]:
                if gates_map[gate]["gate_type"] == "DFF":
                    max_levels = max(max_levels, level)
                    continue

        sequential_depth = max_levels + 1
        return sequential_depth

    def unroll_circuit(self):
        """Unroll the sequential circuit for ATPG"""
        seqATPG = self.sequentialATPG

        gate_level_map = seqATPG.gate_level_map
        gates_map = seqATPG.gates_map
        wires_map = seqATPG.wires_map
        state_vars = self.state_vars

        dff_gates_level = {}
        dff_gates = [i for i in state_vars]

        for level, gates in gate_level_map.items():
            for gate in gates:
                if gate in dff_gates:
                    dff_gates_level[gate] = level

        sequential_depth = self.sequential_depth(gate_level_map, gates_map)

        new_wires_map = {}
        new_gates_map = {}

        max_gate_no = max([int(gate) for gate in gates_map])

        for wire in wires_map:
            new_wires_map[wire] = wires_map[wire]
            for i in range(sequential_depth):
                new_wire_dict = {}
                for gate in wires_map[wire]:
                    new_wire_dict[str(int(gate) + max_gate_no * (i + 1))] = wires_map[
                        wire
                    ][gate]
                new_wires_map[wire + f"_{i}"] = new_wire_dict

        for gate in gates_map:
            new_gates_map[gate] = gates_map[gate]
            for i in range(sequential_depth):
                new_dict = {}
                for param in gates_map[gate]:
                    if param != "gate_type" and param != "level":
                        new_dict[param] = [
                            wire + f"_{i}" for wire in gates_map[gate][param]
                        ]
                new_gates_map[int(gate) + max_gate_no * (i + 1)] = new_dict

        new_wires_map["dummy_input"] = {}
        new_wires_map["dummy_output"] = {"-1": "input"}
        new_gates_map[-1] = {
            "gate_type": "dummy",
            "inputs": [],
            "outputs": ["dummy_output"],
        }

        # Re-wire the circuit
        for gate in dff_gates:
            next_inputs = copy.deepcopy(new_gates_map[gate]["inputs"])
            if not new_gates_map[gate]["inputs"]:
                new_gates_map[gate]["inputs"] = ["dummy_input"]
            elif "dummy_input" not in new_gates_map[gate]["inputs"]:
                new_gates_map[gate]["inputs"].append("dummy_input")
            new_wires_map["dummy_input"][str(gate)] = "input"

            for i in range(sequential_depth):
                next_gate = int(gate) + max_gate_no * (i + 1)

                if next_gate not in new_gates_map:
                    raise KeyError(f"Gate {next_gate} not found in new_gates_map.")

                temp_next_inputs = copy.deepcopy(new_gates_map[next_gate]["inputs"])

                new_gates_map[next_gate]["inputs"] = next_inputs

                if i == sequential_depth - 1:
                    for input in next_inputs:
                        if str(next_gate) in new_wires_map[input]:
                            new_wires_map[input].pop(str(next_gate))
                        new_wires_map[input]["-1"] = "input"
                        new_gates_map[-1]["inputs"].append(input)

                next_inputs = temp_next_inputs

        print(GIN, "SeqATPG.unroll_circuit: new_wires_map: \n", new_wires_map)
        print(GIN, "SeqATPG.unroll_circuit: new_gates_map: \n", new_gates_map)

        return new_gates_map, new_wires_map
