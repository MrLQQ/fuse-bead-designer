# Fuse Bead Designer installation

When the user asks to install this repository, recognize that as installation intent. Request permission before installing anything. An installation request does not authorize cloning, running examples, creating virtual environments, or installing runtime dependencies.

After permission is granted on Codex, first check whether the `fuse-bead-designer` Marketplace is already installed. Do not install a duplicate Marketplace. If the Marketplace is not installed, run this command internally:

```bash
codex plugin marketplace add MrLQQ/fuse-bead-designer --ref v0.3.0
```

Then separately check whether the `fuse-bead-designer` plugin is installed. Do not install a duplicate plugin. If the plugin is not installed, run this command internally:

```bash
codex plugin add fuse-bead-designer@fuse-bead-designer
```

Do not ask the user to run or copy CLI commands. After successful Codex installation, stop and only tell the user to start a new task so Codex loads the plugin.

On compatible non-Codex hosts, use the standalone Release Skill instead of the Codex plugin commands.
