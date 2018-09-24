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

__version__ = '0.1.6-2'
__author__ = 'Lvl4Sword'

import argparse
import fcntl
import os
import re
import subprocess
import sys
import time

### Regular expressions
BT_MAC_REGEX = re.compile('(?:[0-9a-fA-F]:?){12}')
BT_NAME_REGEX = re.compile('[0-9A-Za-z ]+(?=\s\()')
BT_CONNECTED_REGEX = re.compile('(Connected: [0-1])')
USB_ID_REGEX = re.compile('([0-9a-fA-F]{4}:[0-9a-fA-F]{4})')

### Bluetooth
BT_PAIRED_WHITELIST = {'DE:AF:BE:EF:CA:FE': 'Generic Bluetooth Device'}
BT_CONNECTED_WHITELIST = ['DE:AF:BE:EF:CA:FE']

### USB
USB_ID_WHITELIST = ['DE:AF:BE:EF']

### AC
AC_FILE = '/sys/class/power_supply/AC/online'

### Battery
BATTERY_FILE = '/sys/class/power_supply/BAT0/present'

### CD/DVD Tray
CDROM_DRIVE = '/dev/sr0'

REST = 2

def detect_bt():
    """detect_bt looks for paired MAC addresses,
    names for paired devices, and connected status for devices.
    Two whitelists, one for paired, one for connected.
    """
    try:
        bt_command = subprocess.check_output(["bt-device", "--list"], shell=False).decode('utf-8')
    except IOError:
        return
    else:
        paired_devices = re.findall(BT_MAC_REGEX, bt_command)
        devices_names = re.findall(BT_NAME_REGEX, bt_command)
        for each in range(0, len(paired_devices)):
            if paired_devices[each] not in BT_PAIRED_WHITELIST:
                kill_the_system()
            else:
                connected = subprocess.check_output(["bt-device", "-i", paired_devices[each]],
                                                     shell=False).decode('utf-8')
                connected_text = re.findall(BT_CONNECTED_REGEX, connected)
                if connected_text[0].endswith('1') and paired_devices[each] not in BT_CONNECTED_WHITELIST:
                    kill_the_system()
                elif connected_text[0].endswith('1') and each in BT_CONNECTED_WHITELIST:
                    if not devices_names[each] == BT_PAIRED_WHITELIST[each]:
                        kill_the_system()

def detect_usb():
    """detect_usb finds all XXXX:XXX USB IDs connected to the system.
    This can include internal hardware as well.
    """

    ids = re.findall(USB_ID_REGEX, subprocess.check_output("lsusb",
                                                            shell=False).decode('utf-8'))
    for each in ids:
        if each not in USB_ID_WHITELIST:
            kill_the_system()

def detect_ac():
    """detect_ac checks if the system is connected to AC power
    Statuses:
    0 = disconnected
    1 = connected
    """

    with open(AC_FILE, 'r') as ac:
        online = int(ac.readline().strip())
        if online == 0:
            kill_the_system()

def detect_battery():
    """detect_battery checks if there's a battery.
    Obviously this doesn't matter if your system doesn't have a battery.
    Statuses:
    0 = not present
    1 = present
    """
    try:
        with open(BATTERY_FILE, 'r') as battery:
            present = int(battery.readline().strip())
            if present == 0:
                kill_the_system()
    except FileNotFoundError:
        pass

def detect_tray(CDROM_DRIVE):
    """detect_tray reads status of the CDROM_DRIVE.
    Statuses:
    1 = no disk in tray
    2 = tray open
    3 = reading tray
    4 = disk in tray
    """
    fd = os.open(CDROM_DRIVE, os.O_RDONLY | os.O_NONBLOCK)
    rv = fcntl.ioctl(fd, 0x5326)
    os.close(fd)
    if rv != 1:
        kill_the_system()

def kill_the_system():
    """Shut the system down quickly"""
    subprocess.Popen(['/sbin/poweroff', '-f'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="Prints all info once, without worrying about shutdown.",
                        action="store_true")
    args = parser.parse_args()
    if args.debug:
        print('Bluetooth:')
        try:
            print('\n'.join(subprocess.check_output(["bt-device", "--list"]).decode('utf-8').split('\n')[1:]))
        except IOError:
            print('None detected\n')

        print('USB:')
        print(''.join(subprocess.check_output("lsusb", shell=False).decode('utf-8')))

        print('AC:')
        with open('/sys/class/power_supply/AC/online', 'r') as ac:
            print(ac.readline().strip())

        print('Battery:')
        try:
            with open('/sys/class/power_supply/BAT0/present', 'r') as battery:
                print(battery.readline().strip())
        except FileNotFoundError:
            print('None detected\n')

        print('Disk Tray:')
        fd = os.open(CDROM_DRIVE, os.O_RDONLY | os.O_NONBLOCK)
        rv = fcntl.ioctl(fd, 0x5326)
        os.close(fd)
        print(rv)
    else:
        while True:
            detect_bt()
            detect_usb()
            detect_ac()
            detect_battery()
            detect_tray(CDROM_DRIVE)
            time.sleep(REST)
