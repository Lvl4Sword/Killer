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

import ctypes
import sys
from ctypes import wintypes

try:
    from enum import Enum, Flag
except ImportError:
    print("Killer requires Python 3.6+ on Windows")
    sys.exit(1)


class ACLineStatus(Enum):
    OFFLINE = 0
    ONLINE = 1
    UNKNOWN = 255


class BatteryFlags(Flag):
    HIGH = 1
    LOW = 2
    CRITICAL = 4
    CHARGING = 8
    NONE = 128
    UNKNOWN = 255


class SystemPowerStatus(ctypes.Structure):
    """Contains information about the power status of the system."""
    _fields_ = [
        ('ac_line_status', ctypes.c_ubyte),
        ('battery_flag', ctypes.c_ubyte),
        ('battery_life_percent', ctypes.c_ubyte),
        ('system_status_flag', ctypes.c_ubyte),
        ('battery_life_time', wintypes.DWORD),
        ('battery_full_life_time', wintypes.DWORD)
    ]


def get_power_status() -> SystemPowerStatus:
    """Retrieves the power status of the system.

    The status indicates whether the system is running on AC or DC power,
    whether the battery is currently charging, how much battery life remains,
    and if battery saver is on or off.

    :raises OSError: if the call to GetSystemPowerStatus fails
    :return: the power status
    :rtype: SystemPowerStatus
    """
    get_system_power_status = ctypes.windll.kernel32.GetSystemPowerStatus
    get_system_power_status.argtypes = [ctypes.POINTER(SystemPowerStatus)]
    get_system_power_status.restype = wintypes.BOOL
    status = SystemPowerStatus()

    if not get_system_power_status(ctypes.pointer(status)):
        raise ctypes.WinError()
    else:
        return status
