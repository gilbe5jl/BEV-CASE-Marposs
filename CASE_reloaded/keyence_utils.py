'''
 ___________
||         ||            _______
|| PHOENIX ||           | _____ |
|| IMAGING ||           ||_____||
||_________||           |  ___  |
|  + + + +  |           | |___| |
    _|_|_   \           |       |
   (_____)   \          |       |
              \    ___  |       |
       ______  \__/   \_|       |
      |   _  |      _/  |       |
      |  ( ) |     /    |_______|
      |___|__|    /         V:10.1.29
           \_____/
'''
import socket
import time
import datetime

from pycomm3 import LogixDriver

from plc_utils import write_plc_single, write_plc_check_pass, flush_check_pass
from plc_utils import print_red,print_color, read_plc_single, int_array_to_str,reset_plc_tags,write_plc_flush
import tag_lists
from pycomm3.tag import Tag
import tag_lists
import sys
import os
import json
import csv

with open(os.path.join(sys.path[0], 'config.json'), "r") as config_file:
    config_data = config_file.read()
    config_info = json.loads(config_data)
    
    

def read_config():
    """
    Reads the configuration file and returns the parsed JSON data.
    """
    try:
        with open(os.path.join(sys.path[0], 'config.json'), "r") as config_file:
            config_data = config_file.read()
            return json.loads(config_data)
    except FileNotFoundError as file_error:
        print_color(f"Error reading configuration file: File not found.\n")
        return None



def keyence_string_generator(machine_num: str, part_type: int, results_dict: dict, sock: socket.socket, config_info: dict,part_program,part_name:str):
    try:
        '''
        Fixed issue revolving around part_program, we were outputting wrong keyence string due to sometimes reading part_program as zero.
        Part_program was orginally being read from a dictionary and now it is being passed directly into the function 
        '''
        scan_set = 'scan_names_' + config_info['part_type_switch'][str(part_type)] # we are passing in a one or a two and getting x76 or x77 which we use this string to get the correct scan set
        for i,j in results_dict.items():
            if 'PUN' not in i:
                print_color(f"{machine_num}{i}:{j[1]}\n")
        keyence_string = config_info[part_name][scan_set][str(part_program)] + f'_{config_info["part_type_switch"][str(part_type)]}'

    except Exception as error:
        print_color(f'({machine_num}) Error building Keyence String: Check Part Program({part_program}) & Part Type({part_type})...{error}')
        return 'ERROR'
    return keyence_string

# used to ensure the correct Keyence program is loaded for the part being processed 
def keyence_swap_check(sock: socket.socket, machine_num: str, part_type: int):
    if not isinstance(part_type, int) or part_type < 0:
        print_color(f"({machine_num}) ERROR: Invalid part_type '{part_type}'. Must be a positive integer.")
        return False
    try:
        sock.settimeout(5)  # Set a timeout for socket operations
        sock.sendall('PR\r\n'.encode())
        keyence_value = int(sock.recv(32).decode().split(',')[2].split('\\')[0][3])
        if keyence_value != part_type:
            print_color(f'({machine_num})[STAGE:0] Initiating Swap Check...\n')
            sock.sendall(f'PW,1,{part_type}\r\n'.encode())
            sock.recv(32)
            time.sleep(2)
            return True
        return False
    # except KeyError as error:
    #     print(f'({machine_num}) ERROR: PART_TYPE {part_type} is invalid. Keyence Swap Check failed:\n{error}')
    #     return 0
    # except TimeoutError as error:
    #     print_color(f"Keyence Swap Check failed:\n{error}")
    except (ValueError, IndexError) as parse_error:
        print_color(f"({machine_num}) ERROR: Parsing response failed. Details: {parse_error}")
        return False
    except (TimeoutError, socket.timeout) as timeout_error:
        print_color(f"({machine_num}) ERROR: Keyence Swap Check timed out. Details: {timeout_error}")
        return False
    except socket.error as sock_error:
        print_color(f"({machine_num}) ERROR: Socket error during Keyence Swap Check. Details: {sock_error}")
        return False
    finally:
        sock.settimeout(None)  # Reset the timeout setting after operation
    


# def keyence_swap_check(sock: socket.socket, machine_num: str, part_type: int) -> bool:
#     if not isinstance(part_type, int) or part_type < 0:
#         logging.error(f"({machine_num}) ERROR: Invalid part_type '{part_type}'. Must be a positive integer.")
#         return False

