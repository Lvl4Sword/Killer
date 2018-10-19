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

import argparse
import configparser
import json
import os
import platform
import re
import smtplib
import socket
import ssl
import subprocess
import sys
import time
from email.mime.text import MIMEText
from pathlib import Path
from ssl import Purpose

__version__ = "0.6.1"
__author__ = "Lvl4Sword"

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

socket.setdefaulttimeout(3)

BT_MAC_REGEX = re.compile("(?:[0-9a-fA-F]:?){12}")
BT_NAME_REGEX = re.compile("[0-9A-Za-z ]+(?=\s\()")
BT_CONNECTED_REGEX = re.compile("(Connected: [0-1])")
USB_ID_REGEX = re.compile("([0-9a-fA-F]{4}:[0-9a-fA-F]{4})")


class Killer:
    def __init__(self, config_path: str = None, debug: bool = False):
        self.DEBUG = debug
        if config_path is None:
            to_search = [Path.cwd(),
                         Path(__file__).parent,
                         Path.home()]
            for path in to_search:
                if self.DEBUG:
                    print("Searching for 'killer.conf' in: %s" % str(path))
                file = path / 'killer.conf'
                if file.exists():
                    config_path = file
                    break
            if config_path is None:
                print("ERROR: Failed to find configuration file 'killer.conf'"
                      "\nPaths searched:\n%s" % ''.join(['  %s\n' % str(x)
                                                         for x in to_search]))
                sys.exit(1)
        self.config_file = Path(config_path).resolve()
        if not self.config_file.exists():
            print("Could not find configuration file %s" % str(self.config_file))
            sys.exit(1)
        self.config = configparser.ConfigParser()
        self.config.read(str(self.config_file))  # Python 3.5 requires str() conversion

    def detect_bt(self):
        """detect_bt looks for paired MAC addresses,
        names for paired devices, and connected status for devices.
        Two whitelists, one for paired, one for connected.
        """
        if POSIX:
            try:
                bt_command = subprocess.check_output(["bt-device", "--list"],
                                                      shell=False).decode()
            except IOError:
                if self.DEBUG:
                    print("None detected\n")
                else:
                    return
            else:
                if self.DEBUG:
                    print("Bluetooth:")
                    bt_devices = bt_command.split('\n')
                    if len(bt_devices) == 3 and bt_devices[2] == '':
                        print(bt_command.split('\n')[1])
                    else:
                        print(', '.join(bt_command.split('\n')[1:]))
                    print()
                else:
                    paired_devices = re.findall(BT_MAC_REGEX, bt_command)
                    devices_names = re.findall(BT_NAME_REGEX, bt_command)
                    for each in range(0, len(paired_devices)):
                        if paired_devices[each] not in json.loads(self.config['linux']['BT_PAIRED_WHITELIST']):
                            self.kill_the_system('Bluetooth Paired')
                        else:
                            connected = subprocess.check_output(["bt-device", "-i",
                                                                 paired_devices[each]],
                                                                 shell=False).decode()
                            connected_text = re.findall(BT_CONNECTED_REGEX, connected)
                            if connected_text[0].endswith("1") and paired_devices[each] not in json.loads(self.config['linux']['BT_CONNECTED_WHITELIST']):
                                self.kill_the_system('Bluetooth Connected MAC Disallowed')
                            elif connected_text[0].endswith("1") and each in json.loads(self.config['linux']['BT_CONNECTED_WHITELIST']):
                                if not devices_names[each] == json.loads(self.config['linux']['BT_PAIRED_WHITELIST'])[each]:
                                    self.kill_the_system('Bluetooth Connected Name Mismatch')

    def detect_usb(self):
        """detect_usb finds all USB IDs/VolumeSerialNumbers connected to the system.
        For linux, this includes internal hardware as well.
        """
        if POSIX:
            ids = re.findall(USB_ID_REGEX, subprocess.check_output("lsusb",
                                                                    shell=False).decode())
            if self.DEBUG:
                print("USB:")
                print(', '.join(ids))
                print()
            else:
                for each_device in ids:
                    if each_device not in json.loads(self.config['linux']['USB_ID_WHITELIST']):
                        self.kill_the_system('USB Allowed Whitelist')
                for device in json.loads(self.config['linux']['USB_CONNECTED_WHITELIST']):
                    if device not in ids:
                        self.kill_the_system('USB Connected Whitelist')
        elif WINDOWS:
            ids = []
            for each in wmi.WMI().Win32_LogicalDisk():
                if each.Description == 'Removable Disk':
                    ids.append(each.VolumeSerialNumber)
            if self.DEBUG:
                print("USB:")
                print(', '.join(ids))
                print()
            else:
                for each_device in ids:
                    if each_device not in self.config['windows']['USB_ID_WHITELIST']:
                        self.kill_the_system('USB Allowed Whitelist')
                for device in self.config['windows']['USB_CONNECTED_WHITELIST']:
                    if device not in ids:
                        self.kill_the_system('USB Connected Whitelist')

    def detect_ac(self):
        """detect_ac checks if the system is connected to AC power
        Statuses:
        0 = disconnected
        1 = connected
        """
        if POSIX:
            if self.DEBUG:
                ac_types = []
                for each in os.listdir("/sys/class/power_supply"):
                    with open("/sys/class/power_supply/{0}/type".format(each)) as power_file:
                        the_type = power_file.readline().strip()
                        if the_type == "Mains":
                            ac_types.append(each)
                print("AC:")
                if ac_types:
                    if len(ac_types) >= 2:
                        print(', '.join(ac_types))
                    elif len(ac_types) == 1:
                        print(ac_types[0])
                    print()
                else:
                    print("None detected\n")
            else:
                with open(self.config['linux']['AC_FILE']) as ac:
                    online = int(ac.readline().strip())
                    if not online:
                        self.kill_the_system('AC')

    def detect_battery(self):
        """detect_battery checks if there is a battery.
        Obviously this is useless if your system does not have a battery.
        Statuses:
        0 = not present
        1 = present
        """
        if POSIX:
            if self.DEBUG:
                battery_types = []
                for each in os.listdir("/sys/class/power_supply"):
                    with open("/sys/class/power_supply/{0}/type".format(each)) as power_file:
                        the_type = power_file.readline().strip()
                        if the_type == "Battery":
                            battery_types.append(each)
                print("Battery:")
                if battery_types:
                    if len(battery_types) >= 2:
                        print(', '.join(battery_types))
                    elif len(battery_types) == 1:
                        print(battery_types[0])
                    print()
                else:
                    print("None detected\n")
            else:
                try:
                    with open(self.config['linux']['BATTERY_FILE']) as battery:
                        present = int(battery.readline().strip())
                        if not present:
                            self.kill_the_system('Battery')
                except FileNotFoundError:
                    pass

    def detect_tray(self):
        """detect_tray reads status of the CDROM_DRIVE.
        Statuses:
        1 = no disk in tray
        2 = tray open
        3 = reading tray
        4 = disk in tray
        """
        if POSIX:
            disk_tray = self.config['linux']['CDROM_DRIVE']
            fd = os.open(disk_tray, os.O_RDONLY | os.O_NONBLOCK)
            rv = fcntl.ioctl(fd, 0x5326)
            os.close(fd)
            if self.DEBUG:
                print('CD Tray:')
                print(rv)
                print()
            else:
                if rv != 1:
                    self.kill_the_system('CD Tray')

    def detect_power(self):
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
            if self.DEBUG:
                print('Power:')
                print('ACLineStatus', status.ACLineStatus)
                print('BatteryFlag', status.BatteryFlag)
                print()
            else:
                if ('ACLineStatus', status.ACLineStatus) != 1:
                    # If not connected to power, shutdown
                    self.kill_the_system('AC')
                elif ('BatteryFlag', status.BatteryFlag) not in [0, 1, 2, 4, 8, 9, 10, 12]:
                    if ('BatteryFlag', status.BatteryFlag) == 128:
                        # Battery not detected, so this is useless
                        pass
                    else:
                        # Battery is not connected, shut down
                        self.kill_the_system('Battery')

    def detect_ethernet(self):
        """Check if an ethernet cord is connected.
        Status:
        0 = False
        1 = True
        """
        if POSIX:
            with open(self.config['linux']['ETHERNET_CONNECTED']) as ethernet:
                connected = int(ethernet.readline().strip())
            if self.DEBUG:
                print("Ethernet:")
                print(connected)
            else:
                if connected:
                    self.kill_the_system('Ethernet')
        elif WINDOWS:
            for x in wmi.WMI().Win32_NetworkAdapter():
                if x.NetConnectionStatus is not None:
                    if self.DEBUG:
                        # This can contain quite a few things
                        # Including Ethernet, Bluetooth, and Wireless
                        print(x.Name)
                        print(x.NetConnectionStatus)
                        print(x.MacAddress)
                    else:
                        if x.MacAddress == self.config['windows']['ETHERNET_INTERFACE']:
                            # This should probably be clearer, but for the time being:
                            # https://github.com/Lvl4Sword/Killer/wiki/Windows-Connection-Status-Codes
                            if x.NetConnectionStatus == 7:
                                self.kill_the_system('Ethernet')

    def kill_the_system(self, warning: str):
        """Send an e-mail, and then
        shut the system down quickly.
        """
        try:
            self.mail_this(warning)
        except socket.gaierror:
            current_time = time.localtime()
            formatted_time = time.strftime('%Y-%m-%d %I:%M:%S%p', current_time)
            with open(self.config['global']['KILLER_FILE'], 'a') as killer_file:
                killer_file.write('Time: {0}\nInternet is out.\nFailure: {1}\n\n'.format(formatted_time, warning))
        if WINDOWS:
            subprocess.Popen(["shutdown.exe", "/s", "/f", "/t", "00"])
        else:
            subprocess.Popen(["/sbin/poweroff", "-f"])

    def mail_this(self, warning: str):
        subject = '[ALERT: {0}]'.format(warning)
        # typical values for text_subtype are plain, html, xml
        text_subtype = 'plain'

        current_time = time.localtime()
        formatted_time = time.strftime('%Y-%m-%d %I:%M:%S%p', current_time)

        content = 'Time: {0}\nWarning: {1}'.format(formatted_time, warning)
        msg = MIMEText(content, _charset='utf-8')
        msg['Subject'] = subject
        msg['From'] = self.config["email"]["SENDER"]
        ssl_context = ssl.create_default_context(purpose=Purpose.SERVER_AUTH)
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.check_hostname = True
        ssl_context.set_ciphers(self.config["email"]["CIPHER_CHOICE"])
        ssl_context.options &= ~ssl.HAS_SNI
        ssl_context.options &= ~ssl.OP_NO_COMPRESSION
        # No need to explicitly disable SSLv* as it's already been done
        # https://docs.python.org/3/library/ssl.html#id7
        ssl_context.options &= ~ssl.OP_NO_TLSv1
        ssl_context.options &= ~ssl.OP_NO_TLSv1_1
        ssl_context.options &= ~ssl.OP_SINGLE_DH_USE
        ssl_context.options &= ~ssl.OP_SINGLE_ECDH_USE
        conn = smtplib.SMTP_SSL(self.config["email"]["SMTP_SERVER"],
                                port=self.config["email"]["SMTP_PORT"],
                                context=ssl_context)
        conn.esmtp_features['auth'] = self.config["email"]["LOGIN_AUTH"]
        conn.login(self.config["email"]["SENDER"], self.config["email"]["SENDER_PASSWORD"])
        try:
            for each in json.loads(self.config["email"]["DESTINATION"]):
                conn.sendmail(self.config["email"]["SENDER"], each, msg.as_string())
        except socket.timeout:
            raise socket.gaierror
        finally:
            conn.quit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Prints all info once, without worrying about shutdown.")
    parser.add_argument("-c", "--config", type=str, default=None,
                        help="Path to a configuration file to use")
    args = parser.parse_args()
    execute = Killer(config_path=args.config, debug=args.debug)
    while True:
        if WINDOWS:
            execute.detect_power()
        elif POSIX:
            execute.detect_bt()
            execute.detect_ac()
            execute.detect_battery()
            execute.detect_tray()
        execute.detect_usb()
        execute.detect_ethernet()
        if execute.DEBUG:
            break
        else:
            time.sleep(execute.config.getint('global', 'REST'))


if __name__ == '__main__':
    main()
