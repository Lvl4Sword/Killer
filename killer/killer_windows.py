import logging
import subprocess

import win32file
import win32api
import wmi

from killer.killer_base import KillerBase
from killer.windows import power

log = logging.getLogger('Windows')


class KillerWindows(KillerBase):
    def __init__(self, config_path: str = None, debug: bool = False):
        super().__init__(config_path, debug)

    def detect_bt(self):
        raise NotImplementedError

    def detect_usb(self):
        if not self.config['windows']['usb_id_whitelist']:
            log.warning("No USB devices whitelisted, skipping detection...")
            return

        ids = []

        for each in win32api.GetLogicalDriveStrings().split('\\\x00'):
            if win32file.GetDriveType(each) == win32file.DRIVE_REMOVABLE:
                decimal_id = int(win32api.GetVolumeInformation(each[1])
                hex_id = '%X' % (0x100000000 + decimal_id)
                ids.append(hex_id)

        log.debug('USB: %s', ', '.join(ids) if ids else 'none detected')

        for each_device in ids:
            if each_device not in self.config['windows']['usb_id_whitelist']:
                self.kill_the_system('USB Allowed Whitelist')
        for device in self.config['windows']['usb_connected_whitelist']:
            if device not in ids:
                self.kill_the_system('USB Connected Whitelist')

    def detect_ac(self):
        status = power.get_power_status().ac_line_status
        status = power.ACLineStatus(status)

        log.debug('AC: %s', status.name)

        if status != power.ACLineStatus.ONLINE:
            # If not connected to power, shutdown
            self.kill_the_system('AC')

    def detect_battery(self):
        status = power.get_power_status().battery_flag
        status = power.BatteryFlags(status)

        log.debug('Battery: %s', status)

        if status == power.BatteryFlags.NONE:
            self.kill_the_system('Battery')

    def detect_tray(self):
        raise NotImplementedError

    def detect_ethernet(self):
        # TODO: Add enum for:
        #   https://github.com/Lvl4Sword/Killer/wiki/Windows-Connection-Status-Codes
        for x in wmi.WMI().Win32_NetworkAdapter():
            if x.NetConnectionStatus is not None:
                # This can contain quite a few things including Ethernet, Bluetooth, and Wireless
                log.debug('%s %d %s', x.MacAddress, x.NetConnectionStatus, x.Name)

                if x.MacAddress == self.config['windows']['ethernet_interface']:
                    if x.NetConnectionStatus == 7:
                        self.kill_the_system('Ethernet')

    def kill_the_system(self, warning: str):
        super().kill_the_system(warning)
        if not self.DEBUG:
            subprocess.Popen(["shutdown.exe", "/s", "/f", "/t", "00"])