#     try:
#         sock.settimeout(5)  # Set a timeout for socket operations
#         sock.sendall(b'PR\r\n')
#         response = sock.recv(32).decode()
#         keyence_value = int(response.split(',')[2].split('\\')[0][3])

#         if keyence_value != part_type:
#             logging.info(f'({machine_num})[STAGE:0] Initiating Swap Check...')
#             sock.sendall(f'PW,1,{part_type}\r\n'.encode())
#             sock.recv(32)  # Receive acknowledgment
#             time.sleep(2)  # Small delay for stabilization
#             return True
#         return False

#     except (ValueError, IndexError) as parse_error:
#         logging.error(f"({machine_num}) ERROR: Parsing response failed. Details: {parse_error}")
#         return False
#     except (TimeoutError, socket.timeout) as timeout_error:
#         logging.error(f"({machine_num}) ERROR: Keyence Swap Check timed out. Details: {timeout_error}")
#         return False
#     except socket.error as sock_error:
#         logging.error(f"({machine_num}) ERROR: Socket error during Keyence Swap Check. Details: {sock_error}")
#         return False
#     finally:
#         sock.settimeout(None)  # Reset the timeout setting after operation






def trigger_keyence(sock: socket.socket, machine_num: str,plc:LogixDriver):
    def read_busy():
        sock.sendall(b'MR,%Trg1Ready\r\n')
        return sock.recv(32)
    def wait_for_busy(busy_value):
        print_color(f'({machine_num})[STAGE:1] KEYENCE WAITING FOR BUSY SIGNAL...\n')
        while read_busy() != busy_value:
            time.sleep(0.02)
    def measure_execution_time(start_time,message):
        execution_time = (datetime.datetime.now() - start_time).total_seconds() * 1000
        # if execution_time > 0:
        print_color(f'({machine_num}) Keyence Trigger Delayed, {message}: {execution_time} ms\n')
    #wait_for_busy(b'MR,+0000000000.000000\r')
    
    # measure_execution_time(datetime.datetime.now(),"ignore")
    #trigger_start_time = datetime.datetime.now()
    try:
        timeout_seconds = 10
        sock.settimeout(timeout_seconds)
        # measure_execution_time(datetime.datetime.now(),"Pre Trigger")
        sock.sendall(b'T1\r\n')
        sock.recv(32)
        # measure_execution_time(datetime.datetime.now(),"Post Trigger")
        wait_for_busy(b'MR,+0000000000.000000\r')
        write_plc_single(plc, machine_num, 'Busy', True)
        
        # print(f'({machine_num}) Keyence Triggered!\n')
    except Exception as error:
        print_color(f'({machine_num}) Error during Keyence Trigger: {error}\n')
    except (TimeoutError, socket.timeout) as timeout_error:
        print_color(f"({machine_num}) ERROR: Keyence connection Timeout during Trigger\n{timeout_error}")
    except socket.error as sock_error:
        print_color(f"({machine_num}) ERROR: Socket error during Keyence Trigger\n{sock_error}")
    finally:
        sock.settimeout(None)
    #measure_execution_time(trigger_start_time)
    #wait_for_busy(b'MR,+0000000001.000000\r')
    #measure_execution_time(trigger_start_time)
    #write_plc_single(plc, machine_num, 'Busy', False)
# END 'TriggerKeyence'


#sends specific Keyence Program (branch) info to pre-load/prepare Keyence for Trigger(T1), also loads naming variables for result files
def load_keyence(sock:socket.socket, machine_num:str, partProgram:int, keyence_str:str,plc:LogixDriver):
    try:
        timeout_seconds = 45
        sock.settimeout(timeout_seconds)
        branch_info = f'MW,#PhoenixControlFaceBranch,{partProgram}\r\n' # keyence message
        stw_cmd = 'STW,0,"' + keyence_str + '\r\n' # keyence message sets image names for part
        result_cmd = f'OW,42,"{keyence_str}-Result\r\n' # keyence message specifies output unit
        out_unit_pos = 'OW,43,"' + keyence_str + '-10ZPos\r\n' # keyence message output unit
        out_unit_loc = 'OW,44,"' + keyence_str + '-10Loc\r\n' # keyence message output unit
        # sock.recv to clear buffer
        # sending branch info
        sock.sendall(branch_info.encode()) 
        sock.recv(32)
        sock.sendall(stw_cmd.encode())
        sock.recv(32)
        sock.sendall(result_cmd.encode())
        sock.recv(32)
        sock.sendall(out_unit_pos.encode())
        sock.recv(32)
        sock.sendall(out_unit_loc.encode())
        sock.recv(32)
        write_plc_single(plc, machine_num, 'Ready', True)
    except (TimeoutError, socket.timeout) as timeout_error:
        print_color(f"({machine_num})ERROR: Connection Timeout during load sequence...\n")
    except socket.error as sock_error:
        print_color(f"({machine_num})ERROR: Socket error during load sequence...\n")
    finally:
        sock.settimeout(None)




