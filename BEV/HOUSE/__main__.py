import os
import subprocess
import sys
# from clean_up import *
# from robot_3 import Station
# from log_handler import PhoenixLogger

# def run_target_python_file(file_path):
#     """
#     Run a target Python file as a separate process.

#     Args:
#         file_path (str): The full path to the Python file to run.
#     """
#     try:
#         # delete_old_logs(1)
#         station_nums = ['3','4']
#         logger = PhoenixLogger(station_nums)
#         logger.delete_old_logs()
#         alpha = Station(station_nums[0], logger)
#         beta = Station(station_nums[1], logger)

#         alpha.start()
#         beta.start()
#         python_executable = sys.executable  # Get the path to the Python interpreter
#         subprocess.Popen([python_executable, file_path])
#     except Exception as e:
#         print(f"Error in {file_path}: {e}")


# if __name__ == "__main__":
#     file_names = ["robot_3.py","robot_4.py"] # Replace with the name of your Python file
#     print("PLC - Keyence Automation, BEV Porosity Housing X76 & X77\n")
#     for file_name in file_names:
#         current_directory = os.path.dirname(os.path.abspath(__file__))
#         file_path = os.path.join(current_directory, file_name)
#         run_target_python_file(file_path)


from multiprocessing import Process
from robot_3 import Station
from log_handler import PhoenixLogger

def run_station(station_num, logger):
    station = Station(station_num, logger)
    station.start()

if __name__ == "__main__":
    print("PLC - Keyence Automation, BEV Porosity Housing X76 & X77\n")
    station_nums = ['3', '4']
    logger = PhoenixLogger()
    logger.delete_old_logs()
    
    processes = []
    for station_num in station_nums:
        p = Process(target=run_station, args=(station_num, logger))
        processes.append(p)
        p.start()
    
    for p in processes:
        p.join()