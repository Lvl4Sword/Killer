import json
import logging
import os
import re
import subprocess

import fcntl

from killer.killer_base import KillerBase
from killer.posix import power

BT_MAC_REGEX = re.compile(r"(?:[0-9a-fA-F]:?){12}")
BT_NAME_REGEX = re.compile(r"[0-9A-Za-z ]+(?=\s\()")
BT_CONNECTED_REGEX = re.compile(r"(Connected: [0-1])")
USB_ID_REGEX = re.compile(r"([0-9a-fA-F]{4}:[0-9a-fA-F]{4})")

log = logging.getLogger('POSIX')


class KillerPosix(KillerBase):
    def __init__(self, config_path: str = None, debug: bool = False):
        super().__init__(config_path, debug)

    def detect_bt(self):
        bt_config = self.config['bluetooth']
        try:
            bt_command = subprocess.check_output(["bt-device", "--list"],
                                                 shell=False).decode()
        except Exception as e:
            log.debug('Bluetooth: none detected (exception: {0})'.format(e))
        else:
            if self.DEBUG:
                # TODO: Clean up
                bt_devices = bt_command.split('\n')
                if len(bt_devices) == 3 and bt_devices[2] == '':
                    log.debug('Bluetooth:', bt_command.split('\n')[1])
                else:
                    log.debug('Bluetooth:', ', '.join(bt_command.split('\n')[1:]))
            else:
                paired_devices = re.findall(BT_MAC_REGEX, bt_command)
                devices_names = re.findall(BT_NAME_REGEX, bt_command)
                for each in range(0, len(paired_devices)):
                    if paired_devices[each] not in bt_config['paired_whitelist']:
                        self.kill_the_system('Bluetooth Paired: {0}'.format(paired_devices[each]))
                    else:
                        connected = subprocess.check_output(
                            ["bt-device", "-i",
                             paired_devices[each]],
                            shell=False).decode()
                        connected_text = re.findall(BT_CONNECTED_REGEX, connected)
                        if connected_text[0].endswith("1") \
                                and paired_devices[each] not in bt_config['connected_whitelist']:
                            self.kill_the_system('Bluetooth Connected MAC Disallowed: {0}'.format(paired_devices[each]))
                        elif connected_text[0].endswith("1") and each in bt_config['connected_whitelist']:
                            if devices_names[each] != bt_config['paired_whitelist'][each]:
                                self.kill_the_system('Bluetooth Connected Name Mismatch: {0}'.format(devices_names[each]))

    def detect_usb(self):
        ids = re.findall(USB_ID_REGEX, subprocess.check_output("lsusb", shell=False).decode())
        log.debug('USB:', ', '.join(ids) if ids else 'none detected')

        for each_device in ids:
            if each_device not in self.config['linux']['usb_id_whitelist']:
                 self.kill_the_system('USB Allowed Whitelist: {0}'.format(each_device))
            else:
                if self.config['linux']['usb_id_whitelist'][each_device] != ids.count(each_device):
                    self.kill_the_system('USB Duplicate Device: {0}'.format(each_device))

        for device in self.config['linux']['usb_connected_whitelist']:
            if device not in ids:
                self.kill_the_system('USB Connected Whitelist: {0}'.format(device))

    def detect_ac(self):
        if self.DEBUG:
            devices = ', '.join(power.get_devices(power.DeviceType.MAINS))
            log.debug('AC:', devices if devices else 'none detected')

        if not power.is_online(self.config['linux']['ac_file']):
            self.kill_the_system('AC')

    def detect_battery(self):
        if self.DEBUG:
            devices = ', '.join(power.get_devices(power.DeviceType.BATTERY))
            log.debug('Battery:', devices if devices else 'none detected')

        try:
            if not power.is_present(self.config['linux']['battery_file']):
                self.kill_the_system('Battery')
        except FileNotFoundError:
            pass

    def detect_tray(self):
        disk_tray = self.config['linux']['cdrom_drive']
        fd = os.open(disk_tray, os.O_RDONLY | os.O_NONBLOCK)
        rv = fcntl.ioctl(fd, 0x5326)
        os.close(fd)

        log.debug('CD Tray:', rv)

        if rv != 1:
            self.kill_the_system('CD Tray')

    def detect_ethernet(self):
        with open(self.config['linux']['ethernet_connected_file']) as ethernet:
            connected = int(ethernet.readline().strip())

        log.debug('Ethernet:', connected)

        if connected:
            self.kill_the_system('Ethernet')

    def kill_the_system(self, warning: str):
        super().kill_the_system(warning)
        if not self.DEBUG:
            subprocess.Popen(["/sbin/poweroff", "-f"])
