---
name: update-fuse-bead-designer
description: Check or update the Fuse Bead Designer Plugin or standalone Skill. Use when the user asks whether this specific Plugin has an update, asks to update it, or confirms a version-specific notice such as “确认更新到 v0.5.0”.
---

# Update Fuse Bead Designer

Read [update discovery](../create-fuse-bead-patterns/references/update-discovery.md).
Update only `fuse-bead-designer@fuse-bead-designer` from the named
`fuse-bead-designer` Marketplace. Never update another Plugin or Marketplace.

## Check and confirm

1. Inspect only the named Marketplace and Plugin. On Codex, read
   `codex plugin marketplace list --json` and `codex plugin list --json`.
   Require the Marketplace to be the Fuse Bead Designer Git source and the
   installed Plugin to be exactly `fuse-bead-designer@fuse-bead-designer`.
2. From this Skill directory, run
   `python ../create-fuse-bead-patterns/scripts/check_update.py --force`.
   Parse its JSON; do not write when it is not `update-available`.
3. Require the requested target to equal the fresh `latest_version`, be newer
   than the installed version, and be an exact stable tag of the form
   `vMAJOR.MINOR.PATCH`. Never track `main` or a branch.
4. Before any write, require an explicit versioned confirmation for that fresh
   target, exactly such as `确认更新到 v0.5.0`. A request such as “更新这个插件吧”
   is not confirmation. If it is absent or names another target, ask for the
   exact sentence and stop.
5. Request and honor every host safety approval required for the write. Exact
   confirmation does not bypass those prompts.

## Apply the update

Prefer the host's native Plugin manager. On Codex, use only the verified
transaction below; do not invent `codex plugin update`, `inspect`, or `doctor`
commands.

1. From the installed Plugin JSON, record the installed version and map it to
   the old exact stable ref `v<installed-version>`; stop if it cannot form an
   exact stable tag. This records the installed version before any write.
2. Remove only the named Plugin and Marketplace, then rebind the named
   Marketplace to the confirmed target and reinstall only the named Plugin:

   ```bash
   codex plugin remove fuse-bead-designer@fuse-bead-designer
   codex plugin marketplace remove fuse-bead-designer
   codex plugin marketplace add MrLQQ/fuse-bead-designer --ref <confirmed-target>
   codex plugin add fuse-bead-designer@fuse-bead-designer
   ```

3. Read `codex plugin list --json` and verify the installed version equals the
   confirmed target without its leading `v`. Do not infer success from command
   exit status. If verification or any target step fails, restore the previous
   stable tag by removing only this Plugin and Marketplace, adding
   `MrLQQ/fuse-bead-designer --ref <old-stable-tag>`, reinstalling this Plugin,
   and verifying the installed version again. Report a rollback failure plainly.
   In other words: restore the previous stable tag before reporting failure.
4. Before any standalone write, require the host's native manager to record the
   exact installed version and corresponding old stable ref, install only the
   confirmed exact target, mechanically verify the installed target, and
   restore the old stable ref after any install or verification failure.
   Mechanically verify the restored old version before stopping. If any native
   capture, scoped install, mechanical verification, or rollback capability is
   missing, stop before writes and provide only bounded manual installation
   guidance. Never leave a changed standalone Skill unverified. Do not
   substitute Codex CLI commands on a standalone host.

Do not run examples, create a virtual environment, install pattern-generation
dependencies, or perform another Plugin update. After either verified success
or a rollback attempt, stop and ask the user to start a new task before using
the resulting Skill version.
