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

import platform
import sys

# Determine what platform we're running
WINDOWS = sys.platform.startswith('win32')
LINUX = sys.platform.startswith('linux')
OSX = sys.platform.startswith('darwin')
BSD = OSX or 'bsd' in sys.platform
POSIX = LINUX or BSD

# Detect if we're running in Windows Subsystem for Linux (WSL)
WSL = not WINDOWS and 'Microsoft' in platform.version()

LOGO = """
        _  _  _  _ _
       | |/ /(_)| | |
       |   /  _ | | | ____ _ _
       |  \\  | || | |/ _  ) `_|
       | | \\ | || | ( (/_/| |
       |_|\\_\\|_|\\__)_)____)_|
_____________________________________
\\                       | _   _   _  \\
 `.                  ___|____________/
   ``````````````````
"""

__all__ = ['WINDOWS', 'LINUX', 'OSX', 'BSD', 'POSIX', 'WSL', 'LOGO']
