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
import logging
import time

from killer import __version__
from killer.utils import LOGO, WINDOWS, POSIX
from killer.utils.log import configure_logging

log = logging.getLogger('Killer')


def get_killer(args):
    """Returns a KillerBase instance subclassed based on the OS."""
    if POSIX:
        log.debug('Platform: POSIX')
        from killer.killer_posix import KillerPosix
        return KillerPosix(config_path=args.config, debug=args.debug)
    elif WINDOWS:
        log.debug('Platform: Windows')
        from killer.killer_windows import KillerWindows
        return KillerWindows(config_path=args.config, debug=args.debug)
    else:
        # TODO: WSL
        # TODO: OSX
        # TODO: BSD
        raise NotImplementedError("Your platform is not currently supported."
                                  "If you would like support to be added, or "
                                  "if your platform is supported and this is "
                                  "a bug, please open an issue on GitHub!")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="Killer")
    parser.add_argument("--version", action="version",
                        version="%(prog)s {}".format(__version__))
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Prints all info once, without worrying about shutdown.")
    parser.add_argument("-c", "--config", type=str, default=None,
                        help="Path to a configuration file to use")
    parser.add_argument("-lc", "--log-config", type=str, default=None,
                        help="Path to logging configuration file.")
    parser.add_argument("--no-logo", action="store_true",
                        help="Do not display the startup logo")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    if not args.no_logo:
        print(LOGO)

    configure_logging(args.log_config, args.debug)

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
            time.sleep(float(execute.config['global']['examination_interval']))


if __name__ == '__main__':
    main()
