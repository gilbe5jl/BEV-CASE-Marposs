# allen_bradley_plc.py
from plc.plc_interface import PLCInterface
from pycomm3 import LogixDriver, CommError 
from pycomm3.tag import Tag




"""
NOTE: 
We might wish to choose to retry, return None, or re-raise the errors.
    -- This still needs to be determined.
    -- We will also want to log the errors.
    -- We will want to add a retry mechanism.
    -- We will want to add a timeout mechanism.
    -- We will want to add a backoff mechanism. This is a mechanism that will increase the time between retries. Maybe.
    -- We will want to add a logging mechanism.
"""
class AllenBradleyPLC(PLCInterface):
    def __init__(self, ip_address: str):
        self.ip_address = ip_address
        self.connection = None

    def connect(self):
        try:
            self.connection = LogixDriver(self.ip_address)
            self.connection.open()
            return self.connection
        except CommError as e:
            print(f"Error connecting to PLC at {self.ip_address}: {e}")
            # raise # This will raise the error to the caller and print the traceback to the console.
        # except TimeoutError as te: # not needed it is already caught by CommError
            # print(f"Timeout while connecting to PLC at {self.ip_address}: {te}")
            # raise

    def disconnect(self):
        if self.connection:
            try:
                self.connection.close()
            except CommError as e:
                print(f"Error disconnecting from PLC at {self.ip_address}: {e}")
            finally:
                self.connection = None

    def read_tag(self, tag: str):
        if not self.connection:
            self.connect()
        try:
            result = self.connection.read(tag)
            key = result.tag.split(".")[-1]
            return {key: (result.tag, result.value, result.type, result.error)}
        except CommError as e:
            print(f"Error reading tag '{tag}' from PLC: {e}")
            # raise
    def batch_read(self):
        if not self.connection:
            self.connect()
        try:
            results = self.connection.read(*self.tag_list)
            return {
                result.tag.split(".")[-1]: (result.tag, result.value, result.type, result.error)
                for result in results
            }
        except CommError as e:
            print(f"Error batch reading tags from PLC: {e}")
            # raise

    def write_tag(self, tag: str, value):
        if not self.connection:
            self.connect()
        try:
            self.connection.write(tag, value)
        except CommError as e:
            print(f"Error writing value '{value}' to tag '{tag}' on PLC: {e}")
            # raise

    def reset_tags(self, tags: list):
        for tag in tags:
            try:
                self.write_tag(tag, 0)
            except CommError as e:
                print(f"Error resetting tag '{tag}': {e}")