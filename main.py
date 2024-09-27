from atpg import ATPG, Parser



def main():
    #file_path = input("Enter the file_name")
    
    file_path = "./test/ja_out.v"

    parser = Parser(file_path)

    parser.read_parse_file()

    gate_level_map = parser.gate_level_map
    gates_map = parser.gates_map
    wires_map = parser.wires_map

    parser.simulate()

    # TODO: Add ATPG and test vectors here.



if __name__ == "__main__":
    main()
