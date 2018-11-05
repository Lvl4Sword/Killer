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

from typing import Iterator
from pathlib import Path


def get_devices(device_type: str) -> Iterator[str]:
    """Gets names of power devices of the specified type.

    :param str device_type: the type of the devices to retrieve
    :return: the device names
    :rtype: Iterator[str]
    """
    for device in Path('/sys/class/power_supply').iterdir():
        with open(Path(device, 'type')) as type_file:
            if type_file.readline().strip() == device_type:
                yield device.name
