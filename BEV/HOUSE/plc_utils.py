from pycomm3 import LogixDriver, CommError
from pycomm3.tag import Tag
import tag_lists
import sys
import os
import json

def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        self = args[0]  # assuming the first argument is 'self'
        try:
            return func(*args, **kwargs)
        except (CommError,Exception) as error:
            print(f"PLC Comm Error({func.__name__}): {error}")
            return False
    return wrapper



class PhoenixPLC:
    def __init__(self,station_num:str):
        self.station_num = station_num
        self.config_info = self.get_config()
        self.plc_ip = self.config_info['plc_ip']
        self.plc = LogixDriver(self.plc_ip)
        self.error_msg = "PLC Communication error:"
        self.prefix = self.config_info['tagPrefix'][self.station_num]
        self.read_prefix = f"{self.prefix}.O."
        self.write_prefix = f"{self.prefix}.I."
        self.check_pass_tag = f"{self.write_prefix}CHECK_PASS."
        self.heartbeat_tag = f'{self.write_prefix}HEARTBEAT'

    def get_config(machine_num:str) -> dict:
        with open(os.path.join(sys.path[0], f'config.json'), "r") as config_file:
            config_data = config_file.read()
            config_info = json.loads(config_data)
        return config_info

    @handle_exceptions
    def open_connection(self)-> None:
        """
        Opens a connection to the PLC using the pycomm3 library.
        :return: None
        """
        self.plc._forward_open()
        self.plc.open()
    
    @handle_exceptions
    def close_connection(self)-> None:
        """
        Closes the connection to the PLC using the pycomm3 library.
        :return: None
        """
        self.plc.close()
    
    @handle_exceptions
    def batch_read(self)->dict:
        """
        Reads all tags from the PLC using the pycomm3 library.
        :return: A dictionary containing the tag names and their corresponding values.
        """
        tag_suffix = tag_lists.output_tags()
        tags = [f"{self.read_prefix}{tag}" for tag in tag_suffix] # list comprehension of tags to read
        results_list = self.plc.read(*tags) # splat-read: tag, value, type, error
        read_map = {}
        for result in results_list:
            key = result.tag.split(".")[-1]
            read_map[key] = (result.tag, result.value, result.type, result.error)
        return read_map
    #END 

    @handle_exceptions
    def read_tag(self,tag_name:str) -> dict:
        """
        Reads a single tag from the PLC using the pycomm3 library.
        :param tag_name: The name of the tag to read.
        :return: A dictionary containing the tag name and its corresponding value.
        """
        tag = f"{self.read_prefix}{self.config_info['tags'][tag_name]}"
        result_tag = self.plc.read(tag) # The Tag object contains the tag name, value, data type, and error status
        read_dict = {}    
        key = result_tag.tag.split(".")[-1]
        read_dict[key] = result_tag
        return read_dict # Return the dictionary of tag values
    #END 

    @handle_exceptions
    def write_plc(self,results: dict) -> None:
        """
        Writes the results to the PLC using the pycomm3 library.
        :param results: A dictionary containing the tag names and their corresponding values.
        :return: None
        """
        input_tags = tag_lists.input_tag_list(1)
        for i in input_tags:
            tag = f"{self.write_prefix}{i}"
            if i not in results:
                raise KeyError(f"Tag '{i}' not found in the results dictionary.")
            value = results[i][1]
            self.plc.write((tag, value))
    # END write_plc

    @handle_exceptions
    def write_plc_single(self,tag_name:str, tag_val) -> None:
        """
        Writes a single tag to the PLC using the pycomm3 library.
        :param tag_name: The name of the tag to write.
        :param tag_val: The value to write to the tag.
        :return: None
        """
        tag = f"{self.write_prefix}{self.config_info['tags'][tag_name]}"
        self.plc.write((tag, tag_val))

    @handle_exceptions
    def set_bool_tags(self) -> None:
        tags = {
            'Done': False,
            'Pass': False,
            'Busy': False,
            'Fail': False,
            'Ready': True
        }
        for tag_name, tag_val in tags.items():
            self.write_plc_single(tag_name, tag_val)
    #END set_bool_tags

    @handle_exceptions
    def fault_flush(self)-> None:
        """
        Flushes PLC fault tags to default values.
        :return: None
        """
        fault_tag_data = {
            'Faulted': False,
            'PhoenixFltCode': 0,
            'KeyenceFltCode': 0,
            'FaultStatus': 0,
            'Done': False,
            'Pass': False,
            'Busy': False,
            'Fail': False,
            'PartProgram': 0,
            'Ready': True,
        }
        for tag_name, tag_val in fault_tag_data.items():
            self.write_plc_single(tag_name, tag_val)
    #END fault_flush

    @handle_exceptions
    def write_plc_flush(self) -> None:
        """
        Flushes PLC data mirroring tags (to 0)
        """
        default = {'PUN{64}': [0] * 64 }
        input_tags = tag_lists.input_tag_list(2)
        for tag in input_tags:
            if tag == 'PUN':
                self.plc.write((self.write_prefix + tag, default['PUN{64}']))
            else:
                self.plc.write((self.write_prefix + tag, 0))
    #END write_plc_flush

    @handle_exceptions
    def reset_plc_tags(self,reset_type:str) -> None:
        """
        Must pass in string alpha, beta, gamma
        """
        alpha = {'Faulted': False,'PhoenixFltCode': 0,'KeyenceFltCode': 0,'FaultStatus': 0}
        beta = {'Reset': False}
        beta.update(alpha)
        gamma = {'Done': False,'Pass': False,'Busy': False,'Fail': False,'Aborted': False}
        reset_groups = {'alpha':alpha,'beta':beta,'gamma':gamma}
        if reset_type in ('alpha', 'beta'):
            self.write_plc_flush()
            for tag,tag_val in reset_groups[reset_type].items():
                self.write_plc_single(tag, tag_val)
        elif reset_type == 'gamma':
            for tag,tag_val in gamma.items():
                self.write_plc_single(tag, tag_val)
        
    @handle_exceptions
    def write_plc_fault(self, fault_type: int) -> None:
        fault_tags = ['PhoenixFltCode', 'FaultStatus', 'Faulted']
        fault_vals = {
            2: [2, 2, True],
            3: [3, 3, True]
        }
        # Optionally handle an invalid fault_type:
        if fault_type not in fault_vals:
            raise ValueError(f"Invalid fault_type: {fault_type}")
        for tag, tag_val in zip(fault_tags, fault_vals[fault_type]):
            self.write_plc_single(tag, tag_val)
        
    @handle_exceptions
    def flush_check_pass(self)->None:
        tags = []
        for i in range(1,5):
            full_tag =  f"{self.check_pass_tag}{i}"
            tags.append(full_tag)
        for i in tags:
            self.plc.write((full_tag,0))
    
    @handle_exceptions
    def write_check_pass(self,tag_values:list)->None:
        tags = []
        for i in range(1,5):
            full_tag_name =  f"{self.check_pass_tag}{i}"
            tags.append(full_tag_name)
        for tag,val in zip(tags,tag_values):
            self.plc.write((tag,val))

    @handle_exceptions
    def write_results(self,results:list):
        result_tag_list = tag_lists.result_tags()
        for i in range(len(result_tag_list)):
            self.write_plc_single(result_tag_list[i], results[i])
        self.write_plc_single('Done', True)
        print(f'KEYENCE Results written to PLC\n')

    @handle_exceptions
    def write_plc_heartbeat(self) -> bool:
        """
        """
        self.plc.write((self.heartbeat_tag, True))
        return self.read_heartbeat()
    
    @handle_exceptions
    def read_heartbeat(self) -> bool:
        """
        """
        result_tag = self.plc.read(self.heartbeat_tag) # The Tag object contains the tag name, value, data type, and error status
        read_dict = {} 
        key = result_tag.tag.split(".")[-1]
        read_dict[key] = result_tag
        return read_dict['HEARTBEAT'][1]# Return the dictionary of tag values
    #END read_plc_singles

    @handle_exceptions
    def raise_keyence_fault(self,fault_code:int)->None:
        """
        """
        if fault_code != None:
            self.write_plc_single('Faulted', True)
            self.write_plc_single('KeyenceFltCode', fault_code)
