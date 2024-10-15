
<!-- LICENSING -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


<!-- ABOUT THIS PROJECT -->
## About The Project
A simple CLI tool for updating the configuration files on Hardwire Devices via CAN bus using Kvaser USB to CAN as an interface.

<!-- GETTING STARTED -->
## Getting Started
The tool is built using python, and uses the CANlib library for interfacing with the Kvaser CAN bus devices. 

1. Clone the repo
   ```sh
   git clone https://github.com/georgestokes97/Hardwire-Electronics-Config-Update-Tool.git
   ```
2. Install required packages
    ```sh
    pip install -r requirements.txt
    ```
### Windows
<p>On <strong>Windows</strong>, first install the <code class="docutils literal notranslate"><span class="pre">canlib32.dll</span></code> by downloading and installing “Kvaser Drivers for Windows” which can be found on the <a class="reference external" href="https://kvaser.com/single-download/?download_id=47105">Kvaser Download page</a> (<a class="reference external" href="https://www.kvaser.com/downloads-kvaser/?utm_source=software&amp;utm_ean=7330130980013&amp;utm_status=latest">kvaser_drivers_setup.exe</a>) This will also install <code class="docutils literal notranslate"><span class="pre">kvrlib.dll</span></code>, <code class="docutils literal notranslate"><span class="pre">irisdll.dll</span></code>, <code class="docutils literal notranslate"><span class="pre">irisflash.dll</span></code> and <code class="docutils literal notranslate"><span class="pre">libxml2.dll</span></code> used by kvrlib.</p>
<p>The “Kvaser CANlib SDK” also needs to be downloaded from the same place (<a class="reference external" href="https://kvaser.com/single-download/">canlib.exe</a>) and installed if more than just CANlib will be used. This will install the rest of the supported library dll’s.</p>
<p>The two packages, “Kvaser Drivers for Windows” and “Kvaser CANlib SDK”, contains both 32 and 64 bit versions of the included dll’s.</p>

### Linux
<p>On <strong>Linux</strong>, first install the <code class="docutils literal notranslate"><span class="pre">libcanlib.so</span></code> by downloading and installing “Kvaser LINUX Driver and SDK” which can be found on the <a class="reference external" href="https://kvaser.com/single-download/?download_id=47147">Kvaser Download page</a> (<a class="reference external" href="https://www.kvaser.com/downloads-kvaser/?utm_source=software&amp;utm_ean=7330130980754&amp;utm_status=latest">linuxcan.tar.gz</a>).</p>

<!-- USAGE -->
## Usage
The CLI tool uses a Kvaser CAN to USB device to access the CAN Bus. If you have installed the required drivers for the Kvaser device, you can run `list-kvaser-devices.py` to show which channels are available. It will list the channels like below -
 ```sh
    Found 3 channels         
    0. Kvaser Leaf v3 (channel 0) (73-30130-01424-4 / 12841)
    1. Kvaser Virtual CAN Driver (channel 0) (00-00000-00000-0 / 0)
    2. Kvaser Virtual CAN Driver (channel 1) (00-00000-00000-0 / 0)
```
In this case, channel 0 will be used. 

To use the tool, you will need to create a hardwire config file in the Hardwire Electronics PDM configurator software in version 1.1.5 or later. You can save your configuration file and place it in the `hardwire-config-files` directory. <a class="reference external" href="https://drive.google.com/drive/u/1/folders/1srP_ZftM7S_RWoWvo1MFG4b2HitNSpq7">Hardwire Downloads</a>

You must make sure that the config file is made for the device you intend to send it to. 

You must also make sure that the Hardwire device Firmware version and the configuration software version number is the same. 

The tool uses an arbitrary CAN ID of `0x12E7B682` and `0x12E7B681` to send and receive data to/from the device. 

You can then run the CLI tool to update the Hardwire device configuration.

```sh
    python ./src/hardwire-pdm-cli-tool.py -c 0 -b 1M -f ./hardwire-config-files/test-config.HWPDM
```
Run the 'help' command for a list of the available options. 

```sh
usage: hardwire-pdm-cli-tool.py [-h] [--channel CHANNEL] [--bitrate BITRATE] [--filename FILENAME]

Used to send config files to CAN connected Hardwire devices.

options:
  -h, --help            show this help message and exit
  --channel CHANNEL, -c CHANNEL
                        Channel, Which channel the Kvaser CAN device is on
  --bitrate BITRATE, -b BITRATE
                        Bitrate, one of 1M, 500K, 250K, 125K, 100K, 62K, 50K, 83K, 10K
  --filename FILENAME, -f FILENAME
                        config file name e.g ./hardwire-config-files/testp-config.HWPDM
```

## Notes

This tool was made quickly, so bugs may be present. If you find any, email me.
It has been tested on windows 11 and Ubuntu with the Kvaser leaf leaf v3 and a PDM28. 

## Contact
George Stokes - 

george@hardwire-electronics.co.uk

[Linked In](https://www.linkedin.com/in/george-stokes-ba9b38116)
