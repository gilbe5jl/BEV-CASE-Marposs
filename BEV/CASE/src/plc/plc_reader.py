from pycomm3 import LogixDriver, CommError
from pycomm3.tag import Tag
from plc_utils import PLCUtils
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from log_handler import logger  


class PLCreader:
    def __init__(self, plc: LogixDriver, machine_num: str):
        self.plc = plc
        self.machine_num = machine_num
        self.tag_list = PLCUtils.construct_tag_list(machine_num, 'read')

    def _read(self, tag: str):
        try:
            result = self.plc.read(tag)
            key = result.tag.split(".")[-1]
            return {key: (result.tag, result.value, result.type, result.error)}
        except AttributeError:
            logger.out({self.machine_num: f"⚠️ Failed to read PLC tag {tag}"})
            return {}
        except Exception as e:
            logger.out({self.machine_num: f"⚠️ PLC read error for tag {tag}: {e}"})
            return {}
        except CommError as e:
            logger.out({self.machine_num: f"⚠️ Communication error while reading tag {tag}: {e}"})
            return {}

    def single_read(self, tag_name: str) -> dict:
        full_tag_name = PLCUtils.construct_single_tag(self.machine_num, tag_name,'read')
        return self._read(full_tag_name)

    def batch_read(self) -> dict:
        try:
            results = self.plc.read(*self.tag_list)
            return {
                result.tag.split(".")[-1]: (result.tag, result.value, result.type, result.error)
                for result in results
            }
        except Exception as e:
            logger.out({self.machine_num: f"⚠️ Failed batch read from PLC: {e}"})
            return {}
        except CommError as e:
            logger.out({self.machine_num: f"⚠️ Communication error during batch read: {e}"})
            return {}




# Now, you can use any static method from PLCUtils
# single_tag = PLCUtils.construct_single_tag('3', 'Faulted')
# tag_list = PLCUtils.construct_tag_list('4')

# print(f"Single Tag: {single_tag}")
# print(f"Tag List: {tag_list}")
# plc_ip = PLCUtils.plc_ip()
# print(plc_ip)
# try:
#     with LogixDriver(plc_ip) as plc:
#         print(read_plc_tags(plc, '3', 'Faulted'))   # Read a single tag
# except CommError as e:
#     print(f"Failed to connect to PLC: {e}")
    
# print(PLCUtils.construct_tag_list('3','read'))