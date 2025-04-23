from plc.plc_utils import PLCUtils
from plc.allen_bradley_plc import AllenBradleyPLC

plc_ip = PLCUtils.config().get('plc_ip')
plc = AllenBradleyPLC(plc_ip)
plc.connect()

# Connect to the PLC
# Connect to keyence controller
