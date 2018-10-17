#!/usr/bin/env python3
"""If there are any unrecognized bluetooth or USB devices,
laptop power is unplugged, laptop battery is removed while on AC,
or the disk tray is tampered with, shut the computer down!
"""
#         _  _  _  _ _
#        | |/ /(_)| | |
#        |   /  _ | | | ____ _ _
#        |  \  | || | |/ _  ) `_|
#        | | \ | || | ( (/_/| |
#        |_|\_\|_|\__)_)____)_|
# _____________________________________
# \                       | _   _   _  \
#  `.                  ___|____________/
#    ``````````````````


# <https://github.com/Lvl4Sword/Killer>
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/agpl.html>.

__version__ = "0.2.4"
__author__ = "Lvl4Sword"

import argparse
import os
import platform
import re
import subprocess
import sys
import time

DEBUG = False

# Determine what platform we're running
WINDOWS = sys.platform.startswith('win32')
LINUX = sys.platform.startswith('linux')
OSX = sys.platform.startswith('darwin')
BSD = OSX or 'bsd' in sys.platform
POSIX = LINUX or BSD

# Detect if we're running in Windows Subsystem for Linux (WSL)
WSL = not WINDOWS and 'Microsoft' in platform.version()

if WINDOWS:
    import wmi
    import ctypes
    from ctypes import wintypes
elif POSIX:
    import fcntl

# Regular expressions
BT_MAC_REGEX = re.compile("(?:[0-9a-fA-F]:?){12}")
BT_NAME_REGEX = re.compile("[0-9A-Za-z ]+(?=\s\()")
BT_CONNECTED_REGEX = re.compile("(Connected: [0-1])")
USB_ID_REGEX = re.compile("([0-9a-fA-F]{4}:[0-9a-fA-F]{4})")

# Bluetooth
BT_PAIRED_WHITELIST = {"DE:AF:BE:EF:CA:FE": "Generic Bluetooth Device"}
BT_CONNECTED_WHITELIST = ["DE:AF:BE:EF:CA:FE"]

# USB
# Windows' format is 8 digits without :
USB_ID_WHITELIST = ["DEAF:BEEF"]

# AC
AC_FILE = "/sys/class/power_supply/AC/online"

# Battery
BATTERY_FILE = "/sys/class/power_supply/BAT0/present"

# CD/DVD Tray
CDROM_DRIVE = "/dev/sr0"

# Ethernet connection
# If Windows, this is not used. Go to ETHERNET_INTERFACE
ETHERNET_CONNECTED = "/sys/class/net/EDIT_THIS/carrier"

# Windows-only. set to MAC address of the Ethernet interface
ETHERNET_INTERFACE = "DE-AD-BE-EF-CA-FE"

# If using windows, set this to 5 to ensure the USB powershell runs properly.
REST = 2


def detect_bt():
    """detect_bt looks for paired MAC addresses,
    names for paired devices, and connected status for devices.
    Two whitelists, one for paired, one for connected.
    """
    if POSIX:
        try:
            bt_command = subprocess.check_output(["bt-device", "--list"],
                                                 shell=False).decode()
        except IOError:
            if DEBUG:
                print("None detected\n")
            else:
                return
        else:
            if DEBUG:
                print("Bluetooth:")
                print(bt_command)
            else:
                paired_devices = re.findall(BT_MAC_REGEX, bt_command)
                devices_names = re.findall(BT_NAME_REGEX, bt_command)
                for each in range(0, len(paired_devices)):
                    if paired_devices[each] not in BT_PAIRED_WHITELIST:
                        kill_the_system()
                    else:
                        connected = subprocess.check_output(["bt-device", "-i",
                                                             paired_devices[each]],
                                                             shell=False).decode()
                        connected_text = re.findall(BT_CONNECTED_REGEX, connected)
                        if connected_text[0].endswith("1") \
                                and paired_devices[each] not in BT_CONNECTED_WHITELIST:
                            kill_the_system()
                        elif connected_text[0].endswith("1") \
                                and each in BT_CONNECTED_WHITELIST:
                            if not devices_names[each] == BT_PAIRED_WHITELIST[each]:
                                kill_the_system()


def detect_usb():
    """detect_usb finds all XXXX:XXXX USB IDs connected to the system.
    This can include internal hardware as well.
    """
    if POSIX:
        ids = re.findall(USB_ID_REGEX,
                         subprocess.check_output("lsusb", shell=False).decode())
        if DEBUG:
            print("USB:")
            print(ids)
        else:
            for each in ids:
                if each not in USB_ID_WHITELIST:
                    kill_the_system()
    elif WINDOWS:
        if DEBUG:
            print("USB:")
        for each in wmi.WMI().Win32_LogicalDisk():
            if DEBUG:
                print(each)
            else:
                if each not in USB_ID_WHITELIST:
                    kill_the_system()


