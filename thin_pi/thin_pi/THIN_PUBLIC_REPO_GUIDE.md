# Thin public repo plan (easy updates)

You can’t make only one branch public. Repo visibility applies to the entire repo.

To keep the “full” system private but allow customer installs without GitHub logins, use a **separate public repo** that contains only the thin files.

---

## Recommended setup

- **Private** repo: `Innosaw/QR-system` (full system, internal)
- **Public** repo: `Innosaw/QR-system-thin` (thin-only installer + runtime)

The thin-only repo is generated from the private repo using the manifest:
- `thin_pi/thin_repo_manifest.txt`

---

## One-time: create and publish `QR-system-thin`

1) Create a new GitHub repo (public): `Innosaw/QR-system-thin`

2) From the private repo, export a clean thin tree:

```bash
python3 thin_pi/export_thin_repo.py --out dist/QR-system-thin --clean
```

3) Initialize and push the thin repo:

```bash
cd dist/QR-system-thin
git init
git add .
git commit -m "Initial thin public repo"
git branch -M main
git remote add origin https://github.com/Innosaw/QR-system-thin.git
git push -u origin main
```

---

## Updating `QR-system-thin` after you change thin code

Whenever you update thin files in the private repo:

```bash
python3 thin_pi/export_thin_repo.py --out dist/QR-system-thin --clean
cd dist/QR-system-thin
git add .
git commit -m "Update thin"
git push
```

---

## Pointing thin installs at the public repo

The thin installer supports overriding the repo URL:

```bash
export INNOSAW_THIN_REPO_URL="https://github.com/Innosaw/QR-system-thin.git"
sudo bash thin_pi/install_thin_pi.sh
```

Once you’re ready to switch fully, you can change the default in the installer, or keep using the env var.


