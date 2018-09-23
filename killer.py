#!/usr/bin/env python3
__version__ = '0.1.1'
__author__ = 'Lvl4Sword'

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
bt_connected_regex = ('(Connected: [0-1])')
usb_id_regex = '([0-9a-fA-F]{4}:[0-9a-fA-F]{4})'
###

### Bluetooth
# Find the paired devices with bt-device --list
bt_paired_whitelist = ['DE:AD:BE:EF:CA:FE']
bt_connected_whitelist = ['DE:AD:BE:EF:CA:FE']
###

### USB
# Find the current devices by running lsusb
usb_id_whitelist = ['DE:AD:BE:EF:CA:FE']
###

rest = 2

def detect_bt():
    paired_devices = re.findall(bt_mac_regex, subprocess.check_output(["bt-device", "--list"],
                                                                        shell=False).decode('utf-8'))
    for each in paired_devices:
        if each not in bt_paired_whitelist:
            subprocess.Popen(['/sbin/shutdown', '-h', 'now'])
        else:
            connected = subprocess.check_output(["bt-device", "-i", each],
                                                 shell=False).decode('utf-8')
            connected_text = re.findall(bt_connected_regex, connected)
            if connected_text[0].endswith('1') and each not in bt_connected_whitelist:
                kill_the_system()

def detect_usb():
    ids = re.findall(usb_id_regex, subprocess.check_output("lsusb",
                                                            shell=False).decode('utf-8'))
    for each in ids:
        if each not in usb_id_whitelist:
            kill_the_system()

def detect_ac():
    with open('/sys/class/power_supply/AC/online', 'r') as ac:
        online = ac.readline().strip()
        if online == '0':
            kill_the_system()

def detect_battery():
    with open('/sys/class/power_supply/BAT0/present', 'r') as battery:
        present = battery.readline().strip()
        if present == '0':
            kill_the_system()

def kill_the_system():
    subprocess.Popen(['/sbin/poweroff', '-f'])

if __name__ == '__main__':
    while True:
        detect_bt()
        detect_usb()
        detect_ac()
        detect_battery()
        time.sleep(rest)
