# Thin Pi Setup Guide

This repo is the public thin-device runtime for Raspberry Pi units.

## Purpose

Thin Pis are intentionally minimal:

- local admin UI
- scanner detection and mapping
- LAN discovery for local approval
- thin-mode forwarding to the main shop/server when paired

They do not run the full shop app UI.

## Install

```bash
cd ~
sudo rm -rf qr-system
git clone https://github.com/Steven-McWilliams/Shop-Thin-Installer.git qr-system
cd qr-system
sudo bash install_thin_pi.sh
```

## Validate

```bash
sudo systemctl status innosaw-thin --no-pager
curl http://localhost:5006/healthz
curl http://localhost:5006/admin
```

## Repo boundary

- Thin Pi repo: `https://github.com/Steven-McWilliams/Shop-Thin-Installer.git`
- Full private shop repo: separate private app repo, not used for customer Pi devices
