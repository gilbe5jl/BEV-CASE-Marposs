from enum import Enum, auto

class InspectionState(Enum):
    IDLE = auto()
    LOAD_PROGRAM = auto()
    START_INSPECTION = auto()
    WAIT_FOR_DONE = auto()
    INSPECTION_COMPLETE = auto()
    ERROR = auto()

class KeyenceControllerStateMachine:
    def __init__(self, controller_id, plc_interface, keyence_interface):
        self.controller_id = controller_id
        self.plc = plc_interface
        self.keyence = keyence_interface
        self.state = InspectionState.IDLE

    def update(self):
        try:
            if self.state == InspectionState.IDLE:
                if self.plc.read_condition_to_start(self.controller_id):
                    self.keyence.load_program(self.controller_id)
                    self.state = InspectionState.LOAD_PROGRAM

            elif self.state == InspectionState.LOAD_PROGRAM:
                if self.keyence.program_loaded(self.controller_id):
                    self.keyence.start_inspection(self.controller_id)
                    self.state = InspectionState.START_INSPECTION

            elif self.state == InspectionState.START_INSPECTION:
                if self.keyence.inspection_started(self.controller_id):
                    self.state = InspectionState.WAIT_FOR_DONE

            elif self.state == InspectionState.WAIT_FOR_DONE:
                if self.keyence.inspection_done(self.controller_id):
                    self.plc.signal_complete(self.controller_id)
                    self.state = InspectionState.INSPECTION_COMPLETE

            elif self.state == InspectionState.INSPECTION_COMPLETE:
                if self.plc.reset_signal_received(self.controller_id):
                    self.state = InspectionState.IDLE

        except Exception as e:
            self.state = InspectionState.ERROR
            self.plc.signal_error(self.controller_id, str(e))
