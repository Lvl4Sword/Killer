```
           _  _  _  _ _
          | |/ /(_)| | |
          |   /  _ | | | ____ _ _
          |  \  | || | |/ _  ) `_|
          | | \ | || | ( (/_/| |
          |_|\_\|_|\__)_)____)_|
   _____________________________________
   \                       | _   _   _  \
    `.                  ___|____________/
      ``````````````````
```

```
            System tamper detector
(USB, Bluetooth, AC, Battery, Disk Tray, Ethernet)
  Shuts the system down upon disallowed changes.

Looking for testers to support more than just Linux.
```

## Installation
```bash
git clone https://github.com/Lvl4Sword/Killer.git
cd Killer
pip3 install --user -U -r requirements.txt
```

## Usage
TBD


# Development
## Linux
```bash
git clone https://github.com/Lvl4Sword/Killer.git
cd Killer
mkdir -p ~/.virtualenvs/
python3 -m venv ~/.virtualenvs/killer
source ~/.virtualenvs/killer/bin/activate
pip install -U -r requirements.txt
pip install -U -r dev-requirements.txt
```

## Windows
TBD soon
