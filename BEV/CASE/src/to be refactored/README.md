The flow is essentially:
	1.	Load program
	2.	Start program
	3.	Wait for BUSY
	4.	End program
	5.	Wait for DONE
	6.	Read result
	7.	Handle fault / reset if needed

The PLC doesn’t care how you go from LOAD_PROGRAM to DONE, it only cares when and how the bits are flipped.

structured around controlling and coordinating inspection processes for a Keyence controller through a PLC

