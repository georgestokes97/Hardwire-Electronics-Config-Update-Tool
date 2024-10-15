"""
MIT License

Copyright (c) 2024 George Stokes

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


Title: Hardwire Electronics CLI tool.
Author: George Stokes
Date: 09/10/2024
Description: Used to send config files to CAN connected Hardwire devices. 
"""

import argparse
import glob
import time
import json
from canlib import canlib, Frame
from enum import Enum

CANSENDID = 0x12E7B682
CANRECEIVEID = 0x12E7B681

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
bitrates = {
    '1M': canlib.Bitrate.BITRATE_1M,
    '500K': canlib.Bitrate.BITRATE_500K,
    '250K': canlib.Bitrate.BITRATE_250K,
    '125K': canlib.Bitrate.BITRATE_125K,
    '100K': canlib.Bitrate.BITRATE_100K,
    '62K': canlib.Bitrate.BITRATE_62K,
    '50K': canlib.Bitrate.BITRATE_50K,
    '83K': canlib.Bitrate.BITRATE_83K,
    '10K': canlib.Bitrate.BITRATE_10K,
}

class MSG_TYPE(Enum):
    INFO = 1
    CONFIG_SEND_START = 2
    CONFIG_DATA = 3

def string_format_fail(string):
    return bcolors.FAIL + string + bcolors.ENDC

def load_config_file(givenFileName):

    # see if config file given
    if(givenFileName == ''):
        print(string_format_fail('No Config File Specified'))
        return -1
    
    # see if config file is in the current directory
    if(len(glob.glob(f"{givenFileName}")) == 0):
        print(string_format_fail(f'Config File - {givenFileName}  not found in current directory'))
        return -1
  
    # open it
    try:
        configfile = open(glob.glob(f"{givenFileName}")[0], "r")
        print('Loading Config file: ' + str(glob.glob(f"{givenFileName}")[0]))
    except:
        print(string_format_fail('Could not open config file.'))
        return -1
            
    # load it as json
    try: 
        configfile = json.loads(configfile.read())
    except:
        print(string_format_fail('Could not read config file'))
        return -1

    # from the config file, get the data which is sent to the PDM via CAN. 
    try:
        rawSendData = configfile["rawSendData"]
    except:
        print(string_format_fail('Invalid Config File'))
        return -1
    
    configVersion = configfile["MetaData"]["ConfiguratorVersion"].replace(".", "")
    configDeviceModel = configfile["Global"]["deviceModelVersion"]

    print(f'Config File Version:{configVersion}')
    print(f'Config File Device Model:{configDeviceModel}')

    if(len(configDeviceModel) < 1):
        print(string_format_fail('Invalid device model'))

    return rawSendData, configVersion, configDeviceModel

def print_channels(selectedChannel):
    print(' ')
    print('CAN Channel:')
    for ch in range(canlib.getNumberOfChannels()):
        chdata = canlib.ChannelData(ch)
        selected = ''
        if(ch == selectedChannel):
            selected = bcolors.OKGREEN + '<-- Selected' + bcolors.ENDC
        print(f"{ch}. {chdata.channel_name} ({chdata.card_upc_no} / {chdata.card_serial_no})  {selected}")

def print_bitrate(selectedBitrate):
    print('')
    print('Bit Rate:')
    for br in bitrates:
        selected = ''
        if(br == selectedBitrate):
            selected = bcolors.OKGREEN + '<-- Selected' + bcolors.ENDC
        print(f"{br}   {selected}")

def removeDuplicateInfoMessages(deviceResponses):
    # for response in deviceResponses:
    #     print(response.data[1] <<24 | response.data[2] << 16 | response.data[3] << 8 | response.data[4] )

    i=0
    while(True):
        currentID = deviceResponses[i].data[1] <<24 | deviceResponses[i].data[2] << 16 | deviceResponses[i].data[3] << 8 | deviceResponses[i].data[4] 

        j=i+1
        while(j< len(deviceResponses)):
            compareID = deviceResponses[j].data[1] <<24 | deviceResponses[j].data[2] << 16 | deviceResponses[j].data[3] << 8 | deviceResponses[j].data[4] 
            if(compareID == currentID):
                deviceResponses.pop(j)
                continue
            j+=1
              
        i+=1
        if(i >= len(deviceResponses)):
            break

    return deviceResponses

