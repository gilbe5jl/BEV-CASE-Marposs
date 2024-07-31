# PLC Keyence Automation

The robot_*.py files represents the control logic for Keyence XGX-Controller(s) and an Allen-Bradley PLC. It's designed to automate the execution of various stages of a operation while monitoring and managing connections between a Programmable Logic Controller (PLC) and Keyence XGX-Controller(s). 

### `__main__.py` File

The `__main__.py` file serves as the main entry point to the program. It must be configured by specifying which modules are to be run as processes. It is executed when the program is run as a script using the command-line interface.

## Purpose

1. **Entry Point**: The central function of __main__.py is to serve as the initial point of execution when the program is invoked as a script. It hosts the code responsible for launching a variable number of processes, dynamically adjusting to the number of Keyence XGX-Controllers utilized in the system. This file orchestrates the setup and management of these processes.

2. **Initialization**: `__main__.py` includes code for initializing the program or setting up necessary configurations before the main functionality is triggered.

3. **Default Behavior**: It defines the default behavior of the program when run as a script. This includes running certain modules, and performing log roation.

## Usage

To execute the default behavior of the program, open a command prompt, navigate to the directory containing the program's main file (`__main__.py`), and run:

```bash
python __main__.py
```
```bash
# Allow dynamic specification of "robot_*.py" files for Keyence controllers
file_names = ["robot_3.py", "robot_4.py"]  # Example: Specify names of the modules to be run as separate processes here
```
### `robot_*.py` File(s)

The `robot_*.py` file(s) are designed to run as separate processes, with each file initiating two threads upon execution. One thread serves as a heartbeat, ensuring a stable connection to the PLC by regularly checking and maintaining communication. The second thread encompasses the main control logic responsible for automating communication between the Keyence XGX-Controller(s) and the PLC. This setup optimizes the system's reliability during operation.

### `keyence_utils.py` File
The `keyence_utils.py` file is a collection of functions intended to facilitate communication and interaction with a Keyence XGX-Controller. The keyence_string_generator function generates a string based on specified parameters, ensuring the correct program is loaded for the part/surface being inspected. Additionally, there are functions such as keyence_swap_check, trigger_keyence, load_keyence, exit_keyence, monitor_end_scan, and monitor_keyence_not_running, each serving distinct purposes within the automation process. These functions handle tasks such as checking and adjusting Keyence program settings, triggering Keyence operations, monitoring PLC signals for interrupting Keyence scans, and managing Keyence processing status. 

### `plc_utils.py` File
The `plc_utils.py` file comprises a set of functions designed to streamline communication and interaction with an Allen-Bradley PLC (Programmable Logic Controller). Each function within this file serves the purpose of either retrieving data from, writing data to, or clearing PLC tags.

### `utils.py` File
