#####################
#     MACHINE       #
#####################
import threading
import datetime, time
import socket
from pycomm3 import LogixDriver
import json
from tag_lists import *
from plc_utils import *
from keyence_utils import *
from export_data import *
from colorama import Fore, Style
from utils import *
import datetime
import time as sleep_time  # Rename the time module import

# Global Variables
# MACHINE_NUMBER = '3' 
# PART_NAME = 'CASE'
spec_map = {}
event = threading.Event()
kill_threads = threading.Event()
part_program = 0

def read_config()->dict:
    with open(os.path.join(sys.path[0], 'config.json'), "r") as config_file:
        config_data = config_file.read()
        config_map = json.loads(config_data)
        return config_map
class create_cycle:
    def __init__(self, machine_num, keyence_ip,plc_ip,part_name):   
        self.machine_num = machine_num
        self.keyence_ip = keyence_ip
        self.plc_ip = plc_ip
        self.part_name = part_name
        self.current_stage = 0
    def cycle(self):
        machine_num = self.machine_num
        keyence_ip = self.keyence_ip
        plc_ip = self.plc_ip
        part_name = self.part_name
        kill_threads.clear()
        event.wait()
        sleep_time.sleep(.05)
        config_info = read_config()
        # print_color(f'({machine_num}) Connecting to PLC at {config_info["plc_ip"]}...\n')
        # print_color(f'({machine_num}) Connecting to Keyence at {keyence_ip}...\n')
        scan_duration = 0 # keeping track of scan time in MS
        with LogixDriver(plc_ip) as plc: #context manager for plc connection, currently resetting connection after ~24 hrs to avoid issues
            try:
                timeout_seconds = 60 
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Keyence socket connections
                sock.settimeout(timeout_seconds)
                sock.connect((keyence_ip, 8500))
            except TimeoutError as error:
                print_red(f"({machine_num}) KEYENCE connection Error:{error} ")
            print_color(f'\n({machine_num}) PLC Connection Successful...\n({machine_num}) KEYENCE Connection Successful...\n')
            # setKeyenceRunMode(machine_num, sock)
            connection_timer = cycle_start(plc, machine_num) #reset PLC tags to start cycle and reset connection timer, raise ready
            while(True):
                if(kill_threads.is_set() ): print_red(f'({machine_num})[PRE-STAGE:0] RESET DETECTED\n') ; break #check reset at beginning of cycle
                #spec_map = check_keyene_spec(sock, spec_map)
                part_type,reset_check,tag_data = get_status_info(machine_num, plc,self.current_stage).values()#get part type and reset check from PLC
                if (reset_check[config_info['tags']['Reset']][1]): self.current_stage = reset_plc_tags(plc, machine_num,'type_one') ; kill_threads.set()
                #################### STAGE ZERO ####################   
                if(self.current_stage == 0):
                    start_stage_zero(machine_num, plc, sock, self.current_stage) #stage 0 function
                    while(tag_data[config_info['tags']['LoadProgram']][1] != True): #Looping until LOAD PROGRAM goes high  # Data from PLC is only valid while LOAD_PROGRAM is low
                        if (kill_threads.is_set()): print_red(f'({machine_num})[STAGE:0] RESET DETECTED\n') ; break #check for reset at beginning of cycle
                        tag_data = get_stage_zero_tag_data(plc,machine_num)
                        reset_check = get_stage_zero_reset_data(plc,machine_num) #get data from PLC
                        if (reset_check[config_info['tags']['Reset']][1] == True): self.current_stage = reset_plc_tags(plc, machine_num,'type_one') ; kill_threads.set()
                        sleep_time.sleep(.050) # 5ms pause between reads
                    if (kill_threads.is_set()): break #check for reset at beginning of cycle
                    swap_check, part_program, part_type = stage_zero_preLoad(machine_num, plc, sock,config_info).values()
                    if swap_check == False: kill_threads.set() # reset threads if invalid part type
                    part_type,keyence_string = stage_zero_data(machine_num, tag_data, sock, config_info,part_program,part_name).values() #building out external Keyence string for scan file naming
                    if keyence_string == 'ERROR': kill_threads.set() # reset threads error generating keyence string                              
                    keyence_string = stage_zero_load(plc, sock, machine_num, tag_data,keyence_string) 
                    self.current_stage += 1 #increment current stage to proceed forward
                #################### STAGE ONE ####################
                elif self.current_stage == 1:
                    print_color(f'({machine_num})[STAGE:1] Waiting for START_PROGRAM...\n')
                    while not tag_data[config_info['tags']['StartProgram']][1]: #looping until PLC(START_PROGRAM) goes high
                        if (kill_threads.is_set()): print_red(f'({machine_num})[STAGE:1] RESET detected while waiting for START_PROGRAM\n') ; break #check for reset at beginning of cycle
                        tag_data = read_plc_dict(plc, machine_num) #continuous PLC read
                        if tag_data[config_info['tags']['Reset']][1]: self.current_stage = reset_plc_tags(plc, machine_num, 'type_two'); kill_threads.set() #check for reset during cycle # type_two reset for stage 1
                        sleep_time.sleep(0.050)
                    exe_time,tag_data,start_trigger_timer = stage_one_trigger(plc, sock, machine_num, tag_data).values()
                    if (exe_time > 3000): write_plc_fault(plc, machine_num, 2)  # measure time it took to trigger keyence, if greater than 3 seconds, set fault
                    scan_duration,exe_time,tag_data= stage_one_post_trigger(plc, sock, machine_num, tag_data, start_trigger_timer).values()
                    if (exe_time > 3000) : write_plc_fault(plc, machine_num, 3)
                    self.current_stage += stage_one_end(plc, sock, machine_num, tag_data, scan_duration, keyence_string, part_type, part_program)
                #################### END STAGE ONE ####################
                elif self.current_stage == 2:  # Final Stage, reset to Stage 0 once PLC(END_PROGRAM) and PHOENIX(DONE) have been set low
                    stage_two_start(plc, machine_num) #Raise DONE high 
                    while not tag_data[config_info['tags']['EndProgram']][1]:
                        if kill_threads.is_set(): print_red(f'({machine_num})[STAGE:2] RESET DETECTED...\n') ; break
                        tag_data = read_plc_dict(plc, machine_num)  # continuous PLC read
                        if tag_data[config_info['tags']['Reset']][1]:print_color(f'({machine_num})[STAGE:2] RESET DETECTED...\n') ; self.current_stage = reset_plc_tags(plc, machine_num, 'type_two') ; kill_threads.set() # type_two reset for stage 2
                        sleep_time.sleep(0.050)  # 5ms pause between reads
                    self.current_stage = reset_to_end_cycle(plc, machine_num)  # reset PLC tags to end cycle  # cycle complete, reset to stage 0
                if abs(datetime.datetime.now() - connection_timer).total_seconds() > 86400: print_red(f'({machine_num})[STAGE:2] RESET DETECTED...\n') ; connection_timer = datetime.datetime.now() ; kill_threads.set() # if connected for 24 hours perform restart
                if (kill_threads.is_set()): print_red(f'({machine_num})[STAGE:2] RESET DETECTED...\n') ; self.current_stage = 0 ; break  #check for reset at beginning of cycle
                sleep_time.sleep(0.005)  # artificial loop timer

  
