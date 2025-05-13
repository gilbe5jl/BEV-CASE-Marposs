from enum import Enum, auto
from config_loader import Config

class TagMode(Enum):
    BASIC = auto()
    FULL = auto()
class TagList:
    def __init__(self):
        self.tags = Config().get().get('tags', {})


    # def fault_tag_list(self):
    #     returnList = [
    #         self.tags['Faulted'],
    #         self.tags['PhoenixFltCode'],
    #         self.tags['KeyenceFltCode']
    #     ]
    #     return returnList

    def bool_reset(self)->dict:
        tags = {
            'Done': False,
            'Pass': False,
            'Busy': False,
            'Fail': False,
            'Ready': True
        }
        return tags

    def fault_reset(self)->dict:
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
        return fault_tag_data

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
        """
        Returns a list of input tags based on the specified mode.
        :param mode: The mode to determine which tags to include.
        :return: A list of input tags.
        """
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