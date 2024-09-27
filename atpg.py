import re
import time
import sys
from enum import Enum
from collections import defaultdict
import json



def evaluate_gate(gate, inputs=[]):
    """Evaluate the output of a single gate given its inputs.
    Also, supports the 'x' state for the input.
    """


    if gate == "BUF":
        return inputs[0]

    elif gate == "NOT":
        if inputs[0] == 'x':
            return inputs[0]
        return 1 - inputs[0]

    elif gate == "NAND":
        if inputs[0] == 'x' or inputs[1] =='x':
            return 'x'
        return 1 - (inputs[0] & inputs[1])

    elif gate == "AND":
        if inputs[0] == 0 or inputs[1] == 0:
            return 0
        elif inputs[0] == 'x' or inputs[1] =='x':
            return 'x'
        return inputs[0] & inputs[1]

    elif gate == "OR":
        if inputs[0] == 1 or inputs[1] == 1:
            return 1
        elif inputs[0] == 'x' or inputs[1] =='x':
            return 'x'

        return 0 

    elif gate == "XOR":
        
        if inputs[0] == 'x' or inputs[1] =='x':
            return 'x'

        return inputs[0] ^ inputs[1]

    elif gate == "NOR":
        
        if inputs[0] == 1 or inputs[1] == 1:
            return 0
        elif inputs[0] == 'x' or inputs[1] == 'x':
            return 'x'
        
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

