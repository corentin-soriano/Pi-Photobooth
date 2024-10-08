# Features
- Full touchscreen controls (except the button which enables "admin mode").
- Print as many times as you want.
- Automatic save to webdav server.
- QRCode generation to download pictures.
- Background replacement (better with green screen background).
- Optionally add custom text and date/time on pictures.
- English and French translations.
- All time counters for pictures and prints.
- Can send webhooks for some data (ex: printer unavailable).

# UI preview
Preview page:  
<img src="screenshots/01_preview_page.png" alt="Preview page" style="width: 50%;" />

Preview page with custom background:  
<img src="screenshots/02_preview_page_bg_replace.png" alt="Preview custom background" style="width: 50%;" />

Picture review with date/time and custom message:  
<img src="screenshots/03_picture_review.png" alt="Picture review" style="width: 50%;" />

Picture review with unavailable printer:  
<img src="screenshots/04_picture_review_printer_unavailable.png" alt="Picture review with unavailable printer" style="width: 50%;" />

Settings (admin mode):  
<img src="screenshots/05_settings.png" alt="Settings" style="width: 50%;" />

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
apt install python3-flask python3-picamera2 python3-qrcode python3-easywebdav python3-opencv git ncat

# Not available from apt:
pip3 install rembg --break-system-packages
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

## Add support for auto-cutting paper (Brother VC-500W only)
- Follow instructions on https://github.com/corentin-soriano/vc-500w_autocut
- In your config.ini, set cups printer as `Brother_VC-500W_Gateway`.
