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

"""
Utility functions for the sysfs power class.
See https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-class-power
"""
from enum import Enum
from typing import Iterator, Union
from pathlib import Path

BASE_PATH = Path('/sys/class/power_supply')


class DeviceType(Enum):
    """Describes the main type of the supply."""
    BATTERY = 'Battery'
    MAINS = 'Mains'
    UPS = 'UPS'
    USB = 'USB'


def get_devices(device_type: DeviceType) -> Iterator[str]:
    """Gets names of power devices of the specified type.

    :param str device_type: the type of the devices to retrieve
    :return: the device names
    :rtype: Iterator[str]
    """
    for device in BASE_PATH.iterdir():
        with open(str(Path(device, 'type'))) as type_file:
            if type_file.readline().strip() == device_type.value:
                yield device.name


def is_present(device_path: Union[Path, str]) -> bool:
    """Reports whether a battery is present or not in the system.

    :param str device_path: the path to the battery device
    :return: True if present or False if absent
    :rtype: bool
    """
    return bool(_get_property(device_path, 'present'))


def is_online(device_path: Union[Path, str]) -> bool:
    """Indicates if a mains cable is plugged into the system.

    :param str device_path: the path to the mains device
    :return: True if plugged in or False if disconnected
    :rtype: bool
    """
    return bool(_get_property(device_path, 'online'))


def _get_property(device_path: Union[Path, str], property_name: str) -> str:
    """Gets the given property for a device."""
    with open(str(Path(device_path, property_name))) as file:
        return file.readline().strip()
