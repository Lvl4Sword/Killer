import ctypes
import subprocess
from ctypes import wintypes

import wmi

from killer.killer_base import KillerBase


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
        raise NotImplementedError

    def detect_battery(self):
        raise NotImplementedError

    def detect_tray(self):
        raise NotImplementedError

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