def printDevice(deviceNumber, CANFrame):
    print(deviceNumber, end='  ')

    # Data bytes 
    #   0       1       2       3       4       5       6       7
    #   INFOMSG ID0     ID1     ID2     ID3     MODEL   FW VER  0  

    # make sure that this message is a device info message
    if(CANFrame.data[0] != MSG_TYPE.INFO.value):
        print(string_format_fail('Invalid device info message'), CANFrame)
        return -1

    deviceModel = CANFrame.data[5]
    deviceID = CANFrame.data[1] <<24 | CANFrame.data[2] << 16 | CANFrame.data[3] << 8 | CANFrame.data[4] 
    deviceFWVer = CANFrame.data[6]

    print(f'Model: {deviceModel},  ID: {deviceID},  FW Ver: {deviceFWVer}')

def chooseHardwireDevice(deviceList, configVersion, configDeviceModel):
  
    print('Detected Hardwire Devices')

    validDeviceList = []
    
    for x in range(len(deviceList)):
        if(printDevice(x, deviceList[x]) != -1):
            validDeviceList.append(x)
    
    print(' ')

    if(len(validDeviceList) == 0):
        print(string_format_fail('No valid info frames received from Hardwire Devices'))
        return -1
    
    if(len(validDeviceList) == 1):
        print(f'Only one device found -> {validDeviceList[0]}')
        returnDevice =  deviceList[validDeviceList[0]]

    if(len(validDeviceList) > 1):
        selectedDevice = -1
        while(True):
            selectedDevice = input('More than one device found. Enter device number to use: ')
            if(selectedDevice.isdigit() == False):
                print('Invalid entry. Enter a number')
            elif(int(selectedDevice) in validDeviceList):
                returnDevice = deviceList[int(selectedDevice)]
                break
            else:
                print('Entered device number is not in the list of available devices')


    # check to make sure that the device FW version matches the config version
    if(returnDevice.data[6] != int(configVersion)):
        print(returnDevice.data[6], configVersion)
        return -1
    
    if(returnDevice.data[5] != int(configDeviceModel)):
        print(string_format_fail(f'Config File is made for device model: {returnDevice.data[5]}. You have selected device model: {configDeviceModel}'))
        return -1

    return returnDevice

def getConfigSendDataArray(rawConfigFile):
    configArray = []

    rawConfigFileLineNum = 0
    rawConfigFileLineCharNum = 0
    
    endOfFile = False
    while(endOfFile == False):

        formattedLine = []
        for i in range(0, 6):
            #we need to fill the line with 6 bytes. (thats the only space avaialbe in the CAN data packet which is 8 bytes. [MSG_TYPE, MSG_INDEX, Data 0, Data 1, Data 2, Data 3, Data 4, Data 5])
          
            rawConfigFileLine = rawConfigFile[rawConfigFileLineNum]

            formattedLine.append(rawConfigFileLine[rawConfigFileLineCharNum])

            rawConfigFileLineCharNum+=1

            if(rawConfigFileLineCharNum >= len(rawConfigFileLine)):
                rawConfigFileLineNum+=1
                rawConfigFileLineCharNum=0

            if(rawConfigFileLineNum >= len(rawConfigFile)):
                endOfFile = True

                for j in range (0,6):
                    if(len(formattedLine) <6):
                        formattedLine.append('\n')
                break

        print(f'Building Send Data: {printProgressBar(rawConfigFileLineNum, len(rawConfigFile), length = 50)}', end='\r')
        configArray.append(formattedLine)
        
    return configArray

def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):

    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    return f'{prefix} |{bar}| {percent}% {suffix}'
    # Print New Line on Complete

