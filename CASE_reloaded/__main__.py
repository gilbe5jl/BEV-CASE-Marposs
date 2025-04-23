import os
import subprocess
import sys
from utils import print_red
from clean_up import *
from __machine__ import *

# def run_target_python_file(file_path):
#     """
#     Run a target Python file as a separate process.

#     Args:
#         file_path (str): The full path to the Python file to run.
#     """
#     try:
#         delete_old_logs(1)
#         python_executable = sys.executable  # Get the path to the Python interpreter
#         subprocess.Popen([python_executable, file_path])
#     except Exception as e:
#         print(f"Error in {file_path}: {e}")


# def start_cycles(part_name: str, machine_num: str):
#     """
#     Start the inspection cycles for the specified machine.
#     Starts a separate process for each machine.
    
#     Args:
#         machine_num (str): The machine number string.
#         part_name (str): The part name.
#     """
#     try:
#         # Get the path to the current script's directory
#         current_directory = os.path.dirname(os.path.abspath(__file__))
#         machine_file = os.path.join(current_directory, "__machine__.py")
        
#         # Run the target Python file (__machine__.py) in a new process
#         python_executable = sys.executable  # Path to the Python interpreter
#         subprocess.Popen([python_executable, machine_file, part_name, machine_num])
#     except Exception as e:
#         print(f"Error in starting process for machine {machine_num}: {e}")

# if __name__ == "__main__":
#     part_name = "CASE"  # Set the part name for both processes
    
#     # Start two processes with different machine numbers
#     start_cycles(part_name,'3')  # Start cycle for machine 3
#     start_cycles(part_name,'4')  # Start cycle for machine 4
#     print("PLC - Keyence Automation, BEV Porosity Case | House X76 & X77\n")


# from multiprocessing import Process
# import __machine__

# def run_machine_instance(params):
#     # You might need to modify this to pass the correct parameters to __machine__
#     __machine__.run(params)  # Adjust `run` to the main callable in __machine__

# if __name__ == "__main__":
#     # Define the different parameters for each instance
#     params_1 = {"param1": "value1", "param2": "value2"}
#     params_2 = {"param1": "value3", "param2": "value4"}

#     # Create two processes
#     process1 = Process(target=run_machine_instance, args=(params_1,))
#     process2 = Process(target=run_machine_instance, args=(params_2,))

#     # Start the processes
#     process1.start()
#     process2.start()

#     # Join the processes (optional, depends on your application needs)
#     process1.join()
#     process2.join()

    # import subprocess

if __name__ == "__main__":
    # Define parameters for each instance
    params_1 = ["python3", "__machine__.py", "CASE", "3"]
    params_2 = ["python3", "__machine__.py", "CASE", "4"]

    # Run both instances
    subprocess.Popen(params_1)
    subprocess.Popen(params_2)