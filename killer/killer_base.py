import configparser
import json
import smtplib
import socket
import ssl
import sys
import time
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from pathlib import Path


class KillerBase(ABC):
    def __init__(self, config_path: str = None, debug: bool = False):
        socket.setdefaulttimeout(3)
        self.DEBUG = debug
        if config_path is None:
            to_search = [Path.cwd(),
                         Path(__file__).parent,
                         Path.home()]
            for path in to_search:
                if self.DEBUG:
                    print("Searching for 'killer.conf' in: %s" % str(path))
                file = path / 'killer.conf'
                if file.exists():
                    config_path = file
                    break
            if config_path is None:
                print("ERROR: Failed to find configuration file 'killer.conf'"
                      "\nPaths searched:\n%s" % ''.join(['  %s\n' % str(x)
                                                         for x in to_search]))
                sys.exit(1)
        self.config_file = Path(config_path).resolve()
        if not self.config_file.exists():
            print("Could not find configuration file %s" % str(self.config_file))
            sys.exit(1)
        self.config = configparser.ConfigParser()
        self.config.read(
            str(self.config_file))  # Python 3.5 requires str() conversion

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
        try:
            self.mail_this(warning)
        except socket.gaierror:
            current_time = time.localtime()
            formatted_time = time.strftime('%Y-%m-%d %I:%M:%S%p', current_time)
            with open(self.config['global']['KILLER_FILE'], 'a') as killer_file:
                killer_file.write('Time: {0}\nInternet is out.\nFailure: {1}\n\n'.format(formatted_time, warning))

    def mail_this(self, warning: str):
        subject = '[ALERT: {0}]'.format(warning)

        current_time = time.localtime()
        formatted_time = time.strftime('%Y-%m-%d %I:%M:%S%p', current_time)

        content = 'Time: {0}\nWarning: {1}'.format(formatted_time, warning)
        msg = MIMEText(content, 'plain')
        msg['Subject'] = subject
        msg['From'] = self.config["email"]["SENDER"]
        ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.check_hostname = True
        ssl_context.set_ciphers(self.config["email"]["CIPHER_CHOICE"])
        ssl_context.options &= ~ssl.HAS_SNI
        ssl_context.options &= ~ssl.OP_NO_COMPRESSION
        # No need to explicitly disable SSLv* as it's already been done
        # https://docs.python.org/3/library/ssl.html#id7
        ssl_context.options &= ~ssl.OP_NO_TLSv1
        ssl_context.options &= ~ssl.OP_NO_TLSv1_1
        ssl_context.options &= ~ssl.OP_SINGLE_DH_USE
        ssl_context.options &= ~ssl.OP_SINGLE_ECDH_USE
        conn = smtplib.SMTP_SSL(self.config["email"]["SMTP_SERVER"],
                                port=self.config["email"]["SMTP_PORT"],
                                context=ssl_context)
        conn.esmtp_features['auth'] = self.config["email"]["LOGIN_AUTH"]
        conn.login(self.config["email"]["SENDER"], self.config["email"]["SENDER_PASSWORD"])
        try:
            for each in json.loads(self.config["email"]["DESTINATION"]):
                conn.sendmail(self.config["email"]["SENDER"], each, msg.as_string())
        except socket.timeout:
            raise socket.gaierror
        finally:
            conn.quit()
