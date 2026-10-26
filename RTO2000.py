import numpy as np
import pandas as pd
from RsInstrument import *
import os
from time import time
import sys



# def create(self, env_dir):
#     env_dir = os.path.abspath(env_dir)
#     context = self.ensure_directories(env_dir)
#     self.create_configuration(context)
#     self.setup_python(context)
#     self.setup_scripts(context)
#     self.post_setup(context)




RsInstrument.assert_minimum_version('1.102.0')
resource_string_1 = 'TCPIP::192.168.2.101::INSTR'  # Standard LAN connection (also called VXI-11)
resource_string_2 = 'TCPIP::192.168.2.101::hislip0'  # Hi-Speed LAN connection - see 1MA208
resource_string_3 = 'GPIB::20::INSTR'  # GPIB Connection
resource_string_4 = 'USB::0x0AAD::0x0119::022019943::INSTR'  # USB-TMC (Test and Measurement Class)
resource_string_5 = 'RSNRP::0x0095::104015::INSTR'  # R&S Powersensor NRP-Z86

#Initializing session
try:
    instr = RsInstrument(resource_string_2)
except:
    print("ERROR: Connect to the scope, dummy")
    sys.exit(1)

error_checking = True #If Error checking set to false, you reduce speed performance penalty by shutting off and flushing the scopes status subsystem; Recommended to leave on or else you might disable OPC-sync but idk that would be a really stupid feature

if error_checking == False:
    instr.instrument_status_checking = False
    instr.clear_status()
else:
    instr.instrument_status_checking = True
    instr.check_status()
    errors_list = instr.query_all_errors()
    print(errors_list)


idn = instr.query_str('*IDN?')

print(f"\nHello, I am: '{idn}'")
print(f'RsInstrument driver version: {instr.driver_version}')
print(f'Visa manufacturer: {instr.visa_manufacturer}')
print(f'Instrument full name: {instr.full_instrument_model_name}')
print(f'Instrument installed options: {",".join(instr.instrument_options)}')

channel = 1

instr.write_str('ACQuire:POINts:AUTO RECLength')   # keep record length fixed (verify enum name for your firmware)
instr.write_str('ACQuire:POINts 5000')

instr.write_str('CHANnel{channel}:SCALe 200E-3')              # V/div
instr.write_str('CHANnel{channel}:OFFSet -389E-3')               # V
instr.write_str('TIMebase:SCALe 5E-9')             # s/div (or TIMebase:RANGe)
instr.write_str('TIMebase:REFerence 50')           # % of screen
instr.write_str('TIMebase:HORizontal:POSition -8.71E-9')
instr.write_str('CHANnel{channel}:IMPedance 50')  # s
instr.write_str('CHANnel{channel}:COUpling DC')

instr.visa_timeout = 3000
instr.write_with_opc("INIT")

#Fetching waveform
def measure():
    waveform = abs(instr.query_bin_or_ascii_int_list('FORM ASC;:CHAN1:DATA?'))
    print(f'Results: {waveform}')
    return waveform

#writing waveform to file if so desired
path = os.abspath()

def writeWaveform():
    instr.data_chunk_size = 10000
    instr.query_bin_block_to_file(
        'FORM REAL,32;:CHAN1:DATA?',
        path,
        append=False)

def analysis(waveform): # Function designed to run full analysis on the waveform
    #FWHM
    peak = np.argmax(waveform)

    rightBound = peak
    leftBound = peak
    while rightBound < len(waveform) - 1 and waveform[rightBound] > waveform[rightBound + 1]:
        rightBound += 1
    while leftBound > 0 and waveform[leftBound] > waveform[leftBound - 1]:
        leftBound -= 1

    baseline = np.median(waveform)  # see note below

    peak = np.argmax(waveform)
    rightBound = peak
    leftBound = peak
    while rightBound < len(waveform) - 1 and waveform[rightBound] > waveform[rightBound + 1]:
        rightBound += 1
    while leftBound > 0 and waveform[leftBound] > waveform[leftBound - 1]:
        leftBound -= 1

    baseline = np.median(waveform)

    midpoint = baseline + 0.5 * (waveform[peak] - baseline)
    ninety = baseline + 0.9 * (waveform[peak] - baseline)
    ten = baseline + 0.1 * (waveform[peak] - baseline)

    ninetyLoc = 0
    midLoc = 0

    leftVal = peak
    rightVal = peak

    while waveform[leftVal] >= ten:
        if waveform[leftVal] > ninety:
            ninetyLoc = leftVal
        if waveform[leftVal] >= midpoint:
            midLoc = leftVal
        leftVal -= 1
    while waveform[rightVal] >= ten:
        rightVal += 1

    print(f"FWHM is {(rightVal - midLoc) / 100} nanoseconds")
    print(f"Rise time is {(ninetyLoc - leftVal) / 100} nanoseconds")

instr.close() #Session Close

analysis(measure())