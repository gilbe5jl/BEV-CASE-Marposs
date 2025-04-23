import sys
import os
import json
import inspect
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from log_handler import logger  # ✅ Now it won't conflict with `logging`


class PLCUtils:
    """
    A utility class for handling PLC-related functions, including integer array conversion and configuration retrieval.
    """
    @staticmethod
    def int_array_to_str(int_array: list) -> str:
        """
        Convert a list of integers to a string of ASCII characters (PLC int-arrays into ASCII string for OPC).
        
        :param int_array: A list of integers to be converted to a string
        :return: A string of ASCII characters
        """
        return ''.join(chr(i) for i in int_array)

    @staticmethod
    def config() -> dict:
        """
        Retrieve the configuration settings from a JSON file in src/configs/config.json.
        Dynamically resolves the full path based on current file location.
        """
        try:
            # Get base directory by going up until we find 'src'
            current_dir = os.path.abspath(os.path.dirname(__file__))

            while current_dir and not os.path.isdir(os.path.join(current_dir, 'src')):
                parent = os.path.dirname(current_dir)
                if parent == current_dir:
                    raise FileNotFoundError("Could not locate 'src/configs/config.json'")
                current_dir = parent

            config_path = os.path.join(current_dir, 'src', 'configs', 'config.json')
            # print(f"Config path: {config_path}")

            with open(config_path, "r") as config_file:
                return json.load(config_file)

        except FileNotFoundError:
            print("Config file not found")
            logger.out("Config file not found")
            return {}
        
    @staticmethod    
    def construct_single_tag(machine_num: str, tag_name: str, tag_type: str) -> str:
        """
        Constructs a full tag name for reading and writing a single PLC tag.
        
        :param machine_num: The machine number is used to select which tag prefix to use.
        :param tag_name: The specific tag to be read.
        :return: Full PLC tag name as a string.
        """
        config_info = PLCUtils.config()  # ✅ Corrected function call
        # print(f"Constructing tag for machine {machine_num} and tag name {tag_name}")
        # logger.out({machine_num: f"Constructing tag for machine {machine_num} and tag name {tag_name}"})
        if machine_num not in config_info.get("tagPrefix", {}):
            print(f"⚠️ Machine {machine_num} not found in config.")
            logger.out({machine_num: f"⚠️ Machine {machine_num} not found in config."})
            return ""

        tags = config_info.get("tags", {})
        if tag_name not in tags and tag_name not in tags.values():# handle missing tag           
            print(f"⚠️ Tag '{tag_name}' not found in config.")
            logger.out({machine_num: f"⚠️ Tag '{tag_name}' not found in config."})
            return ""
        if "read" == tag_type:
            tag_type = "O"  # Output tags for reading
        elif "write" in tag_type:
            tag_type = "I"
        prefix = f"{config_info['tagPrefix'][machine_num]}.{tag_type}." # 'o' for output is used for reading, 'i' for input is used for writing
        
        return f"{prefix}{config_info['tags'][tag_name]}"
    
    @staticmethod
    def construct_tag_list(machine_num: str,tag_type) -> list:
        """
        Constructs a list of full tag names for batch reading/writing from the PLC.

        :param machine_num: The machine number of the Keyence Controller.
        :return: List of full PLC tag names.
        """
        # Determine if it's a read or write operation 
        config_info = PLCUtils.config()   # ✅ Load configuration
        machine_num = str(machine_num)  # Ensure machine_num is a string
        if machine_num not in config_info.get("tagPrefix", {}):
            logger.out({machine_num: f"⚠️ Machine {machine_num} not found in config."})
            return []
        if "read" == tag_type:
            tag_type = "O"  # Output tags for reading
            tag_list = config_info.get('outputTags', [])
        elif "write" in tag_type:
            tag_type = "I"  # Input tags for writing
            tag_list = config_info.get('inputTags', [])
        prefix = f"{config_info['tagPrefix'][machine_num]}.{tag_type}."
        return [f"{prefix}{tag}" for tag in tag_list]
    




    @staticmethod
    def plc_ip() -> str:
        """
        Retrieve the IP address of the PLC from the configuration file.

        :return: The IP address of the PLC as a string.
        """
        return PLCUtils.config().get('plc_ip')


# print(PLCUtils.get_config())
# x = PLCUtils.get_config()
# print(x['tagPrefix']['3'])
# print(PLCUtils.construct_single_tag('3', 'Faulted'))
# print(PLCUtils.construct_tag_list(4,'read'))
# x = PLCUtils.output_tags()
# print('filtered Tags:')
# for i in x:
#     print(i)