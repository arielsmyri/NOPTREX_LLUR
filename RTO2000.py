import numpy as np
import pandas as pd
from RsInstrument import *
import os
from time import time


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
instr = RsInstrument(resource_string_1)

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



instr.visa_timeout = 3000
instr.write_with_opc("INIT")

#Fetching waveform
def measure():
    waveform = instr.query_bin_or_ascii_int_list('FORM ASC;:CHAN1:DATA?')
    print(f'Results: {waveform}')
    return waveform

#writing info to file is so desired
def writeWaveform():
    instr.data_chunk_size = 10000
    instr.query_bin_block_to_file(
        'FORM REAL,32;:CHAN1:DATA?',
        r'c:\temp\rto_waveform_data.bin', #FIX THIS OR UR FRIED KIDDO -- USE OS PATH METHOD
        append=False)

instr.close() #Session Close