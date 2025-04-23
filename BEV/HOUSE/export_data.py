# from plc_utils import int_array_to_str
import datetime
import os
import sys
import json
from tag_lists import *

with open(os.path.join(sys.path[0], 'config.json'), "r") as config_file:
    config_data = config_file.read()
    config_info = json.loads(config_data)

# input_tags = input_tag_list(2)
# results_tags = result_tags()

def int_array_to_str(int_array:list) -> str:
        """
        Convert a list of integers to a string of ASCII characters (PLC int-arrays into ASCII string for OPC)
        :param int_array: A list of integers to be converted to a string
        :return: A string of ASCII characters
        """
        # List comprehension to convert each integer to its corresponding ASCII character. Then join the characters into a single string
        string = ''.join(chr(i) for i in int_array)
        return string
    #END int_array_to_str
def export_all_data(machine_num:str, results:dict, keyence_results:list, keyence_str:str, duration:int, part_type, part_program,check_pass_results:dict):
    """
    Export all data to CSV and text files.

    Args:
        machine_num (str): The machine number.
        results (dict): A dictionary containing results data.
        keyence_results (list): A list of Keyence results.
        face_name (str): The face name for the file.
        duration (int): The duration of the operation.
        part_type: The type of the part.
        part_program: The program associated with the part.
        keyence_str (str): A Keyence string.

    Returns:
        None
    """
    create_csv(machine_num, results, keyence_results, keyence_str, duration, part_type, part_program)
    write_part_results(machine_num, results, keyence_results, keyence_str,check_pass_results)

# def create_csv(machine_num:str, results:dict, keyence_results:list, face_name:str, duration:int,part_type,part_program):
    '''
    Results data is written to a CSV file 
    The CSV file is used by the HMI 
    '''
    # file_name = config_info['FTP_directory'] + config_info['keyence_ip'][machine_num] + config_info['FTP_extension']
    # file_name = file_name + '\\' + face_name + '.txt'
    # if not os.path.exists(os.path.dirname(file_name)):
    #    os.makedirs(os.path.dirname(file_name))
    # file_name = file_name.replace('\x00', '')
    # print(f'Creating CSV files:\t->{file_name}')
    # with open(file_name, 'w+', newline='') as f:
    #    for i in input_tags:
    #        try:
    #             if i == 'PUN':
    #                 # print(f"\n\t\tPUN:{results['PUN'][1]}\n\n")
    #                 result = int_array_to_str(results[i][1])            
    #                 f.write(f"{i}_2, {result}\n")
    #                 print(i, str(results[i][1]))
    #             elif i == 'PASS':
    #                 # result = str(0)
    #                 # f.write(f"{i}_2, {result}\n")
    #                 print(f"PASS->{i}", str(results[i][1]))
    #             else:
    #                 if i == 'PART_PROGRAM':
    #                     f.write(f"PART_PROGRAM_2, {part_program}\n")
    #                 elif i == 'PART_TYPE':
    #                     f.write(f"PART_TYPE_2, {part_type}\n")
    #                 else:
    #                     result = str(results[i][1])
    #                     f.write(f"{i}_2, {result}\n")
    #                     print(i, str(results[i][1]))
    #        except KeyError as error:
    #            print(error)
    #    for i in range(len(results_tags)):
    #        try:
    #            f.write(f"{results_tags[i]}_2, {str(keyence_results[i])}  \n")
    #        except KeyError as error:
    #            print("A Key ERROR occured while creating CSV file",error)
    #    f.write('DURATION_2, ' + str(duration) + '\n')
