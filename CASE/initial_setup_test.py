import socket
from pycomm3 import LogixDriver
from tag_lists import *
from plc_utils import *
from keyence_utils import *

def read_config():
    with open(os.path.join(sys.path[0], 'config.json'), "r") as config_file:
        config_data = config_file.read()
        config_vars = json.loads(config_data)
        return config_vars
#END
    
config_info = read_config()
with LogixDriver(config_info['plc_ip']) as plc: #context manager for plc connection, currently resetting connection after ~24 hrs to avoid issues
    x = read_plc_dict(plc,'3')
   # print(x)

    for i in x:
        print(i)