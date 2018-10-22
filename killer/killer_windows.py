import subprocess

import wmi

from .killer_base import KillerBase
from .windows import power


class KillerWindows(KillerBase):
    def __init__(self, config_path: str = None, debug: bool = False):
        super().__init__(config_path, debug)

    def detect_bt(self):
        raise NotImplementedError

    def detect_usb(self):
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
        status = power.get_power_status().ac_line_status
        status = power.ACLineStatus(status)

        if self.DEBUG:
            print("AC:")
            print(status.name)
            print()
        elif status != power.ACLineStatus.ONLINE:
            # If not connected to power, shutdown
            self.kill_the_system('AC')

    def detect_battery(self):
        status = power.get_power_status().battery_flag
        status = power.BatteryFlags(status)

        if self.DEBUG:
            print("Battery:")
            print(status)
            print()
        elif status == power.BatteryFlags.NONE:
            self.kill_the_system('Battery')

    def detect_tray(self):
        raise NotImplementedError

    def detect_ethernet(self):
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
        super().kill_the_system(warning)
        subprocess.Popen(["shutdown.exe", "/s", "/f", "/t", "00"])