#END create_csv
def create_csv(machine_num:str, results:dict, keyence_results:dict, face_name:str, duration:int,part_type,part_program):
    '''
    OUTPUT DATA to be read by SQL for HMI
    Edited by Chinmay on 8/1/2023
    Copied from Silao Program, 
    Chinmay changes removed replaced with all capital key names to fix key error 
    Ateel request:
    Part type is either 1,2,7
    Part type 2 needs to be replaced with a 1 then written to csv for HMI 
    '''    
    file_name = config_info['FTP_directory'] + config_info['keyence_ip'][machine_num] + config_info['FTP_extension']
    file_name = file_name + '\\' + face_name + '.txt'
    if not os.path.exists(os.path.dirname(file_name)):
       os.makedirs(os.path.dirname(file_name))
    file_name = file_name.replace('\x00', '')
    # print('Creating CSV called:',file_name)
   #  part_type = str(results['PART_PROGRAM'][1])
    # print(f"-------------------------PART_TYPE:({part_type})---------------------------------")
    if (str(part_type) == '2' or part_type == 2):
        # print(f'\t RECIEVED: Part Type ({part_type})\n--Changing Part Type (2) to Part Type (1)')
        part_type = '2'

    with open(file_name, 'w+', newline='') as f:
       f.write(f'PART_TYPE_2, {part_type} \n')
    #    f.write('PART_TYPE_2, ' + str(results['PART_TYPE'][1]) + '\n')
       f.write('PART_PROGRAM_2, ' + str(part_program) + '\n')
      #  f.write('PART_PROGRAM_2, ' + str(results['PART_PROGRAM'][1]) + '\n')
       f.write('SCAN_NUMBER_2, ' + str(results['SCAN_NUMBER'][1]) + '\n')
       f.write('PUN_2, ' + int_array_to_str(results['PUN'][1]) + '\n')
       f.write('GM_PART_NUMBER_2, ' + str(results['GM_PART_NUMBER{8}'][1]) + '\n')
       f.write('MODULE_2, ' + str(results['MODULE'][1]) + '\n')
       f.write('PLANT_CODE_2, ' + str(results['PLANT_CODE'][1]) + '\n')
       f.write('TIMESTAMP_MONTH_2, ' + str(results['TIMESTAMP_MONTH'][1]) + '\n')
       f.write('TIMESTAMP_DAY_2, ' + str(results['TIMESTAMP_DAY'][1]) + '\n')
       f.write('TIMESTAMP_YEAR_2, ' + str(results['TIMESTAMP_YEAR'][1]) + '\n')
       f.write('TIMESTAMP_HOUR_2, ' + str(results['TIMESTAMP_HOUR'][1]) + '\n')
       f.write('TIMESTAMP_MINUTE_2, ' + str(results['TIMESTAMP_MINUTE'][1]) + '\n')
       f.write('TIMESTAMP_SECOND_2, ' + str(results['TIMESTAMP_SECOND'][1]) + '\n')
    #    f.write('DEFECT_NUMBER_2, ' + str(results['DEFECT_NUMBER'][1]) + '\n')
    #    f.write('DEFECT_SIZE_2, ' + str(results['DEFECT_SIZE'][1]) + '\n')
    #    f.write('DEFECT_ZONE_2, ' + str(results['DEFECT_ZONE'][1]) + '\n')
       
    #    f.write('PASS_2, ' + str(results['PASS'][1]) + '\n')
    #    f.write('FAIL_2, ' + str(results['FAIL'][1]) + '\n')
      #  ls = ['DEFECT_NUMBER','DEFECT_SIZE','DEFECT_ZONE','PASS','FAIL','MASK_FAIL','SIZE_FAIL','SPACING_FAIL','DENSITY_FAIL']
    #    print('====KEYENCE RESULTS LIST====')
    #    for i,j in zip(ls, keyence_results):
    #        print(f"{i} \t{j}\n") 

       for i,j in zip(keyence_results[1].keys(),keyence_results[1].values()):
            if i != 'ZPOINT_1' or i != 'ZPOINT_2':
                f.write(f'{i}_2,  {str(j)}\n')
            else:
                f.write(f'{i},  {str(j)}\n')

    #    for i,j in zip(keyence_results[1].keys(),keyence_results[1].values()):
        #  print(f"({machine_num})KEYENCE_RESULTS: ({i}_2) : {j}\n")
      

       duration = round(duration,4) 
       f.write('DURATION_2, ' + str(duration) + '\n')


       return
#END create_csv
# Gerry's request to log all results per part in one continuous file
def write_part_results(machine_num: str, results_dict: dict, keyence_results: list, keyence_string: str, check_pass_results: dict):
    def process_tag_name(check_pass_results: dict):
        new_dict = {}
        for i, j in check_pass_results.items():
            index = i.find("Check_Pass")
            if index != -1:
                new_key = i[index:]
                new_dict[new_key] = j
        return new_dict

    empty_str = ''
    pun_str = str(results_dict['PUN'][1])
    pun_str = pun_str.strip()  # remove spaces
    pun_str = pun_str.rstrip('\\x00')  # remove nulls
    pun_str = 'PUN: ' + pun_str
    t = datetime.datetime.now()
    s = t.strftime('%Y-%m-%d %H:%M:%S.%f')  # stripping off decimal (ms)
    dt_string = t.strftime("%Y-%m-%d")  # datetime stamped file naming, year#-month#-day#
    # designating end of part by part #, to write out actual line in .csv
    pass_fail_output = empty_str.join(['[Pass: ', str(keyence_results[0][3]), ', Fail: ', str(keyence_results[0][4] )+']'])

    processed_check_pass_results = process_tag_name(check_pass_results)
    check_pass_output = ', '.join([f'{i}: {j}' for i, j in processed_check_pass_results.items()])

    file_name = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop', 'results.txt')
    single_hole_face_names = ['220', '260', '440', '490-AB', '490-CD', '442', '460']

    with open(file_name, 'a+', newline='') as f:
        f.write(s[:-4] + ', ')
        f.write(keyence_string + ' ')

        for i in single_hole_face_names:
            if i in keyence_string or int(machine_num) == 4:
                f.write(pass_fail_output)
                f.write(f"[{check_pass_output}]\n\n")
                break
# END write_part_results

# # Example Usage
# machine_num = '4'
# results_dict = {'PUN': {1: 'pun_value'}}
# keyence_results = [[1, 2, 3, 0, 0]]
# keyence_string = 'xxxxMASTER42069_2023-12-06-13-43-54_H442_X80P'
# check_pass_results = {'Check_Pass.1': 0, 'Check_Pass.2': 0}

# write_part_results(machine_num, results_dict, keyence_results, keyence_string, check_pass_results)
