# Installation guide

Using this image : Raspberry Pi OS with desktop (64-bit).  
Perform all commands as root user.

## System updates
```bash
apt update
apt upgrade
reboot
```

## Update raspi configuration:
```bash
raspi-config
# Mandatory:
    3 Interface Options
        I7 Remote GPIO -> YES
# Optional:
    1 System Options
        S1 Wireless LAN -> Setup your wifi.
        S5 Boot / Auto Login
            B4 Desktop Autologin -> YES
        S6 Splash Screen -> YES
    2 Display Options
        D2 Screen Blanking -> NO
```

## Dependencies:
```bash
apt install python3-flask python3-picamera2 python3-qrcode python3-easywebdav git

# Not available from apt:
pip3 install rembg pydavsync --break-system-packages
```

## Clone this repository in /opt:
```bash
cd /opt
git clone https://github.com/corentin-soriano/Pi-Photobooth.git
```

## Add systemd services and local configuration:
```bash
cd /opt/Pi-Photobooth/
ln -sf $PWD/photobooth-{frontend,backend}.service /etc/systemd/system/

cp config{.tpl,}.ini
chmod 600 config.ini
vi config.ini
```

## Enable services on boot and reboot to apply all changes:
**Note: First launch take about 1 minute to load rembg.**
```bash
systemctl enable photobooth-{frontend,backend}.service
reboot
# Check state:
systemctl status photobooth-{frontend,backend}.service
```