def detect_ac():
    """detect_ac checks if the system is connected to AC power
    Statuses:
    0 = disconnected
    1 = connected
    """
    if POSIX:
        if DEBUG:
            ac_types = []
            for each in os.listdir("/sys/class/power_supply"):
                with open("/sys/class/power_supply/{0}/type".format(each)) as power_file:
                    the_type = power_file.readline().strip()
                    if the_type == "Mains":
                        ac_types.append(each)
            print("AC:")
            if ac_types:
                print(ac_types)
            else:
                print("None detected\n")

        else:
            with open(AC_FILE) as ac:
                online = int(ac.readline().strip())
                if online == 0:
                    kill_the_system()


def detect_battery():
    """detect_battery checks if there is a battery.
    Obviously this is useless if your system does not have a battery.
    Statuses:
    0 = not present
    1 = present
    """
    if POSIX:
        if DEBUG:
            battery_types = []
            for each in os.listdir("/sys/class/power_supply"):
                with open("/sys/class/power_supply/{0}/type".format(each)) as power_file:
                    the_type = power_file.readline().strip()
                    if the_type == "Battery":
                        battery_types.append(each)
            print("Battery:")
            if battery_types:
                print(battery_types)
            else:
                print("None detected\n")
        else:
            try:
                with open(BATTERY_FILE) as battery:
                    present = int(battery.readline().strip())
                    if present == 0:
                        kill_the_system()
            except FileNotFoundError:
                pass


def detect_tray(drive=CDROM_DRIVE):
    """detect_tray reads status of the CDROM_DRIVE.
    Statuses:
    1 = no disk in tray
    2 = tray open
    3 = reading tray
    4 = disk in tray
    """
    if POSIX:
        fd = os.open(drive, os.O_RDONLY | os.O_NONBLOCK)
        rv = fcntl.ioctl(fd, 0x5326)
        os.close(fd)


def detect_power():
    class SYSTEM_POWER_STATUS(ctypes.Structure):
        _fields_ = [
            ('ACLineStatus', ctypes.c_ubyte),
            ('BatteryFlag', ctypes.c_ubyte),
        ]

    SYSTEM_POWER_STATUS_P = ctypes.POINTER(SYSTEM_POWER_STATUS)

    GetSystemPowerStatus = ctypes.windll.kernel32.GetSystemPowerStatus
    GetSystemPowerStatus.argtypes = [SYSTEM_POWER_STATUS_P]
    GetSystemPowerStatus.restype = wintypes.BOOL

    status = SYSTEM_POWER_STATUS()
    if not GetSystemPowerStatus(ctypes.pointer(status)):
        raise ctypes.WinError()
    else:
        if DEBUG:
            print('ACLineStatus', status.ACLineStatus)
            print('BatteryFlag', status.BatteryFlag)
        else:
            if ('ACLineStatus', status.ACLineStatus) != 1:
                # If not connected to power, shutdown
                kill_the_system()
            elif ('BatteryFlag', status.BatteryFlag) not in [0, 1, 2, 4, 8, 9, 10, 12]:
                if ('BatteryFlag', status.BatteryFlag) == 128:
                    # Battery not detected, so this is useless
                    pass
                else:
                    # Battery is not connected, shut down
                    kill_the_system()


def detect_ethernet():
    """Check if an ethernet cord is connected.
    Status:
    0 = False
    1 = True
    """
    if POSIX:
        with open(ETHERNET_CONNECTED) as ethernet:
            connected = int(ethernet.readline().strip())
        if DEBUG:
            print("Ethernet:")
            print(connected)
        else:
            if connected == 0:
                kill_the_system()
    elif WINDOWS:
        for x in wmi.WMI().Win32_NetworkAdapter():
            if x.NetworkConnectionStatus is not None:
                if DEBUG:
                    # This can contain quite a few things
                    # Including Ethernet, Bluetooth, and Wireless 
                    print(x.Name)
                    print(x.NetConnectionStatus)
                    print(x.MacAddress)
                else:
                    if x.MacAddress == ETHERNET_INTERFACE:
                        # This should probably be clearer, but for the time being:
                        # https://github.com/Lvl4Sword/Killer/wiki/Windows-Connection-Status-Codes
                        if x.NetConnectionStatus == 7:
                            kill_the_system()


def kill_the_system():
    """Shut the system down quickly"""
    if WINDOWS:
        subprocess.Popen(["shutdown.exe", "/s", "/f", "/t", "00"])
    else:
        subprocess.Popen(["/sbin/poweroff", "-f"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Prints all info once, without worrying about shutdown.")
    args = parser.parse_args()
    global DEBUG
    DEBUG = args.debug
    while True:
        detect_bt()
        detect_usb()
        detect_ac()
        detect_battery()
        detect_tray(CDROM_DRIVE)
        detect_ethernet()
        if DEBUG:
            break
        else:
            time.sleep(REST)


if __name__ == "__main__":
    main()
