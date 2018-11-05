import json
import logging
import os
import re
import subprocess

import fcntl

from killer.killer_base import KillerBase

BT_MAC_REGEX = re.compile("(?:[0-9a-fA-F]:?){12}")
BT_NAME_REGEX = re.compile("[0-9A-Za-z ]+(?=\s\()")
BT_CONNECTED_REGEX = re.compile("(Connected: [0-1])")
USB_ID_REGEX = re.compile("([0-9a-fA-F]{4}:[0-9a-fA-F]{4})")

log = logging.getLogger(__name__)


class KillerPosix(KillerBase):
    def __init__(self, config_path: str = None, debug: bool = False):
        super().__init__(config_path, debug)

    def detect_bt(self):
        try:
            bt_command = subprocess.check_output(["bt-device", "--list"],
                                                 shell=False).decode()
        except IOError:
            log.debug('Bluetooth: none detected')
        else:
            if self.DEBUG:
                # TODO: Clean up
                bt_devices = bt_command.split('\n')
                if len(bt_devices) == 3 and bt_devices[2] == '':
                    log.debug('Bluetooth: %s', bt_command.split('\n')[1])
                else:
                    log.debug('Bluetooth: %s', ', '.join(bt_command.split('\n')[1:]))
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
        ids = re.findall(USB_ID_REGEX, subprocess.check_output("lsusb",
                                                                shell=False).decode())
        log.debug('USB: %s', ', '.join(ids))

        for each_device in ids:
            if each_device not in json.loads(self.config['linux']['USB_ID_WHITELIST']):
                self.kill_the_system('USB Allowed Whitelist')
        for device in json.loads(self.config['linux']['USB_CONNECTED_WHITELIST']):
            if device not in ids:
                self.kill_the_system('USB Connected Whitelist')

    def detect_ac(self):
        if self.DEBUG:
            ac_types = []
            for each in os.listdir("/sys/class/power_supply"):
                with open("/sys/class/power_supply/{0}/type".format(each)) as power_file:
                    the_type = power_file.readline().strip()
                    if the_type == "Mains":
                        ac_types.append(each)

            log.debug('AC: %s', ', '.join(ac_types) if ac_types else 'none detected')
        else:
            with open(self.config['linux']['AC_FILE']) as ac:
                online = int(ac.readline().strip())
                if not online:
                    self.kill_the_system('AC')

    def detect_battery(self):
        if self.DEBUG:
            battery_types = []
            for each in os.listdir("/sys/class/power_supply"):
                with open("/sys/class/power_supply/{0}/type".format(each)) as power_file:
                    the_type = power_file.readline().strip()
                    if the_type == "Battery":
                        battery_types.append(each)

            log.debug('Battery: %s', ', '.join(battery_types) if battery_types else 'none detected')
        else:
            try:
                with open(self.config['linux']['BATTERY_FILE']) as battery:
                    present = int(battery.readline().strip())
                    if not present:
                        self.kill_the_system('Battery')
            except FileNotFoundError:
                pass

    def detect_tray(self):
        disk_tray = self.config['linux']['CDROM_DRIVE']
        fd = os.open(disk_tray, os.O_RDONLY | os.O_NONBLOCK)
        rv = fcntl.ioctl(fd, 0x5326)
        os.close(fd)

        log.debug('CD Tray: %d', rv)

        if rv != 1:
            self.kill_the_system('CD Tray')

    def detect_ethernet(self):
        with open(self.config['linux']['ETHERNET_CONNECTED']) as ethernet:
            connected = int(ethernet.readline().strip())

        log.debug('Ethernet: %d', connected)

        if connected:
            self.kill_the_system('Ethernet')

    def kill_the_system(self, warning: str):
        super().kill_the_system(warning)
        if not self.DEBUG:
            subprocess.Popen(["/sbin/poweroff", "-f"])
