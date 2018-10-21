#!/usr/bin/env python3
"""If there are any unrecognized bluetooth or USB devices,
laptop power is unplugged, laptop battery is removed while on AC,
or the disk tray is tampered with, shut the computer down!
"""
#         _  _  _  _ _
#        | |/ /(_)| | |
#        |   /  _ | | | ____ _ _
#        |  \  | || | |/ _  ) `_|
#        | | \ | || | ( (/_/| |
#        |_|\_\|_|\__)_)____)_|
# _____________________________________
# \                       | _   _   _  \
#  `.                  ___|____________/
#    ``````````````````


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

import argparse
import time

from . import WINDOWS, LINUX, OSX, BSD, POSIX, WSL


def get_killer(args):
    """Returns a KillerBase instance subclassed based on the OS."""
    if POSIX:
        from killer.killer_posix import KillerPosix
        return KillerPosix(config_path=args.config, debug=args.debug)
    elif WINDOWS:
        from killer.killer_windows import KillerWindows
        return KillerWindows(config_path=args.config, debug=args.debug)
    else:
        raise NotImplementedError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Prints all info once, without worrying about shutdown.")
    parser.add_argument("-c", "--config", type=str, default=None,
                        help="Path to a configuration file to use")
    args = parser.parse_args()
    execute = get_killer(args)
    while True:
        if POSIX:
            execute.detect_bt()
            execute.detect_tray()
        execute.detect_ac()
        execute.detect_battery()
        execute.detect_usb()
        execute.detect_ethernet()
        if execute.DEBUG:
            break
        else:
            time.sleep(execute.config.getint('global', 'REST'))


if __name__ == '__main__':
    main()