def check_keyene_spec(sock:socket.socket, oldDict:dict):
    with open(os.path.join(sys.path[0], 'spec.json'), "r") as spec_file:
        spec_data = spec_file.read()
        spec_map = json.loads(spec_data)
            
        if spec_map == oldDict:
            return spec_map
        else:
            for i in spec_map.keys:
                keyence_branch = str(i)
                new_spec = str(spec_map[i])
                message = f'MW,#Branch1Spec,{new_spec}\r\n'
                sock.sendall(message.encode())
                _ = sock.recv(32)
        spec_file.close()
    return spec_map

# sends 'TE,0' then 'TE,1' to the Keyence, resetting to original state (ready for new 'T1')
#interrupts active scans on 'EndScan' from PLC
def exit_keyence(sock: socket.socket,machine_num:str):
    # print_color(f'({machine_num})[STAGE:1] EXITING KEYENCE PROGRAM...\n')
    commands = ['TE,0\r\n', 'TE,1\r\n']
    for command in commands:
        sock.sendall(command.encode())
        sock.recv(32)
    def read_busy():
        sock.sendall(b'MR,%Busy\r\n')
        return sock.recv(32)
    while read_busy() != b'MR,+0000000000.000000\r':
        time.sleep(0.2)
        read_busy()
# END 'ExtKeyence'



# reading PLC(EndScan) until it goes high to interrupt current Keyence scan
# This version uses a dictionary comprehension to initialize the current dictionary with the desired tags. 
# It then continuously checks the PLC tags' values until both conditions are met (either EndScan or Reset is True).
def monitor_end_scan(plc: LogixDriver, machine_num: str, sock: socket.socket):
    # print_color(f'({machine_num})[STAGE:1] WAITING for PLC(END_SCAN)')
    # current = {tag: None for tag in ['EndScan', 'Reset']}
    # while not all(tag_value[1] for tag_value in current.values()):
    #     current.update({tag: read_plc_single(plc, machine_num, tag) for tag in current})
    #     time.sleep(0.005)
    current = read_plc_single(plc,machine_num,'EndScan')
    current.update(read_plc_single(plc,machine_num,'Reset'))
    while((current[config_info['tags']['EndScan']][1] == False) and (current[config_info['tags']['Reset']][1]== False)):
        current = read_plc_single(plc,machine_num,'EndScan')
        current.update(read_plc_single(plc,machine_num,'Reset'))
        time.sleep(.005)
    # print_color(f'({machine_num})[STAGE:1] PLC(END_SCAN) is high, Interrupting KEYENCE Scan...\n')
    exit_keyence(sock,machine_num)  # Interrupt Keyence scan
#END monitor_endScan

# function to monitor the Keyence tag 'KeyenceNotRunning', when True (+00001.00000) we know Keyence has completed result processing and FTP file write
def monitor_keyence_not_running(sock: socket.socket, machine_num: str,plc:LogixDriver):
    print_color(f'({machine_num})[STAGE:1] KEYENCE processing results and exporting data...\n')
    write_plc_single(plc, machine_num, 'Ready', False)
    msg = 'MR,#KeyenceNotRunning\r\n'
    def check_keyence_running():
        sock.sendall(msg.encode())
        return sock.recv(32)
    while check_keyence_running() != b'MR,+0000000001.000000\r':
        print_color(f'({machine_num}) Keyence Processing...') 
        time.sleep(0.005)
    print_color(f'({machine_num})[STAGE:1] KEYENCE processing complete!...\n')
# END monitor_KeyenceNotRunning




