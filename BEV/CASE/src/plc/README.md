# PLC Module

This module handles all interactions with the PLC hardware in a decoupled and modular way. It uses an abstract interface to define how PLC communications should work, allowing you to easily swap or extend implementations (for example, to support additional vendors or to create mocks for testing).

## Files

- **plc_interface.py**  
  Defines the abstract base class (`PLCInterface`) that specifies the contract for PLC operations such as connecting, reading, writing, and resetting tags.

- **allen_bradley_plc.py**  
  Contains a concrete implementation of the `PLCInterface` using the `pycomm3` library to communicate with Allen-Bradley PLCs.

## Usage

1. **Importing the Implementation**  
   The business logic imports the concrete PLC class:
   ```python
   from plc.allen_bradley_plc import AllenBradleyPLC


