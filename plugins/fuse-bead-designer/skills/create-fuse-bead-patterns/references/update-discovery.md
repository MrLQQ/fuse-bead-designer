# Update Discovery

The checker is read-only. Run it without `--force` at pattern startup. It
caches each completed attempt for 24-hour behavior: normally it does not fetch
again until 24 hours have elapsed. Use `--force` only for an explicit request
to check or update Fuse Bead Designer.

Interpret its JSON `status` as follows:

- `recent`: a completed check is still within the 24-hour interval.
- `up-to-date`: no newer exact stable tag exists.
- `update-available`: a newer exact stable tag exists; retain its version and
  confirmation prompt for the final pattern response.
- `unavailable`: the check could not complete; continue without a notice.

Only `update-available` is user-visible during pattern generation. The checker
does not install, remove, or modify a Plugin.

## Update boundary

Route a specific check, update request, or exact confirmation to
`update-fuse-bead-designer`. An update request without an exact target is not
write authorization: after a fresh check, ask for the returned sentence, such
as `确认更新到 v0.5.0`.

On Codex, use its Plugin manager only. Before any standalone write, require the
host's native manager to record the exact installed version and corresponding
old stable ref, install only the confirmed exact target, mechanically verify
the installed target, and restore the old stable ref after any install or
verification failure. Mechanically verify the restored old version before
stopping.

If any native capture, scoped install, mechanical verification, or rollback
capability is missing, stop before writes and provide only bounded manual
installation guidance. Name the confirmed tag, this standalone Skill, and the
missing host capability; direct the user to the host's documented exact-release
installation flow without inventing commands. Do not perform a partial
replacement. Never leave a changed standalone Skill unverified. Do not use
Codex commands on a standalone host.

Confirmation authorizes only this Plugin or standalone Skill. It never
authorizes bypassing filesystem, network, or host safety approvals. Do not bypass host permission prompts.
