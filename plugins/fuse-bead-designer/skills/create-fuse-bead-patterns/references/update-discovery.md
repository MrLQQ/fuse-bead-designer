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
as `确认更新到 v0.4.0`.

On Codex, use its Plugin manager only. On a standalone compatible host, use
that host's native Skill manager to replace only this standalone Skill from the
confirmed exact stable release. Do not use Codex commands on a standalone
host, and do not claim an update is possible if the host exposes no native
installer.

Confirmation authorizes only this Plugin or standalone Skill. It never
authorizes bypassing filesystem, network, or host safety approvals. Do not bypass host permission prompts.
