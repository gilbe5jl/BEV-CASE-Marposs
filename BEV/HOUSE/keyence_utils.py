'''
 ___________
||         ||            _______
|| PHOENIX ||           | _____ |
|| IMAGING ||           ||_____||
||_________||           |  ___  |
|  + + + +  |           | |___| |
    _|_|_   \           |       |
   (_____)   \          |       |
              \    ___  |       |
       ______  \__/   \_|       |
      |   _  |      _/  |       |
      |  ( ) |     /    |_______|
      |___|__|    /         V:10.1.29
           \_____/
'''
import socket
import time
from config_loader import Config
def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        self = args[0]  # assuming the first argument is 'self'
        try:
            return func(*args, **kwargs)
        except (TimeoutError, socket.timeout, ConnectionRefusedError, ConnectionResetError, 
                ConnectionError, ConnectionAbortedError, OSError, socket.gaierror) as error:
            print(f"KEYENCE CommError : {error}")
            return False
    return wrapper
    
class PhoenixKeyence:
    def __init__(self, station_num:str):
        self.station_num = station_num
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Keyence socket connections
        self.config_info = Config().get()
        self.keyence_ip = self.config_info['keyence_ip'][station_num]
        self.socket_timeout_seconds = 60 # seconds
        self.part_type = None
        self.connect()


        
    def format_data(self,data):
        data_str = str(data).split('.')
        split_str = data_str[0].split('+')
        numeric_part = int(split_str[1])
        return numeric_part
    
    @handle_exceptions
    def connect(self):
        self.sock.settimeout(self.socket_timeout_seconds)
        self.sock.connect((self.keyence_ip, 8500))
        print(f'KEYENCE: Connection open for ({self.keyence_ip})\n')
    
    @handle_exceptions
    def disconnect(self):
        self.sock.close()
        print(f'KEYENCE: Connection closed for ({self.keyence_ip})\n')

    def string_generator(self,part_type:int,part_program):
        try:
            '''
            Fixed issue revolving around part_program, we were outputting wrong keyence string do to sometimes reading part_program as zero.
            Part_program was orginally being read from a dictionary and now it is being passed directly into the function 
            '''    
            scan_set = 'scan_names' + self.config_info['part_type_switch'][str(part_type)]
            keyence_string = self.config_info[scan_set][str(part_program)] + f'_{self.config_info["part_type_switch"][str(part_type)]}'
            return keyence_string
        except Exception:
            return None
        
    @handle_exceptions
    def swap_check(self, part_type: int):
    # used to ensure the correct Keyence program is loaded for the part being processed 
        self.sock.sendall('PR\r\n'.encode())
        keyence_value = int(self.sock.recv(32).decode().split(',')[2].split('\\')[0][3])
        if keyence_value != part_type:
            self.sock.sendall(f'PW,1,{part_type}\r\n'.encode())
            self.sock.recv(32)
            time.sleep(2)
    
    @handle_exceptions
    def trigger(self):
        def read_busy():
            self.sock.sendall(b'MR,%Trg1Ready\r\n')
            return self.sock.recv(32)
        def wait_for_busy(busy_value):
            print(f'[STAGE:1] KEYENCE WAITING FOR BUSY SIGNAL...\n')
            while read_busy() != busy_value:
                time.sleep(0.02)
        self.sock.sendall(b'T1\r\n')
        self.sock.recv(32)
        wait_for_busy(b'MR,+0000000000.000000\r')
    # END 'TriggerKeyence'

    @handle_exceptions
    def load(self, partProgram:int, keyence_str:str):
    #sends specific Keyence Program (branch) info to pre-load/prepare Keyence for Trigger(T1), also loads naming variables for result files
        sock = self.sock
        timeout_seconds = 45
        sock.settimeout(timeout_seconds)
        branch_info = f'MW,#PhoenixControlFaceBranch,{str(partProgram)}\r\n' # keyence message
        stw_cmd = 'STW,0,"' + keyence_str + '\r\n' # keyence message sets image names for part
        result_cmd = f'OW,42,"{keyence_str}-Result\r\n' # keyence message specifies output unit
        sock.sendall(branch_info.encode())  # sending branch info
        sock.recv(32) # clear buffer
        sock.sendall(stw_cmd.encode())
        sock.recv(32)
        sock.sendall(result_cmd.encode())
        sock.recv(32)
        message = 'OW,43,"' + keyence_str + '-10ZPos\r\n' # keyence message output unit
        sock.sendall(message.encode())
        sock.recv(32)
        message = 'OW,44,"' + keyence_str + '-10Loc\r\n' # keyence message output unit
        sock.sendall(message.encode())
        sock.recv(32)
    # END 

    @handle_exceptions
    def monitor_not_running(self):
    # function to monitor the Keyence tag 'KeyenceNotRunning', when True (+00001.00000) we know Keyence has completed result processing and FTP file write
        print(f'[STAGE:1] KEYENCE processing results.\n')
        msg = 'MR,#KeyenceNotRunning\r\n'
        sock = self.sock
        def check_keyence_running():
            sock.sendall(msg.encode())
            return sock.recv(32)
        while check_keyence_running() != b'MR,+0000000001.000000\r':
            time.sleep(0.005)
        print(f'[STAGE:1] KEYENCE processing complete!\n')
    # END monitor_KeyenceNotRunning

    @handle_exceptions
    def exit(self):
        # sends 'TE,0' then 'TE,1' to the Keyence, resetting to original state (ready for new 'T1')
        #interrupts active scans on 'EndScan' from PLC
        sock = self.sock
        commands = ['TE,0\r\n', 'TE,1\r\n']
        for command in commands:
            sock.sendall(command.encode())
            sock.recv(32)
        def read_busy():
            sock.sendall(b'MR,%Busy\r\n')
            return sock.recv(32)
        while read_busy() != b'MR,+0000000000.000000\r':
            time.sleep(0.2)
            read_busy()
    # END 'ExtKeyence'


    '''
    5/25/2024
    TODO: Ensure that this function is working as intended
    NOTE:
    There needs to be 4 check pass tags for each machine
    I am unsure how many check pass tags have been implemented in the PLC
    Example:
    SN25PHXVPC1.CAM02.I.Check_Pass.1, 0
    SN25PHXVPC1.CAM02.I.Check_Pass.2, 0
    SN25PHXVPC1.CAM02.I.Check_Pass.3, 1
    SN25PHXVPC1.CAM02.I.Check_Pass.4, 0
    Essentially we write a boolean to each check pass tag 
    for each of the four Hole inspections, per machine
    '''
    @handle_exceptions
    def check_pass(self):
        keyence_commands = [f'MR,#Hole{i}\r\n' for i in range(1, 5)] #Creates a list of Keyence commands to Holes 1-4, Hole 5 is not used, to get check pass data
        tag_values = []
        sock = self.sock
        for cmd in keyence_commands:
            sock.sendall(cmd.encode())
            data = sock.recv(32)
            tag_values.append(self.format_data(data))
        return tag_values
    # END keyence_check_pass

    @handle_exceptions
    def get_results(self):
    # function to read Keyence results and write to PLC tags
        #read results from Keyence then pass to proper tags on PLC
        sock=self.sock
        result_messages = ['MR,#ReportDefectCount\r\n', 'MR,#ReportLargestDefectSize\r\n', 'MR,#ReportLargestDefectZoneNumber\r\n', 'MR,#ReportPass\r\n', 'MR,#ReportFail\r\n',
                            'MR,#ReportMaskFail\r\n', 'MR,#ReportSizeFail\r\n', 'MR,#ReportSpacingFail\r\n', 'MR,#ReportDensityFail\r\n',"MR,#Zpoint1_Pass\r\n","MR,#Zpoint2_Pass\r\n"]
        results = []
        for msg in result_messages:
            sock.sendall(msg.encode())
            data = sock.recv(32)
            keyence_value_raw = str(data).split('.')
            keyence_value_raw = keyence_value_raw[0].split('+')
            keyence_value = int(keyence_value_raw[1])
            results.append(keyence_value)
        z_point_cmds = ['MR,#CurrentPoint1_Z\r\n','MR,#CurrentPoint2_Z\r\n']
        for msg in z_point_cmds:
            sock.sendall(msg.encode())
            data = sock.recv(32)
            keyence_value_raw = str(data).split('.') # ["b'MR,-0000","8878\\r"]
            get_keyence_whole_num = keyence_value_raw[0].split(',') #["b'MR","-000"]
            get_keyence_fractional_num = keyence_value_raw[1].split('\\') #["8878","\\r"]
            keyence_whole_num = get_keyence_whole_num[1]
            keyence_fractional_num = get_keyence_fractional_num[0]
            keyence_z_point_data = f"{keyence_whole_num}.{keyence_fractional_num}"
            if '-' in keyence_z_point_data:
                keyence_z_point_data = keyence_z_point_data.split('-')
                keyence_z_point_data = round(float(keyence_z_point_data[1]),4)
                keyence_z_point_data = f"-{keyence_z_point_data}"
            if '+' in keyence_z_point_data:
                keyence_z_point_data = keyence_z_point_data.split('+')
                keyence_z_point_data = round(float(keyence_z_point_data[1]),4)
            results.append(keyence_z_point_data)
        # print(f'({station_num}) Defect_Number: {results[0]}')
        # print(f'({station_num}) Defect_Size: {results[1]}')
        # print(f'({station_num}) Defect_Zone: {results[2]}')
        # print(f'({station_num}) Pass: {results[3]}')
        # print(f'({station_num}) Fail: {results[4]}')
        # print(f'({station_num}) Mask_Fail: {results[5]}')
        # print(f'({station_num}) Size_Fail: {results[6]}')
        # print(f'({station_num}) Spacing_Fail: {results[7]}')
        # print(f'({station_num}) Density_Fail: {results[8]}')
        # print(f'({station_num}) Z_Point_1: {results[9]}')
        # print(f'({station_num}) Z_Point_2: {results[10]}')
        tag_list = ['DEFECT_NUMBER','DEFECT_SIZE','DEFECT_ZONE','PASS','FAIL','MASK_FAIL','SIZE_FAIL','SPACING_FAIL','DENSITY_FAIL','Z1','Z2','ZPOINT_1','ZPOINT_2']
        result_hash = dict(zip(tag_list,results))
        for i,j in result_hash.items():
            print(f'KEYENCE_RESULTS: ({i}) : {j}\n')
        return [results,result_hash]
    #END keyenceResults_to_PLC

    @handle_exceptions
    def set_keyence_run_mode(self):
        print(f'Setting KEYENCE to RUN MODE.\n')
        msg = 'R0'
        self.sock.sendall(msg.encode())
        _ = self.sock.recv(32) #Clearing buffer

    @handle_exceptions
    def control_cont(self):
        print(f'Sending KEYENCE command "PhoenixControlContinue,1"...\n')
        keyence_command = 'MW,#PhoenixControlContinue,1\r\n' ; sock = self.sock
        sock.sendall(keyence_command.encode())
        _ = sock.recv(32) #Clearing buffer

    @handle_exceptions
    def check_fault(self):
        try:
            error_msg = 'MR,%Error0Code\r\n'
            self.sock.sendall(error_msg.encode())
            data = self.sock.recv(32)
            n = str(data).split('.')
            m = n[0].split('+')
            o = int(m[1])
            data = int(o)
            if data in (16, 17, 69, 71, 80, 85, 224):
                print(f'({self.machine_num}) KeyenceFltCode:',data)
                return data
            return None
        except (ConnectionResetError, ConnectionRefusedError, ConnectionError,ConnectionAbortedError,TimeoutError) as error:
            write_plc_single(LogixDriver(plc_ip),machine_num,'PhoenixFltCode',1)
            print(f"{machine_num} keyence connection error: {error}")
            #logger.log_print(machine_num, f"keyence connection error: {error}")
            return 0
        except Exception as error:
            print(f"{machine_num} Unexpected keyence error in:{error}")














    

# # path = f"C:\MiddleManPython\MMHousingDeployment\{i}-Aug-{j}-2023_py.log"


