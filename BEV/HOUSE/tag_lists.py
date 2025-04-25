import json
import sys
import os
from enum import Enum, auto

class TagMode(Enum):
    BASIC = auto()
    FULL = auto()
class TagList:
    def __init__(self):
        self.tags = self.get_config()

    def get_config(self):
        with open(os.path.join(sys.path[0], 'config.json'), "r") as config_file:
            config_data = config_file.read()
            config_info = json.loads(config_data)
        return config_info.get('tags', {})
    # def fault_tag_list(self):
    #     returnList = [
    #         self.tags['Faulted'],
    #         self.tags['PhoenixFltCode'],
    #         self.tags['KeyenceFltCode']
    #     ]
    #     return returnList
    def results(self): 
        returnList = [
            'DefectNumber',
            'DefectSize',
            'DefectZone',
            'Pass',
            'Fail',
            'MaskFail',
            'SizeFail',
            'SpacingFail',
            'DensityFail'
        ]
        return returnList
    
    def outputs(self):
        tags = self.tags
        returnList = [
            tags['LoadProgram'],
            tags['StartProgram'],
            tags['EndProgram'],
            tags['AbortProgram'],
            tags['Reset'],
            tags['PartType'],
            tags['PartProgram'],
            tags['ScanNumber'],
            tags['PUN'],
            tags['GMPartNumber'],
            tags['Module'],
            tags['PlantCode'],
            tags['Month'],
            tags['Day'],
            tags['Year'],
            tags['Hour'],
            tags['Minute'],
            tags['Second']
        ]
        return returnList
    
    def inputs(self,mode: TagMode):
        tags = self.tags
        base_tags = [
            tags['PartType'],
            tags['PartProgram'],
            tags['ScanNumber'],
            'PUN',
            tags['Module'],
            tags['PlantCode'],
            tags['Month'],
            tags['Day'],
            tags['Year'],
            tags['Hour'],
            tags['Minute'],
            tags['Second'],
        ]
        if mode == TagMode.FULL:
            base_tags.extend([tags['Busy'], tags['Done']])
        return base_tags