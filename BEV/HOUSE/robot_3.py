#####################
#     ROBOT 3       #
#####################
import threading
from pycomm3 import LogixDriver
from log_handler import PhoenixLogger
import json
from tag_lists import *
from plc_utils import *
from keyence_utils import *
from export_data import *
from utils import *
import datetime
import time as sleep_time  # Rename the time module import



# def read_config()->dict:
#     with open(os.path.join(sys.path[0], 'config.json'), "r") as config_file:
#         config_data = config_file.read()
#         config_map = json.loads(config_data)
#         return config_map
class Cycler:
    def __init__(self, station_num:str,logger:PhoenixLogger):   
        self.station_num = station_num
        self.logger = logger
        self.current_stage = 0
        self.config_info = self.read_config()
        self.bravo_stage = Bravo(self.station_num,self.logger)
        self.stop_event = threading.Event()

    def read_config(self)->dict:
        with open(os.path.join(sys.path[0], 'config.json'), "r") as config_file:
            config_data = config_file.read()
            config_map = json.loads(config_data)
            return config_map
    def set_stop_event(self):
        '''
        Reset the current stage to 0, set the stop event and log the reset
        '''
        self.current_stage = 0
        self.stop_event.set()
        self.logger.log_print(f'[STAGE:{self.current_stage}] RESET DETECTED\n')
    def create_cycle(self):
        bravo_stage = self.bravo_stage
        self.stop_event.clear()
        sleep_time.sleep(.05)
        # with LogixDriver(config_info['plc_ip']) as plc: 
            # setKeyenceRunMode(station_num, sock)
        bravo_stage.alpha() #reset PLC tags to start cycle and reset connection timer, raise ready
        while(True):
            if(self.stop_event.is_set()): break #check reset at beginning of cycle
            if (bravo_stage.reset_check('alpha')): self.set_stop_event() #check for reset at beginning of cycle
            #################### STAGE ZERO ####################   
            if(self.current_stage == 0):
                load_program = bravo_stage.check_load() 
                while(load_program != True): #Looping until LOAD PROGRAM goes high  # Data from PLC is only valid while LOAD_PROGRAM is low
                    if (self.stop_event.is_set()): break #check for reset at beginning of cycle
                    load_program = bravo_stage.check_load()
                    if (bravo_stage.reset_check('alpha')): self.set_stop_event() #check for reset while waiting for load program to go high
                    sleep_time.sleep(.050) # 5ms pause between reads
                if (self.stop_event.is_set()): break #check for reset even is load_program is true
                if (bravo_stage.zeta() == False): self.set_stop_event() # reset threads if invalid part type                     
                bravo_stage.iota() 
                self.current_stage += 1 #increment current stage to proceed forward
            #################### STAGE ONE ####################
            elif (self.current_stage == 1):
                start_program = bravo_stage.check_start_program() #check for PLC(START_PROGRAM) to go high
                while (start_program != True): #looping until PLC(START_PROGRAM) goes high
                    if (self.stop_event.is_set()): break #check for reset at beginning of cycle
                    start_program = bravo_stage.check_start_program() #check for PLC(START_PROGRAM) to go high
                    if (bravo_stage.reset_check('beta')): self.set_stop_event() #check for reset during cycle # type_two reset for stage 1
                    sleep_time.sleep(0.050)
                bravo_stage.kappa()
                bravo_stage.omicron()
                bravo_stage.sigma()
                self.current_stage += 1 #increment current stage to proceed forward
            #################### END STAGE ONE ####################
            elif (self.current_stage == 2):  # Final Stage, reset to Stage 0 once PLC(END_PROGRAM) and PHOENIX(DONE) have been set low
                end_program = bravo_stage.omega() #Raise DONE high 
                while (end_program != True): #Looping until PLC(END_PROGRAM) goes high
                    if self.stop_event.is_set(): break
                    end_program = bravo_stage.check_end_program() # continuous PLC read
                    if (bravo_stage.reset_check('beta')): self.set_stop_event() # type_two reset for stage 2
                    sleep_time.sleep(0.050)  # 5ms pause between reads
                self.current_stage = bravo_stage.epsilon()  # reset PLC tags to end cycle  # cycle complete, reset to stage 0
            # if abs(datetime.datetime.now() - connection_timer).total_seconds() > 86400: connection_timer = datetime.datetime.now() ; self.set_stop_event() # if connected for 24 hours perform restart
            if (self.stop_event.is_set()): break  #check for reset at beginning of cycle
            sleep_time.sleep(0.005)  

  
#END class Cycler
    def create_heartbeat(self):
        """
        Monitors the PLC HeartBeat tag:
        - If HeartBeat is high, wait until it goes low.
        - Once it’s low continuously for 1 second, write it high.
        This implements the cycle where Phoenix detects a low heartbeat
        (indicating communication failure from Grob) and then sets it high.
        """
        # config_info = read_config()
        # with LogixDriver(config_info['plc_ip']) as plc:
        print(f'Heartbeat connected to PLC.\n')
        while not self.stop_event.is_set():
            try:
                self.bravo_stage.heartbeat()  # Check the heartbeat
            except Exception as error:
                print(f'PLC CommError Heartbeat: {error}')
                self.stop_event.set()
                break
            # Small pause before starting the next cycle.
            sleep_time.sleep(0.5)
        print(f'Heartbeat: Reset detected\n')
        self.stop_event.clear()
   

class Station:
    def __init__(self, station_num:str, logger:PhoenixLogger):
        self.station_num = station_num
        self.logger = logger
        # self.cycle = Cycler(station_num, logger)
        # self.stop_event = threading.Event()
    def create_threads(self):
        # Create an instance of the create_cycle class
        cycle = Cycler(self.station_num, self.logger)
        main_thread = threading.Thread(target=cycle.create_cycle(), name=f"Station_({self.station_num})")
        heartbeat_thread = threading.Thread(target=cycle.create_heartbeat(), name=f"Heatbeat_({self.station_num})")
        main_thread.start()
        heartbeat_thread.start()
        main_thread.join() # Wait for main thread to exit
        heartbeat_thread.join() # Wait for heartbeat thread to exit

    def start(self):
        while True:
            self.create_threads()



# if __name__ == '__main__':
#     logger = PhoenixLogger(['3','4'])
#     while True:
#         Station('3',logger).start()

