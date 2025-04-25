from keyence_utils import *
from plc_utils import *
from tag_lists import *
from pycomm3 import LogixDriver
from export_data import *
import socket
# import os
# import logging
# from datetime import timedelta,time
# from datetime import datetime 
# import datetime
# # from time import sleep
import time
from log_handler import PhoenixLogger
from enum import Enum, auto


#############################################

class Bravo:
    class ResetType(Enum):
        FAULT_RESET = auto()
        PROGRAM_RESET = auto()
        CYCLE_RESET = auto()
    def __init__(self,machine_num: str, logger:PhoenixLogger):
        self.logger = logger
        self.machine_num = machine_num
        self.keyence = PhoenixKeyence(self.machine_num)
        self.plc = PhoenixPLC(self.machine_num)
        self.config_info = self.read_config()
        self.part_program = None
        self.tag_data = None
        self.part_type = None
        self.start_trigger_timer = None
        self.scan_duration = None
        self.keyence_string = None
        self.connection_timer = None

    def read_config(self)->dict:
        with open(os.path.join(sys.path[0], 'config.json'), "r") as config_file:
            config_data = config_file.read()
            config_vars = json.loads(config_data)
            return config_vars
    def int_array_to_str(self,int_array:list) -> str:
        """
        Convert a list of integers to a string of ASCII characters (PLC int-arrays into ASCII string for OPC)
        :param int_array: A list of integers to be converted to a string
        :return: A string of ASCII characters
        """
        # List comprehension to convert each integer to its corresponding ASCII character. Then join the characters into a single string
        string = ''.join(chr(i) for i in int_array)
        return string
    #END int_array_to_str

    def calc_time(self,start_time, end_time):
        return (end_time - start_time).total_seconds() * 1000
    def alpha(self):
    # self.logger.self.logger.log_print(f'({machine_num})[STAGE:0] Flushing PLC(FAULT) Tags...\n')
        self.plc.fault_flush() # Fault Codes and raise ready
        fault_code = self.keyence.check_fault()
        self.plc.raise_keyence_fault(fault_code)
        self.plc.set_bool_tags()
    
    def check_load(self) -> bool:
        tag_data = self.plc.batch_read()
        return tag_data['LOAD_PROGRAM'][1]
        # tag_data = read_tag(self.plc, self.machine_num, 'LoadProgram')
        # return tag_data['LOAD_PROGRAM'][1]

    def reset_check(self, reset_type: 'Bravo.ResetType') -> bool:
        try:
            reset_check = self.plc.read_tag('Reset')
            if reset_check['RESET'][1] is True:
                self.logger.log_print(self.machine_num, f'PLC(RESET) is HIGH')

                if reset_type == self.ResetType.FAULT_RESET:
                    self.plc.reset_tags(self.plc.ResetType.FAULT_RESET)
                elif reset_type == self.ResetType.PROGRAM_RESET:
                    self.plc.reset_tags(self.plc.ResetType.PROGRAM_RESET)
                elif reset_type == self.ResetType.CYCLE_RESET:
                    self.plc.reset_tags(self.plc.ResetType.CYCLE_RESET)
                return True
            return False
        except TypeError as error:
            print("PLC CommError: ", error)
            return False

    def zeta(self) -> bool:
        counter = 0
        while True:
            self.tag_data = self.plc.batch_read()
            self.logger.log_print(self.machine_num,f"PLC(TAG DATA): {self.tag_data}")
            tag_data_og = self.tag_data.copy()
            self.part_program = self.tag_data['PART_PROGRAM'][1]
            if int(self.part_program) != 0:
                self.plc.write_single('Ready', False)  # Setting PLC(READY) low
                self.plc.write_batch(tag_data_og)             # Mirror data after load
                self.part_type = self.tag_data['PART_TYPE'][1]
                swap_check = self.keyence.swap_check(self.part_type)  # Ensure Keyence has proper program loaded
                self.keyence_string = self.keyence.string_generator(self.part_type, self.part_program)
                if swap_check == 0: return False
                if self.keyence_string is None: return False
                return True
            else:
                if (counter % 200) == 0:
                    self.logger.log_print(self.machine_num,f"Error reading PART_PROGRAM: {self.part_program}")
                counter += 1
                time.sleep(0.001)
        

    def iota(self):
        '''
        Loads Keyence program and sets PLC(READY) high
        '''
        try:
            pun_str = int_array_to_str(self.tag_data['PUN'][1])
            datetime_info_len_check = [str(self.tag_data[config_info['tags']['Month']][1]),
                                    str(self.tag_data[config_info['tags']['Day']][1]),
                                    str(self.tag_data[config_info['tags']['Hour']][1]),
                                    str(self.tag_data[config_info['tags']['Minute']][1]),
                                    str(self.tag_data[config_info['tags']['Second']][1])]

            for x in range(0, len(datetime_info_len_check)): 
                if int(datetime_info_len_check[x]) < 10:
                    datetime_info_len_check[x] = '0' + datetime_info_len_check[x]

            self.keyence_string = str(pun_str[10:22]) + '_' + str(self.tag_data[config_info['tags']['Year']][1]) + '-' + datetime_info_len_check[0] + '-' + datetime_info_len_check[1] + '-' + datetime_info_len_check[2] + '-' + datetime_info_len_check[3] + '-' + datetime_info_len_check[4] + '_' + self.keyence_string
            self.logger.log_print(self.machine_num,f'LOADING KEYENCE: Part Program ({self.part_program}),({self.keyence_string})\n')
            self.keyence.load(self.part_program, self.keyence_string)
            self.plc.write_single('Ready', True)
            self.logger.log_print(self.machine_num,f'[STAGE:1] Waiting for START_PROGRAM')
        except Exception as error:
            self.logger.log_print(self.machine_num,f'Error: {error}')
            return None
