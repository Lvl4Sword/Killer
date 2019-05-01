import logging
import re
import subprocess

import win32api
import win32file

from killer.killer_base import KillerBase
from killer.windows import power

log = logging.getLogger('Windows')

MAC_ADDRESS_REGEX = re.compile(r'([0-9a-fA-F]{2}(?:-[0-9a-fA-F]{2}){5})')
MEDIA_STATE_REGEX = re.compile(r'Media State ([^:]+): (Media disconnected)')


class KillerWindows(KillerBase):
    def __init__(self, config_path: str = None, debug: bool = False):
        super().__init__(config_path, debug)

    def detect_bt(self):
        raise NotImplementedError

    def detect_usb(self):
        # TODO - Should this return if nothing is in the whitelist?
        # Feels like it should be done elsewhere.
        if not self.config['windows']['usb_id_whitelist']:
            log.warning("No USB devices whitelisted, skipping detection...")
            return

        ids = []

        for each in win32api.GetLogicalDriveStrings().split('\\\x00'):
            if win32file.GetDriveType(each) == win32file.DRIVE_REMOVABLE:
                decimal_id = win32api.GetVolumeInformation(each[1])
                hex_id = '%X' % (0x100000000 + decimal_id)
                ids.append(hex_id)

        log.debug('USB:', ', '.join(ids) if ids else 'none detected')

        for each_device in ids:
            if each_device not in self.config['windows']['usb_id_whitelist']:
                self.kill_the_system('USB Allowed Whitelist: {0}'.format(each_device))
            else:
                if self.config['windows']['usb_id_whitelist'][each_device] != ids.count(each_device):
                    self.kill_the_system('USB Duplicate Device: {0}'.format(each_device))
        for device in self.config['windows']['usb_connected_whitelist']:
            if device not in ids:
                self.kill_the_system('USB Connected Whitelist: {0}'.format(device))
            else:
                if self.config['windows']['usb_connected_whitelist'][each_device] != ids.count(each_device):
                    self.kill_the_system('USB Whitelist Duplicate Device: {0}'.format(each_device))

    def detect_ac(self):
        status = power.get_power_status().ac_line_status
        status = power.ACLineStatus(status)

        log.debug('AC:', status.name)

        if status != power.ACLineStatus.ONLINE:
            # If not connected to power, shutdown
            self.kill_the_system('AC')

    def detect_battery(self):
        status = power.get_power_status().battery_flag
        status = power.BatteryFlags(status)

        log.debug('Battery:', status)

        if status == power.BatteryFlags.NONE:
            self.kill_the_system('Battery')

    def detect_tray(self):
        raise NotImplementedError

    def detect_ethernet(self):
        # TODO: Add enum for:
        #   https://github.com/Lvl4Sword/Killer/wiki/Windows-Connection-Status-Codes
        ipconfig_cmd = subprocess.check_output(['ipconfig', '/all']).decode()
        for each in ipconfig_cmd.split('\r\n\r\n'):
            mac_address = re.findall(MAC_ADDRESS_REGEX, each)
            if mac_address == self.config['windows']['ethernet_interface']:
                log.debug('MAC Address:', mac_address)
                media_state = re.findall(MEDIA_STATE_REGEX, each)
                if media_state:
                    self.kill_the_system('Ethernet')

    def kill_the_system(self, warning: str):
        super().kill_the_system(warning)
        if not self.DEBUG:
            subprocess.Popen(["shutdown.exe", "/s", "/f", "/t", "00"])
