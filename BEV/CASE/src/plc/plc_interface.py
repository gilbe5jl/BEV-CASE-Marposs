# plc_interface.py
from abc import ABC, abstractmethod

class PLCInterface(ABC):
    @abstractmethod
    def connect(self):
        """Establish connection to the PLC."""
        pass

    @abstractmethod
    def disconnect(self):
        """Close connection to the PLC."""
        pass

    @abstractmethod
    def read_tag(self, tag: str):
        """Read the value of a PLC tag."""
        pass

    @abstractmethod
    def write_tag(self, tag: str, value):
        """Write a value to a PLC tag."""
        pass

    @abstractmethod
    def reset_tags(self, tags: list):
        """Reset a list of PLC tags to a default state."""
        pass