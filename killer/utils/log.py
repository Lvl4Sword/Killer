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

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def configure_logging(debug: bool = False, log_dir: str = None):
    handlers = [logging.StreamHandler(stream=sys.stdout)]

    if log_dir is not None:
        log_dir = Path(log_dir)
        if not log_dir.exists():
            log_dir.mkdir()
        elif log_dir.exists() and not log_dir.is_dir():
            raise NotADirectoryError('The specified log path does not point to a directory.')

        log_dir = Path(log_dir, 'killer.log')
        handlers.append(TimedRotatingFileHandler(log_dir, when='midnight'))

    logging.basicConfig(
        format="%(asctime)s | %(name)-24s | %(levelname)8s | %(message)s",
        level=logging.DEBUG if debug else logging.INFO,
        handlers=handlers
    )