def updateHardwireDeviceConfig(ch, CANFrame, rawConfigFile):
    deviceModel = CANFrame.data[5]
    deviceID = CANFrame.data[1] <<24 | CANFrame.data[2] << 16 | CANFrame.data[3] << 8 | CANFrame.data[4] 
    deviceFWVer = CANFrame.data[6]

    print(' ')
    doWeUpdate = input(f'Update device (Model: {deviceModel},  ID: {deviceID},  FW Ver: {deviceFWVer}) configuration file? y/n: ')

    if(doWeUpdate.upper() != 'Y'):
        print('Device update cancelled.')
        return -1
    
    print('\nInitiating config update.')
    
    configSendDataArray = getConfigSendDataArray(rawConfigFile)

    print('\n')

    print('Establishing communication with device.')

    # send message to device to signal that we are starting config send
    dataArray = [MSG_TYPE.CONFIG_SEND_START.value,
                CANFrame.data[1],
                CANFrame.data[2],
                CANFrame.data[3],
                CANFrame.data[4],
                0,
                0,
                0]
    frameSend = Frame(id_=CANSENDID, data=dataArray, dlc=8, flags=canlib.MessageFlag.EXT)
    ch.iocontrol.flush_rx_buffer()
    ch.write(frameSend)
    ch.writeSync(100)
    time.sleep(0.001)   

    #wait for reply
    while(True):
        try: 
            try :
                ch.readSyncSpecific(CANRECEIVEID, 100)
            except canlib.exceptions.CanTimeout:
                print(string_format_fail('\nLost communication with device. Update cancelled'))
                return          
            frameReceive = ch.readSpecificSkip(CANRECEIVEID)
            
            if(frameSend.data != frameReceive.data):
                print(string_format_fail('\nCAN receive error. Update cancelled'))
                return
            
            if(frameReceive.flags == canlib.MessageFlag.ERROR_FRAME):
                print(string_format_fail('\nCAN receive error. Update cancelled'))
                return
            
            break
        except canlib.canNoMsg:
            print(string_format_fail('\nLost communication with device. Update cancelled'))
            return

    #now we can start sending the configuration
    print('Communication established, starting config update.', end='\n\n')

    configSendArrPos = 0

    errorCounter = 0
    while(True):
        # send line of config

        dataArray = [MSG_TYPE.CONFIG_DATA.value,
                    configSendArrPos%256,
                    ord(configSendDataArray[configSendArrPos][0]),
                    ord(configSendDataArray[configSendArrPos][1]),
                    ord(configSendDataArray[configSendArrPos][2]),
                    ord(configSendDataArray[configSendArrPos][3]),
                    ord(configSendDataArray[configSendArrPos][4]),
                    ord(configSendDataArray[configSendArrPos][5]),]
        
        frameSend = Frame(id_=CANSENDID, data=dataArray, dlc=8, flags=canlib.MessageFlag.EXT)
 
        ch.iocontrol.flush_rx_buffer()
        ch.write(frameSend)
        ch.writeSync(100)
        
        time.sleep(0.001)  #<-- seems a delay reduces errors some time. Rx buffer can become corrupt without
        # print(f'Sending Config ID:{CANSENDID} Data: {configSendDataArray[configSendArrPos]}, Completion:{round((configSendArrPos/(len(configSendDataArray)-1))*100, 1)}%  {configSendArrPos}/{len(configSendDataArray)-1} Errors:{errorCounter}    ', end='\n')
        print(f'Sending Config - Progress: {printProgressBar(configSendArrPos, len(configSendDataArray), length = 50)}  Completed: {configSendArrPos}/{len(configSendDataArray)-1}  Errors:{errorCounter}    ', end='\r')

        configSendArrPos+=1

        #wait for reply
        try: 
            try :
                ch.readSyncSpecific(CANRECEIVEID, 100)
            except canlib.exceptions.CanTimeout:
                if(configSendArrPos >= len(configSendDataArray)):
                    break
                print(string_format_fail('\nLost communication with device. Update cancelled'))
                return          
            frameReceive = ch.readSpecificSkip(CANRECEIVEID)
            
            if(frameSend.data != frameReceive.data):
                errorCounter+=1   
                configSendArrPos -=1
                
            if(frameReceive.flags == canlib.MessageFlag.ERROR_FRAME):
                print(string_format_fail('\nCAN receive error. Update cancelled'))
                return
        except canlib.canNoMsg:
            print(string_format_fail('\nLost communication with device. Update cancelled'))
            return

        if(configSendArrPos >= len(configSendDataArray)):
            break
    
    print('')
     
