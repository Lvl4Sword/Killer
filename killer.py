#!/usr/bin/env python3
__version__ = '0.1.4-1'
__author__ = 'Lvl4Sword'

import argparse
import re
import subprocess
import time

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

### Regular expressions
bt_mac_regex = re.compile('(?:[0-9a-fA-F]:?){12}')
bt_name_regex = re.compile('[0-9A-Za-z ]+(?=\s\()')
bt_connected_regex = ('(Connected: [0-1])')
usb_id_regex = '([0-9a-fA-F]{4}:[0-9a-fA-F]{4})'

### Bluetooth
bt_paired_whitelist = {'DE:AF:BE:EF:CA:FE': 'Generic Bluetooth Device'}
bt_connected_whitelist = ['DE:AF:BE:EF:CA:FE']

### USB
usb_id_whitelist = ['DE:AF:BE:EF:CA:FE']

### CD/DVD Tray
cdrom_drive = '/dev/sr0'

rest = 2

def detect_bt():
    bt_command = subprocess.check_output(["bt-device", "--list"], shell=False).decode('utf-8')
    paired_devices = re.findall(bt_mac_regex, bt_command)
    devices_names = re.findall(bt_name_regex, bt_command)
    for each in range(0, len(paired_devices)):
        if paired_devices[each] not in bt_paired_whitelist:
            kill_the_system()
        else:
            connected = subprocess.check_output(["bt-device", "-i", paired_devices[each]],
                                                 shell=False).decode('utf-8')
            connected_text = re.findall(bt_connected_regex, connected)
            if connected_text[0].endswith('1') and paired_devices[each] not in bt_connected_whitelist:
                kill_the_system()
            elif connected_text[0].endswith('1') and each in bt_connected_whitelist:
                if not devices_names[each] == bt_paired_whitelist[each]:
                    kill_the_system()

def detect_usb():
    ids = re.findall(usb_id_regex, subprocess.check_output("lsusb",
                                                            shell=False).decode('utf-8'))
    for each in ids:
        if each not in usb_id_whitelist:
            kill_the_system()

# 0 = disconnected
# 1 = connected
def detect_ac():
    with open('/sys/class/power_supply/AC/online', 'r') as ac:
        online = ac.readline().strip()
        if online == '0':
            kill_the_system()

# 0 = not present
# 1 = present
def detect_battery():
    with open('/sys/class/power_supply/BAT0/present', 'r') as battery:
        present = battery.readline().strip()
        if present == '0':
            kill_the_system()

# 1 = no disk in tray
# 2 = tray open
# 3 = reading tray
# 4 = disk in tray
def detect_tray(cdrom_drive):
    fd = os.open(cdrom_drive, os.O_RDONLY | os.O_NONBLOCK)
    rv = fcntl.ioctl(fd, 0x5326)
    os.close(fd)
    if rv != 1:
        kill_the_system()

def kill_the_system():
    subprocess.Popen(['/sbin/poweroff', '-f'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="Prints all USB and Bluetooth devices",
                        action="store_true")
    args = parser.parse_args()
    if args.debug:
        print('Bluetooth:')
        print('\n'.join(subprocess.check_output(["bt-device", "--list"]).decode('utf-8').split('\n')[1:]))
        print('USB:')
        print(''.join(subprocess.check_output("lsusb", shell=False).decode('utf-8')))
        print('AC:')
        with open('/sys/class/power_supply/AC/online', 'r') as battery:
            print(battery.readline().strip())
        print('Battery:')
        with open('/sys/class/power_supply/BAT0/present', 'r') as battery:
            print(battery.readline().strip())
        print('Disk Tray:')
        fd = os.open(cdrom_drive, os.O_RDONLY | os.O_NONBLOCK)
        rv = fcntl.ioctl(fd, 0x5326)
        os.close(fd)
        print(rv)
    else:
        while True:
            detect_bt()
            detect_usb()
            detect_ac()
            detect_battery()
            detect_tray(cdrom_drive)
            time.sleep(rest)
