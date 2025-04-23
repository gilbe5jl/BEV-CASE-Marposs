import sys
import os
from pycomm3 import LogixDriver, CommError
from pycomm3.tag import Tag
from plc_utils import PLCUtils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from log_handler import logger 

class PLCwriter:
    def __init__(self, plc: LogixDriver, machine_num: str):
        self.plc = plc
        self.machine_num = machine_num
        # self.tag_list = PLCUtils.construct_tag_list(machine_num, 'write')
        self.input_tags = PLCUtils.config().get('inputTags', [])
        self.status_tags = PLCUtils.config().get('statusTags', [])
        self.fault_flush_tags = PLCUtils.config().get('faultFlush', {})
        self.reset_tags = PLCUtils.config().get('resetTags', {})
        self.bool_tags = PLCUtils.config().get('boolTags', {})
        self.tag_prefix = PLCUtils.config().get('tagPrefix', {})
        self.fault_tags = PLCUtils.config().get('faultTags', [])

    #Writing back to PLC to mirror data on LOAD
    def write_plc_batch(self,plc: LogixDriver, machine_num: str, results: dict) -> None:
        """
        Write data back to PLC to mirror data on LOAD
        :param plc: PLC driver object
        :param machine_num: machine number
        :param results: dictionary of tags and values
        :return: None
        """
        # config_info = get_config(machine_num)

        try:
            # prefix = config_info['mnTagPrefix'][machine_num] + '.I.'
            # input_tags = tag_lists.input_tag_list(1)
            
            # for i in input_tags:
                # tag = prefix + i
                # if i not in results:
                    # raise KeyError(f"Tag '{i}' not found in the results dictionary.")
                
                # value = results[i][1]
                # plc.write((tag, value))
            for i in self.input_tags:
                tag = PLCUtils.construct_single_tags(machine_num, i, 'write')
                if i not in results:
                    raise KeyError(f"Tag '{i}' not found in the results dictionary.")
                
                value = results[i][1]
                plc.write((tag, value))
                
        except KeyError as key_error:
            logger.out({machine_num: f"⚠️ Error while batch-writing tags: {key_error}"}) #Is there any point in having both the key error exception and the general exception? or can they be comingiined? 
        except Exception as error:
            logger.out({machine_num: f"⚠️ Error while batch-writing tags: {error}"})
        except CommError as error:
            logger.out({machine_num: f"⚠️ Communication error while writing tags: {error}"})
    # END write_plc

    # Writes a single PLC tag
    def write_plc_single(self, tag_name:str, tag_value) -> None:
        """
        Write a single PLC tag to the PLC system
        :param plc: The LogixDriver object that is connected to the PLC system
        :param machine_num: The machine number of the Keyence Controller
        :param tag_name: The name of the PLC tag to be written
        :param tag_val: The value to be written to the PLC tag
        :return: None
        """
        try:
            tag = PLCUtils.construct_single_tag(self.machine_num, tag_name, 'write')
            self.plc.write((tag, tag_value))
        except CommError as error:
            logger.out({self.machine_num: f"⚠️ Communication error while writing tag {tag_name}: {error}"})



    def fault_flush(self)-> None:
        """
        clearing potential fault info when resetting
        :param plc: The LogixDriver object that is connected to the PLC system
        :param machine_num: The machine number of the Keyence Controller
        return none
        """
        # fault_tag_data = {
        #     'Faulted': False,
        #     'PhoenixFltCode': 0,
        #     'KeyenceFltCode': 0,
        #     'FaultStatus': 0,
        #     'Done': False,
        #     'Pass': False,
        #     'Busy': False,
        #     'Fail': False,
        #     'PartProgram': 0,
        #     'Ready': True,
        # }
        for i,j in zip(self.fault_flush_tags.keys(),self.fault_flush_tags.values()):
            self.write_plc_single(self.machine_num,i,j)

    def write_plc_flush(self) -> None:
        """
        Flush input tags and status tags to default values, the PUN requires a special case.
        """
        default = {'PUN{64}': [0] * 64 }
        tag_list = self.input_tags + self.status_tags
        flush_tags = []

        for tag in tag_list:
            full_tag = PLCUtils.construct_single_tag(self.machine_num, tag, 'write')
            flush_tags.append(full_tag)
        try:
            for tag in flush_tags:
                if tag == 'PUN':
                    self.plc.write((tag, default['PUN{64}']))
                else:
                    self.plc.write((tag, 0))
        except Exception as error:
            logger.out({self.machine_num: f"⚠️ Error while flushing tags: {error}"})
        except CommError as error:
            logger.out({self.machine_num: f"⚠️ Communication error while flushing tag {tag}: {error}"})
    #END write_plc_flush

  
    def reset_plc_tags(self, reset_stage: str) -> None:
        '''
        So this fuction will reset the PLC tags to their default values based on the reset_stage
        the reset stage will be passed in as a string and will be used to determine which set of tags are to be reset
        the reset stage can only be one of the following: alpha, beta, gamma
        '''
        stage_tags = self.reset_tags.get(reset_stage)

        if not stage_tags:
            logger.out({self.machine_num: f"⚠️ Invalid reset stage: '{reset_stage}'"})
            return

        if reset_stage in ('alpha', 'beta'):
            self.write_plc_flush()

        for tag, value in stage_tags.items():
            self.write_plc_single(tag, value)


    def set_bool_tags(self) -> None:
        """
        Set boolean tags to True
        """
        for tag, value in self.bool_tags.items():
            self.write_plc_single(tag, value)

    def write_plc_check_pass(self,tag_values:list)->None:
        """
        Construct 4 'Check_Pass' tags for the PLC
        '3':"SN25PHXVPC1.CAM02.I.Check_Pass."(1-4)
        '4':"SN25PHXVPC1.CAM01.I.Check_Pass."(1-4)
        :param tag_values: list of 4 values from Keyence to be written to the PLC
        """
        base = 'CHECK_PASS'
        tag_prefix = self.tag_prefix[self.machine_num]
        full_tags = [f"{tag_prefix}.I.{base}.{i}" for i in range(1,5)]
        for i in full_tags:
            logger.out(f"Writing {i} with value {tag_values[full_tags.index(i)]}")
            self.plc.write((i,tag_values[full_tags.index(i)]))

    def flush_check_pass(self)->None:
        base = 'CHECK_PASS'
        tag_prefix = self.tag_prefix[self.machine_num]
        full_tags = [f"{tag_prefix}.I.{base}.{i}" for i in range(1,5)]
        for tag in full_tags:
            logger.out(f"Flushing {tag} with value 0")
            self.plc.write((tag,0))

    def write_plc_fault(self, fault_type: bool) -> None:
        full_tags = [PLCUtils.construct_single_tag(self.machine_num, tag, 'write') for tag in self.fault_tags[:-1]]
        values = self.fault_tags[-1]["alpha"] if fault_type else self.fault_tags[-1]["beta"]
        for tag, value in zip(full_tags, values):
            print(f"Writing {tag} with value {value}")
            try:
                self.plc.write((tag, value))  
            except CommError as error:
                logger.out({self.machine_num: f"⚠️ Communication error while writing tag {tag}: {error}"})
      

            
    #END write_plc_fault



# plc_ip = PLCUtils.config().get('plc_ip')
# # with LogixDriver(plc_ip) as plc:
# plc = LogixDriver(plc_ip)
# writer = PLCwriter(plc,'4')
# writer.write_plc_fault(False)

