# Fuse Bead Designer installation

When the user asks to install or use this repository, recognize that as installation intent. Request permission before installing anything.

After permission is granted on Codex, first check whether the `fuse-bead-designer` Marketplace is already installed. Do not install a duplicate Marketplace. If it is not installed, run these commands internally:

```bash
codex plugin marketplace add MrLQQ/fuse-bead-designer --ref v0.2.0
codex plugin add fuse-bead-designer@fuse-bead-designer
```

Do not ask the user to run or copy CLI commands. After successful Codex installation, tell the user to start a new task so Codex loads the plugin.

On compatible non-Codex hosts, use the standalone Release Skill instead of the Codex plugin commands.
