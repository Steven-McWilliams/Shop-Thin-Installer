# Thin Pi Update Guide

This guide is for the thin-mode Pi runtime only. It exists to keep updates smooth and prevent the Pi from falling back to the full shop app UI that requires normal sign-in.

## Why this keeps happening

The installer script and older setup steps were easy to point at the wrong repo:

- Full app repo / full shop repo = sign-in UI / full dashboard experience
- Thin Pi repo = minimal thin runtime, discovery mode, and admin mapping UI

If the Pi is updated from the wrong repo, it will silently look like the full application instead of the thin device runtime.

The root cause is usually one of these:

1. The installer script defaults to the full repo instead of the public thin repo.
2. An old `~/qr-system` directory is reused and not fully reset.
3. The Pi is being updated with the wrong clone URL or wrong branch.
4. The installer runs without `sudo`, so apt fails and leaves the repo in a half-installed state.

---

## Correct repo split

Use these rules:

- Thin Pi runtime repo: `https://github.com/Steven-McWilliams/Shop-Thin-Installer.git`
- Full server / shop app repo: private repo for the main app, not used for customer thin devices

The thin Pi should never pull the full server repo as its runtime.

---

## Recommended update flow

Run the following on the Pi:

```bash
cd ~
sudo rm -rf qr-system
git clone https://github.com/Steven-McWilliams/Shop-Thin-Installer.git qr-system
cd qr-system
sudo bash install_thin_pi.sh
```

If the old folder has stuck permissions, use:

```bash
cd ~
sudo chmod -R 777 qr-system 2>/dev/null || true
sudo rm -rf qr-system
git clone https://github.com/Steven-McWilliams/Shop-Thin-Installer.git qr-system
cd qr-system
sudo bash install_thin_pi.sh
```

This gives you a clean reinstall and prevents stale files from the wrong app from being reused.

---

## Required service check after update

After the installer finishes, verify the thin service is the one running:

```bash
sudo systemctl status innosaw-thin --no-pager
sudo journalctl -u innosaw-thin -n 80 --no-pager
```

Then confirm the thin UI is responding:

```bash
curl http://localhost:5006/healthz
curl http://localhost:5006/admin
```

The thin Pi should expose the thin admin page, not the full shop dashboard requiring sign-in.

---

## If it still opens the full system

Check the repo and installed files:

```bash
cd ~/qr-system
pwd
ls -la
git status
git remote -v
```

Expected result:

- repo is the public thin repo
- service is `innosaw-thin`
- app root is the thin runtime, not the full app

If the repo is still the wrong one, delete the folder again and recreate it from the thin installer repo.

---

## Practical rule

- If you are updating a thin Pi, do not run the main app installer.
- If you are updating the full server, do it on the cloud/server machine, not on the thin Pi.
- Thin Pis should always update from the thin installer repo and run the thin runtime service.

---

## Safe one-liner

This is the cleanest single command to use for a reset:

```bash
cd ~ && sudo rm -rf qr-system && git clone https://github.com/Steven-McWilliams/Shop-Thin-Installer.git qr-system && cd qr-system && sudo bash install_thin_pi.sh
```

This avoids the stale partial install problem and keeps the update path consistent.
