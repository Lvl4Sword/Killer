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

import json
import logging
import logging.config
from typing import Optional

# TODO: Replace KillerBase.mail_this() with an SMTPHandler here.
DEFAULT_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'basic': {
            'format': '%(asctime)s | %(name)-10s | %(levelname)-8s | %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'basic',
            'stream': 'ext://sys.stdout',
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
        }
    }
}

log = logging.getLogger('Log')


def configure_logging(config_path: Optional[str], debug: bool = False):
    if config_path:
        try:
            with open(config_path) as file:
                config = json.load(file)
                logging.config.dictConfig(config)
        except Exception:
            log.exception('Error loading logging config file %s. Logging will '
                          'be configured with defaults.', config_path)
    load_default(debug)


def load_default(debug: bool = False):
    if debug:
        DEFAULT_CONFIG['loggers']['']['level'] = 'DEBUG'
    logging.config.dictConfig(DEFAULT_CONFIG)
