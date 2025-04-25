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
from enum import Enum, auto


class Cycler:
    class ResetType(Enum):
        FAULT_RESET = auto()
        PROGRAM_RESET = auto()
    def __init__(self, station_num:str,logger:PhoenixLogger):   
        self.station_num = station_num
        self.logger = logger
        self.connection_timer = datetime.datetime.now() 
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
        self.stop_event.set()
        self.logger.log_print(self.station_num,'Reset detected!')

    def handle_reset(self, reset_type: 'Cycler.ResetType') -> bool:
        if self.stop_event.is_set():
            return True

        bravo_reset_map = {
            self.ResetType.FAULT_RESET: self.bravo_stage.ResetType.FAULT_RESET,
            self.ResetType.PROGRAM_RESET: self.bravo_stage.ResetType.PROGRAM_RESET,
        }

        if reset_type in bravo_reset_map:
            if self.bravo_stage.reset_check(bravo_reset_map[reset_type]):
                self.set_stop_event()
                return True

        return False
    
    def stage_zero(self):
        if self.handle_reset(self.ResetType.FAULT_RESET): return False
        load_program = self.bravo_stage.check_load() 
        while(load_program != True): #Looping until LOAD PROGRAM goes high  # Data from PLC is only valid while LOAD_PROGRAM is low
            if self.handle_reset(self.ResetType.FAULT_RESET): break
            load_program = self.bravo_stage.check_load()
            sleep_time.sleep(.050) # 5ms pause between reads
        if self.stop_event.is_set(): return False
        if (self.bravo_stage.zeta() == False): self.set_stop_event() ; return False # reset threads if invalid part type                     
        self.bravo_stage.iota() 
        return True
    
    def stage_one(self):
        start_program = self.bravo_stage.check_start_program() #check for PLC(START_PROGRAM) to go high
        while (start_program != True): #looping until PLC(START_PROGRAM) goes high
            if self.handle_reset(self.ResetType.PROGRAM_RESET): break
            start_program = self.bravo_stage.check_start_program() #check for PLC(START_PROGRAM) to go high
            sleep_time.sleep(0.050)
        if self.stop_event.is_set(): return False
        self.bravo_stage.kappa()
        self.bravo_stage.omicron()
        self.bravo_stage.sigma()
        return True 
    
    def stage_two(self):
        # elif (self.current_stage == 2):  # Final Stage, reset to Stage 0 once PLC(END_PROGRAM) and PHOENIX(DONE) have been set low
        end_program = self.bravo_stage.omega() #Raise DONE high 
        while (end_program != True): #Looping until PLC(END_PROGRAM) goes high
            if self.handle_reset(self.ResetType.PROGRAM_RESET): break
            end_program = self.bravo_stage.check_end_program() # continuous PLC read
            sleep_time.sleep(0.050)  # 5ms pause between reads
        if self.stop_event.is_set(): return False
        self.bravo_stage.epsilon()
        return True # reset PLC tags to end cycle, inspection cycle complete

    def create_cycle(self):
        bravo_stage = self.bravo_stage
        self.stop_event.clear()
        sleep_time.sleep(.05)
        # with LogixDriver(config_info['plc_ip']) as plc: 
            # setKeyenceRunMode(station_num, sock)
        bravo_stage.alpha() #reset PLC tags to start cycle and reset connection timer, raise ready
        while(True):
            #################### STAGE ZERO ####################   
            if (self.stage_zero()==False): break #waiting for PLC(LOAD_PROGRAM) to go high
            #################### STAGE ONE ####################
            if (self.stage_one()==False): break #waiting for PLC(START_PROGRAM) to go high
            #################### END STAGE ONE ####################
            if (self.stage_two()==False): break #waiting for PLC(END_PROGRAM) to go high
            if abs(datetime.datetime.now() - self.connection_timer).total_seconds() > 86400: self.connection_timer = datetime.datetime.now() ; self.set_stop_event() # if connected for 24 hours perform restart
            if self.stop_event.is_set(): break  #check for reset at beginning of cycle
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
