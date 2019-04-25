import json
import logging
import smtplib
import socket
import ssl
import sys
import time
import pkgutil
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from pathlib import Path

log = logging.getLogger('Base')


class KillerBase(ABC):
    CONFIG_SEARCH_PATHS = [Path.cwd(), Path.home()]
    CONFIG_FILENAME = "killer_config.json"

    def __init__(self, config_path: str = None, debug: bool = False):
        socket.setdefaulttimeout(3)
        self.DEBUG = debug
        self._load_config(config_path)

    def _load_config(self, config_path: str = None):
        if config_path is None:
            config_file = None
            for path in self.CONFIG_SEARCH_PATHS:
                log.debug("Searching for '%s' in: %s", self.CONFIG_FILENAME, str(path))
                file = path / self.CONFIG_FILENAME
                if file.exists():
                    config_file = file
                    break
        else:
            config_file = Path(config_path)
            if not config_file.exists():
                log.critical("Configuration file '%s' does not exist", str(config_file))
                sys.exit(1)

        if config_file is None:
            log.warning("Didn't find a user-specified configuration, loading the default...")
            data = pkgutil.get_data('killer', 'killer_config.json')
        else:
            data = config_file.read_text(encoding='utf-8')
        try:
            self.config = json.loads(data)
        except json.JSONDecodeError as ex:
            log.critical("Failed to parse configuration: %s", str(ex))
            sys.exit(1)
        except TypeError:
            self.config = json.loads(data.decode())

    @abstractmethod
    def detect_bt(self):
        """detect_bt looks for paired MAC addresses,
        names for paired devices, and connected status for devices.
        Two whitelists, one for paired, one for connected.
        """
        raise NotImplementedError

    @abstractmethod
    def detect_usb(self):
        """detect_usb finds all USB IDs/VolumeSerialNumbers connected to the system.
        For linux, this includes internal hardware as well.
        """
        raise NotImplementedError

    @abstractmethod
    def detect_ac(self):
        """detect_ac checks if the system is connected to AC power
        Statuses:
        0 = disconnected
        1 = connected
        """
        raise NotImplementedError

    @abstractmethod
    def detect_battery(self):
        """detect_battery checks if there is a battery.
        Obviously this is useless if your system does not have a battery.
        Statuses:
        0 = not present
        1 = present
        """
        raise NotImplementedError

    @abstractmethod
    def detect_tray(self):
        """detect_tray reads status of the CDROM_DRIVE.
        Statuses:
        1 = no disk in tray
        2 = tray open
        3 = reading tray
        4 = disk in tray
        """
        raise NotImplementedError

    @abstractmethod
    def detect_ethernet(self):
        """Check if an ethernet cord is connected.
        Status:
        0 = False
        1 = True
        """
        raise NotImplementedError

    @abstractmethod
    def kill_the_system(self, warning: str):
        """Send an e-mail, and then
        shut the system down quickly.
        """
        log.critical('Kill reason: ' + warning)
        if self.DEBUG:
            return

        try:
            self.mail_this(warning)
        except socket.gaierror:
            current_time = time.localtime()
            formatted_time = time.strftime('%Y-%m-%d %I:%M:%S%p', current_time)
            with open(self.config['global']['killer_file'], 'a', encoding='utf-8') as killer_file:
                killer_file.write('Time: {0}\nInternet is out.\n'
                                  'Failure: {1}\n\n'.format(formatted_time, warning))

    def mail_this(self, warning: str):
        email_config = self.config["email"]
        subject = '[ALERT: {0}]'.format(warning)

        current_time = time.localtime()
        formatted_time = time.strftime('%Y-%m-%d %I:%M:%S%p', current_time)

        content = 'Time: {0}\nWarning: {1}'.format(formatted_time, warning)
        msg = MIMEText(content, 'plain')
        msg['Subject'] = subject
        msg['From'] = email_config["sender"]
        ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.check_hostname = True
        ssl_context.set_ciphers(email_config["cipher_choice"])
        ssl_context.options |= ssl.HAS_SNI
        ssl_context.options |= ssl.OP_NO_COMPRESSION
        # No need to explicitly disable SSLv* as it's already been done
        # https://docs.python.org/3/library/ssl.html#id7
        ssl_context.options |= ssl.OP_NO_TLSv1
        ssl_context.options |= ssl.OP_NO_TLSv1_1
        ssl_context.options |= ssl.OP_SINGLE_DH_USE
        ssl_context.options |= ssl.OP_SINGLE_ECDH_USE
        conn = smtplib.SMTP_SSL(email_config["smtp_server"],
                                port=email_config["smtp_port"],
                                context=ssl_context)
        conn.esmtp_features['auth'] = email_config["login_auth"]
        conn.login(email_config["sender"], email_config["sender_password"])
        try:
            for each in json.loads(email_config["destination"]):
                conn.sendmail(email_config["sender"], each, msg.as_string())
        except socket.timeout:
            raise socket.gaierror
        finally:
            conn.quit()
