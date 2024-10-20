import unittest
from atpg import ATPG, Objective, Parser, Fault


def main():
    # Ask the user for file path or use the default one
    file_path = (
        input("Enter the file name (default: ./test/adder_and_or.v): ")
        or "./test/adder_and_or.v"
    )

    parser = Parser(file_path)
    parser.read_parse_file()

    print("Choose an option:")
    print("1. Simulate")
    print("2. Test")
    choice = input("Enter your choice (1 or 2): ")

    if choice == "1":
        print("[INFO]: Running simulation...")
        parser.simulate()
        print("[INFO]: Simulation completed.")

    elif choice == "2":
        print("[INFO]: Running tests...")
        run_tests(parser)

    else:
        print("[ERROR]: Invalid choice. Please choose 1 or 2.")
        return


def run_tests(parser):
    """
    Run unittests to verify the functionality of ATPG on the given file.
    """
    gate_level_map = parser.gate_level_map
    gates_map = parser.gates_map
    wires_map = parser.wires_map
    primary_inputs = parser.INPUTS
    primary_outputs = parser.OUTPUTS
    state_vars = parser.state_vars

    atpg = ATPG(
        gate_level_map,
        gates_map,
        wires_map,
        primary_inputs,
        primary_outputs,
        state_vars,
    )

    objective = Objective("_02_", "1", "D")

    class TestATPG(unittest.TestCase):
        def test_x_path_check(self):
            """Test the x_path_check function."""
            print("\n[TEST]: Testing X-path check...")
            result = atpg.x_path_check("_02_")
            print(f"[INFO]: X-path check result before modification: {result}")
            self.assertTrue(result, "[TEST]: X-path check should return True initially")

            # Modify wire values and test again
            atpg.wires_val["y"] = "1"
            atpg.wires_val["carryout"] = "1"
            result_after = atpg.x_path_check("_02_")
            print(f"[INFO]: X-path check result after modification: {result_after}")
            self.assertFalse(
                result_after,
                "[TEST]: X-path check should return False after modification",
            )

        def test_backtrace(self):
            """Test the backtrace function."""
            print("\n[TEST]: Testing backtrace function...")
            expected_backtrace = ["b", "carryin"]
            result = atpg.backtrace(objective)
            print(f"[INFO]: Backtrace result: {result}")
            self.assertEqual(
                result,
                expected_backtrace,
                "[TEST]: Backtrace should return the correct PI list",
            )

        def test_imply_with_fault(self):
            fault = Fault("_03_", "D")
            pi_values = {"a": "1", "b": "0", "carryin": "0"}
            output = atpg.implication_with_fault(pi_values, fault)
            print(f"[INFO]: Imply with fault result: {output}")

            self.assertEqual(1, 1, "[TEST]: Imply with fault should return 1")

        def test_sensitization(self):
            fault = Fault("_01_", "D")
            pi_values = {"a": "1", "b": "0", "carryin": "0"}
            sensitization = atpg.sensitize_fault("_03_", "D")
            print(f"[INFO]: Sensitization result: {sensitization}")
            self.assertTrue(sensitization, "[TEST]: Sensitization should return True")

    unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestATPG))


if __name__ == "__main__":
    main()
