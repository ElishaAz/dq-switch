# dq-switch
Switch from Dvorak to QWERTY while Ctrl, Alt or Meta are pressed.

Note: currently, only KDE Plasma is supported.

## Install
This project uses uinput to check when keys are pressed, and as such, requires the user to be in the `input` group.
You can add the current user to the `input` by running `sudo usermod -a -G input $USER`.
Note that this is a security risk: any program that runs as the current user can read all key presses (and any other input device, e.g. mouse).

1. Add the current user to the `input` group: `sudo usermod -a -G input $USER` and reboot.
2. Clone this repository: `git clone https://github.com/ElishaAz/dq-switch` and `cd dq-switch`
3. Create a virtual environment: `python -m venv .venv`
4. Activate it: `. .venv/bin/activate`
5. Install dependencies: `pip install -r requirements.txt`

## Configure

See `dq-switch.cfg` and `dq-switch.py --help`.

## Run
If you created a virtual python environment as above, simply run `dq-switch`. Otherwise, run `python dq-switch.py`.
