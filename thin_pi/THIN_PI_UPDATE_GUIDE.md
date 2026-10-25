# Thin Pi Update Guide

This guide is for the thin-mode Pi runtime only. It keeps updates in the public thin repo and prevents the Pi from falling back to the full private app UI.

## Correct repo split

- Thin Pi runtime repo: `https://github.com/Steven-McWilliams/Shop-Thin-Installer.git`
- Full shop app repo: private repo for the main app, not used for customer thin devices

## Recommended update flow

```bash
cd ~
sudo rm -rf qr-system
git clone https://github.com/Steven-McWilliams/Shop-Thin-Installer.git qr-system
cd qr-system
sudo bash install_thin_pi.sh
```

If the old folder is stale or permissions are blocked, use:

```bash
cd ~
sudo chmod -R 777 qr-system 2>/dev/null || true
sudo rm -rf qr-system
git clone https://github.com/Steven-McWilliams/Shop-Thin-Installer.git qr-system
cd qr-system
sudo bash install_thin_pi.sh
```

## Required service check

```bash
sudo systemctl status innosaw-thin --no-pager
sudo journalctl -u innosaw-thin -n 80 --no-pager
curl http://localhost:5006/healthz
curl http://localhost:5006/admin
```

## Rule

If the Pi is being updated, it should only pull from the public thin repo. It should not pull the private full app repo.
