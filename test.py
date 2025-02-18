import re

# Updated regex patterns
multival = r"(\b(input|output|wire)\b)\s*\[(\d+):\d+\]\s*(\w+)\s*;"
wire_re = r"wire\s*\[(\d+):\d+\]\s*([\w\d_]+)\s*;"
input_re = r"input\s*(\[\d+:\d+\])?\s*([\w\d_]+)\s*;"
output_re = r"output\s*(\[\d+:\d+\])?\s*([\w\d_]+)\s*;"


def main():
    filepath = "./test/assign.test"

    with open(filepath, "r") as f:
        for line in f.readlines():
            line = line.strip()  # Strip newline and other trailing/leading spaces

            # Match multi-bit inputs/outputs/wires
            multival_match = re.search(multival, line)
            if multival_match:
                print("Multival Match:")
                print("Type:", multival_match.group(1))  # input/output/wire
                print("Bit Width:", multival_match.group(3))  # Bit width
                print("Signal Name:", multival_match.group(4))  # Signal name

            # # Match single-bit wires (without range)
            # wire_re_match = re.search(wire_re, line)
            # if wire_re_match:
            #     print("Wire Match:")
            #     print("Bit Width:", wire_re_match.group(1))  # Bit width
            #     print("Signal Name:", wire_re_match.group(2))  # Signal name


if __name__ == "__main__":
    main()
