# Public Thin Pi Bootstrap

This repository is intentionally public and contains only the bootstrap installer needed to bring a fresh Raspberry Pi onto the Thin Pi workflow.

The real app repo remains private, and the Pi can authenticate with a GitHub token or SSH to pull the private code once the bootstrap script has done the initial setup.

## Purpose

- allow anonymous download of the installer from GitHub raw URLs
- create a Thin Pi runtime in `/home/pi/qr-system`
- authenticate to the private app repo using `APP_REPO_URL` or `GITHUB_TOKEN`
- install and start the systemd service

## Public installer URL

```bash
curl -fsSL https://raw.githubusercontent.com/your-public-thin-repo/main/install_thin_pi.sh -o install_thin_pi.sh
sudo bash install_thin_pi.sh
```

## Optional environment overrides

```bash
export APP_REPO_URL="https://github.com/Steven-McWilliams/Shop.git"
export APP_REPO_BRANCH="main"
export GITHUB_TOKEN="ghp_xxx"

sudo -E bash install_thin_pi.sh
```

If the app repo is private, set `GITHUB_TOKEN` so the installer can clone the private repository with a GitHub personal access token.

## Notes

- This repo is public for bootstrap purposes only.
- Production app files stay in the private repo.
- Keep the public installer minimal and stable.
