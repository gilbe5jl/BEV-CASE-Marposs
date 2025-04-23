'''
               T~~
               |
              /"\\
      T~~     |'| T~~
  T~~ |    T~ WWWW|
  |  /"\   |  |  |/\T~~
 /"\ WWW  /"\ |' |WW|
WWWWW/\| /   \|'/\|/"\\
|   /__\/]WWW[\/__\WWWW
|"  WWWW'|I_I|'WWWW'  |
|   |' |/  -  \|' |'  |
|'  |  |LI=H=LI|' |   |
|   |' | |[_]| |  |'  |
|   |  |_|###|_|  |   |
'---'--'-/___\-'--'---'
V:10.1.30
'''
from keyence_utils import *
from plc_utils import *
from tag_lists import *
from pycomm3 import LogixDriver
from export_data import *
import socket
import os
import logging
from datetime import timedelta,time
from datetime import datetime 
import datetime
# from time import sleep
import time
def configure_logger(logger_name,log_file_name,machine_num):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(log_file_name)
    now = datetime.datetime.now().strftime("%I:%M:%S")
    formatter = logging.Formatter(f"{now}-%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger
def log_gen():
    today = datetime.datetime.now().strftime("%a-%b-%d-%Y")
    log_file_3 = f"ROBOT(3)-{today}.log"
    log_file_4 = f"ROBOT(4)-{today}.log"
    # log_file_5 = f"ROBOT(5)_{today}.log"
    logger_r3 = configure_logger("Logger_r3",log_file_3,3)
    logger_r4 = configure_logger("Logger_r4",log_file_4,4)
    return {'log_4': logger_r3, 'log_5':logger_r4}
# logger_r5 = configure_logger("Logger_r5",log_file_5,5)

def delete_old_logs():
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%a-%b-%d-%Y")
    log_file_3 = f"ROBOT(3)_{yesterday}.log"
    log_file_4 = f"ROBOT(4)_{yesterday}.log"
    # log_file_5 = f"ROBOT(5)_{yesterday}.log"
    try:
        os.remove(log_file_3)
        os.remove(log_file_4)
        # os.remove(log_file_5)
    except FileNotFoundError as error:
        pass
# delete_old_logs()
# os.remove(log_file_3)
# os.remove(log_file_4)
# os.remove(log_file_5)
def extract_machine_num(message):
    # Find the opening parenthesis and closing parenthesis in the message
    start_index = message.find('(')
    end_index = message.find(')')
    # Check if both parentheses are found
    if start_index != -1 and end_index != -1:
        # Extract the substring between the parentheses
        machine_num_str = message[start_index + 1:end_index]
        
        try:
            # Attempt to convert the extracted substring to an integer
            machine_num = int(machine_num_str)
            return machine_num
        except ValueError:
            # Handle the case where the substring cannot be converted to an integer
            return None
    return None  # Return None if the parentheses are not found
def print_color(message:str)->None:
    machine_num = str(extract_machine_num(message))
    if machine_num == '3':
        print_green(message)
    elif machine_num == '4':
        print_blue(message)
    elif machine_num == '5':
        print_yellow(message)


logger_r3,logger_r4 = log_gen().values()
def print_green(message:str)->None:
    logger_r3.info(message)
    print(Fore.GREEN + f"{message}\n" + Style.RESET_ALL)
def print_blue(message:str)->None:
    logger_r4.info(message)
    print(f"{message}")
def print_yellow(message:str)->None:
    # logger_r5.info(message)
    print(f"{message}")
def print_red(message:str)->None:
    mn = str(extract_machine_num(message))
    if mn == '3':
        pass
        logger_r3.critical(message)
    if mn == '4':
        pass
        logger_r4.critical(message)
    if mn == '5':
        pass
        # logger_r5.critical(message)
    print(f"{message}")
def exe_time(start_time, end_time):
    return (end_time - start_time).total_seconds() * 1000
def read_config()->dict:
    with open(os.path.join(sys.path[0], 'config.json'), "r") as config_file:
        config_data = config_file.read()
        config_vars = json.loads(config_data)
        return config_vars

def get_status_info(machine_num:str,plc:LogixDriver,current_stage)->list:
    # print_color(f'({machine_num})[STAGE:{current_stage}] Reading PLC(DATA)...\n')
    config_info = read_config()
    tag_data = read_plc_dict(plc, machine_num) #initial PLC tag read
    part_type = tag_data[config_info['tags']['PartType']][1]
    reset_check = read_plc_single(plc, machine_num, 'Reset')   # PLC read and check to reset system off PLC(Reset) tag
    return {"part_type":part_type,"reset_check":reset_check,"tag_data":tag_data}

def start_stage_zero(machine_num:str,plc:LogixDriver,sock:socket.socket,current_stage:int)->None:
    # print_color(f'({machine_num})[STAGE:{current_stage}] Waiting for LOAD_PROGRAM & BUSY...')
    check_keyence_error(machine_num, sock, plc) #check keyence for error codes
    # print_color(f'({machine_num})[STAGE:0] Setting PLC(BOOL) Tags...\n') #flag reset/beginning of timing diagram
    set_bool_tags(plc, machine_num)
def stage_zero_preLoad(machine_num:str,plc:LogixDriver,sock:socket.socket,config_info)->int:
    # print_color(f'({machine_num})[STAGE:0] START_PROGRAM is HIGH...\n')
    counter = 0
    while True:
        tag_data = read_plc_dict(plc, machine_num)
        print_color(f"PLC(TAG DATA): {tag_data}")
        # for i in range(0, len(tag_data)):
            # print_color(f"({machine_num}): {tag_data[i]}") # <<<<<<<<< this might not print correctly
        tag_data_og = tag_data.copy()
        # print_red(f"PLC (TAG DATA COPY): {tag_data_og}")
        part_program = tag_data[config_info['tags']['PartProgram']][1] 
        if int(part_program) != 0:
            print(f"({machine_num}) PLC(PART_PROGRAM, {part_program})...\n")
            write_plc_single(plc, machine_num, 'Ready', False) #setting PLC(READY) low
            write_plc(plc,machine_num,tag_data_og) # MIRRORING DATA #MIRROR DATA AFTER LOAD ################
            part_type = tag_data[config_info['tags']['PartType']][1]
            swap_check = keyence_swap_check(sock, machine_num, part_type) #ensure keyence has proper program loaded   
            return {"swap_check":swap_check,"part_program": part_program,"part_type": part_type}
        else:
            if (counter % 200) == 0: print(f"({machine_num})[STAGE:0] Reading PART_PROGRAM as: ({part_program}), ERROR: Incorrrect PART_PROGRAM. Attempting to retrive PART_PROGRAM...")
            counter += 1
            time.sleep(0.001)
def stage_zero_load(plc: LogixDriver, sock: socket.socket, machine_num: str, tag_data: dict,keyence_string) -> None:
    try:
        pun_str = int_array_to_str(tag_data['PUN'][1])
        datetime_info_len_check = [str(tag_data[config_info['tags']['Month']][1]),
                                  str(tag_data[config_info['tags']['Day']][1]),
                                  str(tag_data[config_info['tags']['Hour']][1]),
                                  str(tag_data[config_info['tags']['Minute']][1]),
                                  str(tag_data[config_info['tags']['Second']][1])]

        for x in range(0, len(datetime_info_len_check)): 
            if int(datetime_info_len_check[x]) < 10:
                datetime_info_len_check[x] = '0' + datetime_info_len_check[x]

        keyence_string = str(pun_str[10:22]) + '_' + str(tag_data[config_info['tags']['Year']][1]) + '-' + datetime_info_len_check[0] + '-' + datetime_info_len_check[1] + '-' + datetime_info_len_check[2] + '-' + datetime_info_len_check[3] + '-' + datetime_info_len_check[4] + '_' + keyence_string
        # part_prog =  str(tag_data[config_info['tags']['PartProgram']][1]) # Here there is a bug, sometimes the part program being read is not the same as the one in the keyence_string, sometimes it is sending the previous part program from the previous cycle
        part_prog = read_plc_single(plc, machine_num, 'PartProgram') #single plc tag read
        
        print(f"\tPart Program: {part_prog}\n")

        print(f'({machine_num})[STAGE:0] LOADING KEYENCE: Part Program ({part_prog}), Keyence String: ({keyence_string})...\n')
        load_keyence(sock, machine_num, str(tag_data[config_info['tags']['PartProgram']][1]), keyence_string, plc)
        # print_color(f'({machine_num})[STAGE:0] LOADING KEYENCE COMPLETE\n') 
        return keyence_string
    except Exception as error:
        print(f'({machine_num}) Error in utils - stage_zero_load: {error}')
        raise error

def stage_one_trigger(plc: LogixDriver, sock: socket.socket, machine_num: str, tag_data: dict) -> None:
    print_color(f'({machine_num})[STAGE:1] START_PROGRAM is active...\n')
    def exe_time(start_time, end_time):
        return (end_time - start_time).total_seconds() * 1000
    try:
        tag_data = read_plc_dict(plc, machine_num)
        start_trigger_timer = datetime.datetime.now()
        print_color(f'({machine_num})[STAGE:1] TRIGGERING KEYENCE...\n')
        trigger_keyence(sock, machine_num, plc)
        end_trigger_timer = datetime.datetime.now()
        ex_time = exe_time(start_trigger_timer, end_trigger_timer)
        return {"exe_time": ex_time, "tag_data": tag_data, "start_trigger_timer": start_trigger_timer}
    except Exception as error:
        print_red(f'({machine_num}) Error in utils.py - stage_one_trigger: {error}')
        raise error

def stage_one_post_trigger(plc: LogixDriver, sock: socket.socket, machine_num: str, tag_data: dict, start_trigger_timer) -> None:
    def exe_time(start_time, end_time):
        return (end_time - start_time).total_seconds() * 1000
    try:
        monitor_end_scan(plc, machine_num, sock)
        print_color(f'({machine_num})[STAGE:1] TERMINATING KEYENCE PROGRAM...\n')
        end_trigger_timer = datetime.datetime.now()
        scan_duration = (end_trigger_timer - start_trigger_timer).total_seconds() * 1000
        write_plc_single(plc, machine_num, 'Busy', False)
        start_result_timer = datetime.datetime.now()
        monitor_keyence_not_running(sock, machine_num,plc)
        end_result_timer = datetime.datetime.now()
        ex_time = exe_time(start_result_timer, end_result_timer)
        return {"scan_duration": scan_duration, "exe_time": ex_time, "tag_data": tag_data}
    except Exception as error:
        print_red(f'({machine_num}) Error in utils.py//stage_one_post_trigger: {error}')
        raise error

def stage_one_end(plc: LogixDriver, sock: socket.socket, machine_num: str, tag_data: dict, scan_duration: int, keyence_string, part_type, part_program) -> None:
    try:
        check_pass_results = keyence_check_pass(machine_num, sock, plc)
        keyence_results = keyence_results_to_PLC(sock, plc, machine_num)
        export_all_data(machine_num, tag_data, keyence_results, keyence_string, scan_duration, part_type, part_program,check_pass_results)
        keyence_control_cont(sock, machine_num)
        # print_color(f'({machine_num})[STAGE:1] Proceeding to [STAGE:2]\n')
        return 1
    except Exception as error:
        print_red(f'({machine_num}) Error in utils.py - end_stage_one: {error}')
        raise error
    
def get_stage_zero_tag_data(plc:LogixDriver,machine_num:str):
    try:
        tag_data = read_plc_dict(plc, machine_num) #continuous full PLC read
        # reset_check = read_plc_single(plc, machine_num, 'Reset') #single plc tag read
        return tag_data
    except Exception as error:
        print_red(f'({machine_num}) Error in utils.py - get_stage_zero_data: {error}')
        raise error
        
    
def get_stage_zero_reset_data(plc:LogixDriver,machine_num:str):
    try:
        # tag_data = read_plc_dict(plc, machine_num) #continuous full PLC read
        reset_check = read_plc_single(plc, machine_num, 'Reset') #single plc tag read
        return reset_check
    except Exception as error:
        print_red(f'({machine_num}) Error in utils.py//get_stage_zero_data: {error}')
        raise error
# move exe_time function to this file and call it from here so that these functions can return less variables 
# machine_num = 3
# message = f'({machine_num}) ...PLC Connection Successful...({machine_num})({machine_num})\n'


def stage_two_start(plc,machine_num):
    print_color(f'({machine_num})[STAGE:2] DONE is HIGH Waiting for END_PROGRAM...\n')
    write_plc_single(plc, machine_num, 'Done', True)
# x = extract_machine_num(message)
# print(x)


def cycle_start(plc,machine_num):
    # print_color(f'({machine_num})[STAGE:0] Flushing PLC(FAULT) Tags...\n')
    write_plc_fault_flush(plc,machine_num) # Fault Codes and raise ready
    connection_timer = datetime.datetime.now() #reset connection timer
    return connection_timer

def stage_zero_data(machine_num, tag_data, sock, config_info,part_program):
    part_type = tag_data[config_info['tags']['PartType']][1]
    print_color(f'({machine_num})[STAGE:0] Pre-Load: PLC(PART_TYPE, {part_type})\n')
    keyence_string = keyence_string_generator(machine_num, part_type, tag_data, sock, config_info,part_program) 
    return {"part_type": part_type, "keyence_string": keyence_string}