def getInitialDeviceResponses(ch):
# send initial message to PDM and wait until it responds with device type, ID, and firmware version
    frameSend = Frame(id_=CANSENDID, data=[MSG_TYPE.INFO.value,0,0,0,0,0,0,0], dlc=8, flags=canlib.MessageFlag.EXT)

    gotResponse = False
    sendAttempts = 0
    frameReceive = 0
    deviceResponses = []
    while(gotResponse == False):

        # send start message to all devices
        try:
            ch.write(frameSend)
            sendAttempts +=1
        except canlib.canError as error:
            print(string_format_fail(f'Failed to send CAN message: {error}'))
            ch.busOff()
            ch.close()
            return -1
        
        # wait for response. There may be more than one so we wait until all responses have been gathered
        while(True):

            try: 
                frameReceive = ch.read(timeout=1000)
                if(frameReceive.flags != canlib.MessageFlag.ERROR_FRAME):
                    deviceResponses.append(frameReceive)
                    gotResponse = True

            except canlib.canNoMsg:
                print('.', end=' ', flush=True)
                break
            except canlib.canError as error:
                print(string_format_fail(f'Failed to receive CAN message: {error}'))
                ch.busOff()
                ch.close()
                return -1

        if(sendAttempts >= 10):
            print('\n')
            print(string_format_fail(f'No Hardwire device detected'))
            ch.busOff()
            ch.close()
            return -1

    print('\n')

    return deviceResponses

def CAN_comms(channel, bitrate, rawConfigFile, configVersion, configDeviceModel):

    print('')
    print('Attempting to start CAN communication')
    print_channels(channel)
    print_bitrate(bitrate)

    # open channel
    ch = canlib.openChannel(channel, bitrate=bitrates[bitrate.upper()])
    ch.setBusOutputControl(canlib.canDRIVER_NORMAL)

    ch.canSetAcceptanceFilter(CANRECEIVEID, 0x1FFFFFFF, is_extended=True)
    ch.canSetAcceptanceFilter(0x000, 0x7FF, is_extended=False)
   
    ch.busOn()
    ch.iocontrol.flush_rx_buffer()
    print('')
    print('Waiting for response')

    deviceResponses = getInitialDeviceResponses(ch)

    if(deviceResponses == -1):
        return -1

    deviceResponses = removeDuplicateInfoMessages(deviceResponses)

    chosenDevice = chooseHardwireDevice(deviceResponses, configVersion, configDeviceModel)

    if(chosenDevice == -1):
        return -1
    
    updateHardwireDeviceConfig(ch, chosenDevice, rawConfigFile)

    print(bcolors.OKGREEN + 'Update completed' + bcolors.ENDC)

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Used to send config files to CAN connected Hardwire devices."
    )
    parser.add_argument('--channel', '-c',  type=int,   default=0,      help= ("Channel, Which channel the Kvaser CAN device is on"))
    parser.add_argument('--bitrate', '-b',  type=str ,  default='250k', help=("Bitrate, one of " + ', '.join(bitrates.keys())))
    parser.add_argument('--filename', '-f', type=str, default='',      help=("config file name e.g ./hardwire-config-files/testp-config.HWPDM"))
 
    args = parser.parse_args(argv)

    # user message
    print(bcolors.HEADER + 'Hardwire Config Update CLI Tool. -h for help' + bcolors.ENDC)
    print('.')

    # load in HWPDM config file
    try:
        rawSendData, configVersion, configDeviceModel = load_config_file(args.filename)
    except:
        return -1

    if(rawSendData == -1):
        return -1

    # go on to CAN bus and attempt to start communication with the Hardwire Device. 
    if(CAN_comms(args.channel, args.bitrate, rawSendData, configVersion, configDeviceModel) == -1):
        return -1

if __name__ == '__main__':
    raise SystemExit(main())