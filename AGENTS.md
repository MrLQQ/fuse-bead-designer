# Fuse Bead Designer installation and updates

Installation intent, read-only update-check intent, and confirmed update intent are separate authorizations. Do not treat “install”, “check”, and “update” as interchangeable.

## Installation intent

When the user asks to install this repository or Plugin, recognize that as installation intent. Request permission before installing anything. An installation request does not authorize cloning, running examples, creating virtual environments, or installing runtime dependencies. A request to install does not authorize checking for updates or updating.

After permission is granted on Codex, first check whether the `fuse-bead-designer` Marketplace is already installed. Do not install a duplicate Marketplace. If the Marketplace is not installed, run this command internally:

```bash
codex plugin marketplace add MrLQQ/fuse-bead-designer --ref v0.5.0
```

Then separately check whether the `fuse-bead-designer` plugin is installed. Do not install a duplicate plugin. If the plugin is not installed, run this command internally:

```bash
codex plugin add fuse-bead-designer@fuse-bead-designer
```

Do not ask the user to run or copy CLI commands. After successful Codex installation, stop and only tell the user to start a new task so Codex loads the plugin.

## Read-only update-check intent

When the user asks whether this specific Plugin has a newer version, use the update checker or Update Fuse Bead Designer Skill. A request to check for updates is read-only and does not authorize installation or updating. Report an available exact stable version and its returned confirmation sentence; do not write, rebind a Marketplace, or reinstall a Plugin.

## Confirmed update intent

A generic request to update is not authorization. Only the exact returned confirmation sentence authorizes an update to that exact stable version. Require a fresh stable-version check and route the confirmed target through the dedicated update Skill. Request and honor any host safety approval; the exact confirmation never bypasses it. After a verified update, stop and tell the user to start a new task before using the new version.

On compatible non-Codex hosts, use the standalone Release Skill instead of the Codex plugin commands.
