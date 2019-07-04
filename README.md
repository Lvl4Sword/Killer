# Attention!

The project requires testing and development from individuals with a Mac.

If you're interested in assisting with this please contact one of the devs

within the Discord or IRC channel listed below

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

            System tamper detector
(USB, Bluetooth, AC, Battery, Disk Tray, Ethernet)
  Shuts the system down upon disallowed changes.
```


[![PyPI - Current version](https://img.shields.io/pypi/v/killer.svg)](https://pypi.org/project/killer/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/killer.svg)](https://pypistats.org/packages/killer)

[![Killer Discord Channel](https://img.shields.io/badge/discord-killer-brightgreen.svg)](https://discord.gg/jKH5bXg)
[![Join irc.freenode.net #killer channel](https://img.shields.io/badge/irc-killer-brightgreen.svg)](https://webchat.freenode.net/?channels=%23killer)


# Installation and usage
```bash
pip3 install --user -U killer
killer --help
python -m killer --help
```


# Development
Setting up an environment for hacking on Killer.

## Linux
```bash
git clone https://github.com/Lvl4Sword/Killer.git
cd ./Killer
mkdir -p ~/.virtualenvs/
python3 -m venv ~/.virtualenvs/killer
source ~/.virtualenvs/killer/bin/activate
python -m pip install -U pip
python -m pip install -U -r requirements.txt
python -m pip install -U -r dev-requirements.txt
```

## Windows
```bash
git clone https://github.com/Lvl4Sword/Killer.git
Set-Location -Path .\Killer
New-Item -ItemType Directory -Force -Path $env:USERPROFILE\.virtualenvs\
py -3 -m venv $env:USERPROFILE\.virtualenvs\killer
$env:USERPROFILE\.virtualenvs\Scripts\Activate.ps1\
python -m pip install -U pip
pip install -U -r requirements.txt
pip install -U -r dev-requirements.txt
```
