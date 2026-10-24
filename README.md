# Public Thin Pi Bootstrap

This repository is intentionally public and contains only the minimal files needed to install and run the Thin Pi on a fresh Raspberry Pi.

The public bootstrap repo should stay small and self-contained. It does not depend on the private app repo during initial setup.

## Purpose

- allow anonymous download of the installer from GitHub raw URLs
- install the Thin Pi runtime into `/home/pi/qr-system`
- create the systemd service
- keep the public repo minimal and easy to maintain

## Public installer URL

```bash
curl -fsSL https://raw.githubusercontent.com/Steven-McWilliams/Shop-Thin-Installer/main/install_thin_pi.sh -o install_thin_pi.sh
sudo bash install_thin_pi.sh
```

## Notes

- This repo is for the public Thin Pi install path only.
- No private app repo is required during first-time bootstrapping.
- Keep the public installer focused on Thin Pi installation and runtime setup only.