# function to read Keyence results and write to PLC tags
def keyence_results_to_PLC(sock:socket.socket, plc:LogixDriver, machine_num:str):
    #read results from Keyence then pass to proper tags on PLC
    
    config_info = read_config()
    result_messages = config_info['memory_read'] #returns a list of strings
    results = []

    # sending result messages to Keyence, then cleaning results to 'human-readable' list
    for msg in result_messages:
        sock.sendall(msg.encode())
        data = sock.recv(32)
        keyence_value_raw = str(data).split('.')
        keyence_value_raw = keyence_value_raw[0].split('+')
        keyence_value = int(keyence_value_raw[1])
        results.append(keyence_value)
        # print("KEYENCE Results RAW --",data)
        # print("KEYENCE Results COOKED --",keyence_value)
    z_point_cmds = ['MR,#CurrentPoint1_Z\r\n','MR,#CurrentPoint2_Z\r\n']
    for msg in z_point_cmds:
        sock.sendall(msg.encode())
        data = sock.recv(32)
        keyence_value_raw = str(data).split('.') # ["b'MR,-0000","8878\\r"]
        get_keyence_whole_num = keyence_value_raw[0].split(',') #["b'MR","-000"]
        get_keyence_fractional_num = keyence_value_raw[1].split('\\') #["8878","\\r"]
        keyence_whole_num = get_keyence_whole_num[1]
        keyence_fractional_num = get_keyence_fractional_num[0]
        keyence_z_point_data = f"{keyence_whole_num}.{keyence_fractional_num}"
        if '-' in keyence_z_point_data:
            keyence_z_point_data = keyence_z_point_data.split('-')
            keyence_z_point_data = round(float(keyence_z_point_data[1]),4)
            keyence_z_point_data = f"-{keyence_z_point_data}"
        if '+' in keyence_z_point_data:
            keyence_z_point_data = keyence_z_point_data.split('+')
            keyence_z_point_data = round(float(keyence_z_point_data[1]),4)
        results.append(keyence_z_point_data)
    print_color(f'({machine_num}) Defect_Number: {results[0]}')
    print_color(f'({machine_num}) Defect_Size: {results[1]}')
    print_color(f'({machine_num}) Defect_Zone: {results[2]}')
    print_color(f'({machine_num}) Pass: {results[3]}')
    print_color(f'({machine_num}) Fail: {results[4]}')
    print_color(f'({machine_num}) Mask_Fail: {results[5]}')
    print_color(f'({machine_num}) Size_Fail: {results[6]}')
    print_color(f'({machine_num}) Spacing_Fail: {results[7]}')
    print_color(f'({machine_num}) Density_Fail: {results[8]}')
    print_color(f'({machine_num}) Z_Point_1: {results[9]}')
    print_color(f'({machine_num}) Z_Point_2: {results[10]}')
    print_color(f'({machine_num}) Thread_Fail: {results[11]}') # No plc tag for this
    print_color(f'({machine_num}) Surface_Fail: {results[12]}') # No plc tag for this
    print_color(f'({machine_num}) HoleChamfer_Fail: {results[13]}') # No plc tag for this
    # writing normalized Keyence results to proper PLC tags
    tag_list = ['DEFECT_NUMBER','DEFECT_SIZE','DEFECT_ZONE','PASS','FAIL','MASK_FAIL','SIZE_FAIL','SPACING_FAIL','DENSITY_FAIL','Z1','Z2','ZPOINT_1','ZPOINT_2']
    result_hash = dict(zip(tag_list,results))
    result_tag_list = tag_lists.result_tag_list()
    for i in range(len(result_tag_list)):
        write_plc_single(plc, machine_num, result_tag_list[i], results[i])
    write_plc_single(plc, machine_num, 'Done', True)
    print_color(f'({machine_num}) KEYENCE Results written to PLC...\n')
    return [results,result_hash]
#END keyenceResults_to_PLC



