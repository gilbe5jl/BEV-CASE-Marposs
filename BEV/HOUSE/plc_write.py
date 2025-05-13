from plc_utils import PhoenixPLC
from tag_lists import TagMode

def handle_exceptions(func):
    '''
    This will have to go into its own file
    '''
    def wrapper(*args, **kwargs):
        self = args[0]  # assuming the first argument is 'self'
        try:
            return func(*args, **kwargs)
        except (CommError,Exception) as error:
            print(f"PLC Comm Error({func.__name__}): {error}")
            return False
    return wrapper



class PhoenixWriter:
    """
    This class is used to write data to the PLC.
    """
    def __init__(self, parent: PhoenixPLC):
        self.parent = parent

    @handle_exceptions
    def batch(self,results: dict) -> None:
        """
        Writes the results to the PLC using the pycomm3 library.
        :param results: A dictionary containing the tag names and their corresponding values.
        :return: None
        """
        for i in self.parent.input_tags:
            tag = f"{self.parent.write_prefix}{i}"
            if i not in results:
                raise KeyError(f"Tag '{i}' not found in the results dictionary.")
            value = results[i][1]
            self.parent.plc.write((tag, value))
    # END write_plc

    @handle_exceptions
    def single(self,tag_name:str, tag_val) -> None:
        """
        Writes a single tag to the PLC using the pycomm3 library.
        :param tag_name: The name of the tag to write.
        :param tag_val: The value to write to the tag.
        :return: None
        """
        tag = f"{self.parent.write_prefix}{self.parent.config_info['tags'][tag_name]}"
        self.parent.plc.write((tag, tag_val))
    #END write_single

    @handle_exceptions
    def bool_set(self) -> None:
        """
        """
        for tag_name, tag_val in self.parent.bool_tags.items():
            self.single(tag_name, tag_val)
    #END

    @handle_exceptions
    def fault_flush(self)-> None:
        """
        Flushes PLC fault tags to default values.
        :return: None
        """
        for tag_name, tag_val in self.parent.fault_flush_tags.items():
            self.single(tag_name, tag_val)
    #END fault_flush

    @handle_exceptions
    def flush(self) -> None:
        """
        Flushes PLC data mirroring tags (to 0)
        """
        default = {'PUN{64}': [0] * 64 }
        input_tags = self.parent.tag_list.inputs(TagMode.FULL)
        for tag in input_tags:
            if tag == 'PUN':
                self.plc.write((self.parent.write_prefix + tag, default['PUN{64}']))
            else:
                self.plc.write((self.parent.write_prefix + tag, 0))
    #END write_plc_flush