###################################


    def check_start_program(self) -> bool:
        tag_data = self.plc.read_tag('StartProgram')
        start_program = tag_data['START_PROGRAM'][1]
        return start_program


    def kappa(self) -> None:
        self.logger.log_print(f'[STAGE:1] START_PROGRAM is active\n')
        self.logger.log_print(f'[STAGE:1] TRIGGERING KEYENCE\n')
        self.tag_data = self.plc.batch_read()
        self.start_trigger_timer = datetime.datetime.now()
        self.keyence.trigger()
        self.plc.write_single('Busy', True)
        end_trigger_timer = datetime.datetime.now()
        exe_time = self.calc_time(self.start_trigger_timer, end_trigger_timer)
        if (exe_time > 3000): self.plc.write_fault(self.plc.FaultType.GENERAL) ; self.logger.log_print(self.machine_num,f'[STAGE:1] KEYENCE TRIGGER TIMEOUT');self.keyence.disconnect() ; return False
       

    def omicron(self) -> None:
        current = self.plc.read_tag('EndScan')
        current.update(self.plc.read_tag('Reset'))
        while((current['END_SCAN'][1] == False) and (current['RESET'][1]== False)):
            current = self.plc.read_tag('EndScan')
            current.update(self.plc.read_tag('Reset'))
            time.sleep(.005)
        self.keyence.exit()
        self.logger.log_print(f'[STAGE:1] TERMINATING KEYENCE PROGRAM')
        end_trigger_timer = datetime.datetime.now()
        self.scan_duration = (end_trigger_timer - self.start_trigger_timer).total_seconds() * 1000
        self.plc.write_single('Busy', False)
        start_result_timer = datetime.datetime.now()
        self.plc.write_single('Ready', False)
        self.keyence.monitor_not_running()
        end_result_timer = datetime.datetime.now()
        exe_time = self.calc_time(start_result_timer, end_result_timer)
        if (exe_time > 3000) : self.plc.write_fault(self.plc.FaultType.COMMS)

      

    def sigma(self) -> None:
        check_pass_results = self.keyence.check_pass()
        self.plc.write_check_pass(check_pass_results)
        keyence_results = self.keyence.get_results()
        self.plc.write_results(keyence_results[0])
        export_all_data(self.machine_num, self.tag_data, keyence_results, self.keyence_string, self.scan_duration, self.part_type, self.part_program,check_pass_results)
        self.keyence.control_cont()
        self.keyence.disconnect()


    
    def omega(self)->bool:
        '''
        Raise DONE high and returns END_PROGRAM bool
        '''
        self.logger.log_print(f'[STAGE:2] DONE is High, Waiting for END_PROGRAM\n')
        self.plc.write_single('Done', True)
        tag = self.plc.read_tag('EndProgram')
        end_program = tag['END_PROGRAM'][1]
        return end_program
    
    def check_end_program(self) -> bool:
        tag = self.plc.read_tag('EndProgram')
        end_program = tag['END_PROGRAM'][1]
        return end_program

    
    def epsilon(self)-> int:
        print(f'[STAGE:2] END_PROGRAM is High\n')
        self.plc.reset_tags(self.plc.ResetType.CYCLE_RESET) #Reset bool tags
        self.plc.flush_check_pass() #Flush Check/Pass data before sending data to PLC again
        self.plc.write_flush() # defaults all .I Phoenix tags at start of cycle
        self.plc.write_single('Ready', True)
        print(f'[STAGE:2] CYCLE COMPLETE\n')
    
    def heartbeat(self):
        """
        Monitors the PLC HeartBeat tag:
        """
        hb_value = self.plc.read_heartbeat()
        print(f'Reading Heartbeat:{hb_value} ',end='\r')        
        time.sleep(1)
        if hb_value == False:    
            self.plc.write_heartbeat()
# machine_num = 3
# message = f'({machine_num}) ...PLC Connection Successful...({machine_num})({machine_num})\n'



# x = extract_machine_num(message)
# print(x)