#END class Cycler
def heartbeat(machine_num,plc_ip): #sets PLC(Heartbeat) high every second to verify we're still running and communicating
    # config_info = read_config()
    def write_heartbeat(plc, machine_num):
        try:
            write_plc_single(plc, machine_num, 'HeartBeat', True)
        except TimeoutError as error:
            print(f'({machine_num}-HB) Timeout in Heartbeat {error}')
            print("Failed to establish PLC connection after multiple retries.")
            kill_threads.set()
    with LogixDriver(plc_ip) as plc:
        print(f'({machine_num}) Heartbeat connected to PLC.\n')
        # while (True):
        counter = 0
        while not (kill_threads.is_set()):
            write_heartbeat(plc, machine_num)
            if (counter % 200) == 0: print(f"({machine_num}) Active PLC Connection",end='\r')
            counter += 1
            sleep_time.sleep(1)
        print(f'({machine_num}-HB) Heartbeat: kill-threads high or reset event set, restarting all threads')
        kill_threads.clear()
   
def run_machine(part_name,machine_num):
    config_info = read_config()  # Read configuration information
    # machine_num = [str(machine_num) for machine_num in config_info['keyence_ip']][0]
    # machine_num = MACHINE_NUMBER
    # part_name = PART_NAME
    keyence_ip = config_info['keyence_ip'][machine_num]
    plc_ip = config_info['plc_ip']
    # Create an instance of the create_cycle class
    cycle_instance = create_cycle(machine_num, keyence_ip,plc_ip,part_name)
    main_thread = threading.Thread(target=cycle_instance.cycle, name=f"ROBOT_({machine_num})")
    heartbeat_thread = threading.Thread(target=heartbeat, args=[machine_num,plc_ip], name=f"Heatbeat_({machine_num})")
    main_thread.start()
    heartbeat_thread.start()
    event.set()  # Signal threads to start
    main_thread.join() # Wait for main thread to exit
    heartbeat_thread.join() # Wait for heartbeat thread to exit


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python __machine__.py <part_name> <machine_num>")
        sys.exit(1)

    part_name = sys.argv[1]  # Get part_name from the command line
    machine_num = sys.argv[2]  # Get machine_num from the command line

    run_machine(part_name, machine_num)