def check_keyence_error(machine_num:str, sock:socket.socket, plc:LogixDriver):
    # error_msg = 'MR,%Error0Code\r\n'
    # sock.sendall(error_msg.encode())
    # n = str(data).split('.')
    # m = n[0].split('+')
    # o = int(m[1])
    # data = int(o)
    # if(data < 16):
    #     # print(f'({machine_num}) Error Code:\n',data)
    #     write_plc_single(plc, machine_num, 'Faulted', True)
    #     write_plc_single(plc, machine_num, 'PhoenixFltCode', data)
    # elif(data >= 16 and data < 48):
    #     # print(f'({machine_num}) Error Code:\n',data)
    #     write_plc_single(plc, machine_num, 'Faulted', True)
    #     write_plc_single(plc, machine_num, 'KeyenceFltCode', data)
    # else:
    #     # print(f'({machine_num}) Error Code (non-crit):{data}\n')
    #     pass
    pass







def set_keyence_run_mode(machine_num:str, sock:socket.socket):
    print_color(f'({machine_num}) SETTING KEYENCE TO RUN MODE...\n')
    msg = 'R0'
    sock.sendall(msg.encode())
    _ = sock.recv(32) #Clearing buffer

'''
5/25/2024
TODO: Ensure that this function is working as intended
NOTE:
There needs to be 4 check pass tags for each machine
I am unsure how many check pass tags have been implemented in the PLC
Example:
SN25PHXVPC1.CAM02.I.Check_Pass.1, 0
SN25PHXVPC1.CAM02.I.Check_Pass.2, 0
SN25PHXVPC1.CAM02.I.Check_Pass.3, 1
SN25PHXVPC1.CAM02.I.Check_Pass.4, 0
Essentially we write a boolean to each check pass tag 
for each of the four Hole inspections, per machine
'''
def keyence_check_pass(machine_num: str, sock: socket.socket, plc: LogixDriver):
    keyence_commands = [f'MR,#Hole{i}\r\n' for i in range(1, 5)] #Creates a list of Keyence commands to Holes 1-4, Hole 5 is not used, to get check pass data
    tag_values = []
    for cmd in keyence_commands:
        sock.sendall(cmd.encode())
        data = sock.recv(32)
        tag_values.append(format_keyence_data(data))
       
    config_info = read_config()
    check_pass_tags = config_info['check_pass_tags'] #returns a dictionary
    tags = []
    for i in range(1,5):
        tag_prefix = check_pass_tags[machine_num]
        full_tag_name =  f"{tag_prefix}{i}"
        tags.append(full_tag_name)
    for i,j in zip(tags,tag_values):
        write_plc_check_pass(plc,machine_num,i,j)
    return dict(zip(tags, tag_values))#************************************************
# END keyence_check_pass

def format_keyence_data(data):
    data_str = str(data).split('.')
    split_str = data_str[0].split('+')
    numeric_part = int(split_str[1])
    return numeric_part


'''
Not sure why this function is in this module, it should be in plc_utils.py
However, I will leave it here for now and move it later
'''
def check_pass_flush(plc,machine_num):
    try:
        config_info = read_config()
        check_pass_tags = config_info['check_pass_tags'] #returns a dictionary
        tags = []
        for i in range(1,5):
            tag_prefix = check_pass_tags[machine_num]
            full_tag_name =  f"{tag_prefix}{i}"
            tags.append(full_tag_name)
        for i in tags:
            flush_check_pass(plc,i)
    except Exception as error:
        print_color(f"Error flushing Check Pass tags: {error}")



def keyence_control_cont(sock:socket.socket, machine_num:str):
    keyence_command = 'MW,#PhoenixControlContinue,1\r\n'
    sock.sendall(keyence_command.encode())
    _ = sock.recv(32) #Clearing buffer
    print_color(f'({machine_num}) Sending KEYENCE command "PhoenixControlContinue,1"...\n')

def reset_to_end_cycle(plc:LogixDriver, machine_num:str):
    print_color(f'({machine_num})[STAGE:2] END_PROGRAM is high...\n')
    reset_plc_tags(plc, machine_num,'type_three')
    check_pass_flush(plc,machine_num) #Flush Check/Pass data before sending data to PLC again
    write_plc_flush(plc,machine_num) # defaults all .I Phoenix tags at start of cycle
    write_plc_single(plc, machine_num, 'Ready', True)
    print_color(f'({machine_num})[STAGE:2] CYCLE COMPLETE...\n')
    return 0
    
# import os 

# # path = f"C:\MiddleManPython\MMHousingDeployment\{i}-Aug-{j}-2023_py.log"


# config_info = read_config()
# check_pass_tags = config_info['memory_read'] 
# print(check_pass_tags)