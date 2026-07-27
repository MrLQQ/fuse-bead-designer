# Fuse Bead Designer v0.3.1 Update Discovery Design

## Goal

Add a safe update path that discovers new stable releases automatically and
lets a user approve the update with one natural-language sentence.

The design must preserve the current stable-tag installation model. It must not
silently replace plugin code, track an unreviewed branch, delay pattern
generation when the network is unavailable, or ask users to copy shell
commands.

## User Experience

The existing pattern-generation Skill performs a lightweight update check when
it starts, subject to a per-device 24-hour interval.

When no newer stable release exists, the check is recent, or the network is
unavailable, the pattern task continues without an update message.

When a newer stable release exists, the Agent displays one concise notice in
the user's conversation language. For a Chinese conversation:

> Fuse Bead Designer v0.4.0 is available. Reply “确认更新到 v0.4.0” to update.

The notice does not interrupt the active pattern task. The user can ignore it
and continue using the installed version.

When the user later replies with the confirmation sentence, a separate update
Skill owns the update workflow. After a successful update it reports the old
and new versions, stops without running examples or installing unrelated
dependencies, and tells the user to start a new task so the host reloads the
plugin.

## Architecture

The feature has three isolated units.

### 1. Update policy

`update-policy.json` lives in the standalone Skill so both the full Plugin and
the standalone Skill archive contain the same update metadata:

- repository: `MrLQQ/fuse-bead-designer`
- current version: `0.3.1`
- stable tag pattern: `vMAJOR.MINOR.PATCH`
- check interval: `86400` seconds

Repository tests keep this version synchronized with the Plugin manifest,
Marketplace manifest, Python package metadata, release packager, README, and
`AGENTS.md`.

### 2. Update checker

`scripts/check_update.py` is a standard-library-only command. It:

1. loads `update-policy.json`;
2. resolves a platform-appropriate cache location, with an explicit
   `--cache-file` override for tests and constrained hosts;
3. returns the cached result without network access when the previous attempt
   is less than 24 hours old;
4. queries GitHub's repository tags API with a short timeout;
5. accepts only exact stable tags matching `vMAJOR.MINOR.PATCH`;
6. compares versions numerically, not lexicographically;
7. writes a small cache containing no credentials or user content; and
8. prints one JSON result for the calling Agent.

The result states are:

- `recent`: the 24-hour interval has not elapsed;
- `up-to-date`: no newer stable tag exists;
- `update-available`: a higher stable tag exists;
- `unavailable`: the check failed or returned unusable data.

All expected network, JSON, cache-permission, and rate-limit failures return an
`unavailable` result without a traceback. They do not block the user's pattern
task. The checker never installs or changes a plugin.

The cache records every completed attempt, including unavailable attempts, so
an offline host does not retry on every pattern request. A `--force` option
bypasses the interval only for an explicit user-requested check.

### 3. Update Skill

`update-fuse-bead-designer` is a second Skill in the Plugin. Its description
triggers on requests to check or update this specific Plugin, including the
confirmation sentence emitted by the checker.

The Skill performs the following workflow:

1. inspect the installed Plugin version and configured Marketplace;
2. force a fresh stable-version check;
3. stop if the requested tag is missing, is not an exact stable tag, is not
   newer than the installed version, or no longer matches the latest stable
   result;
4. treat the user's explicit confirmation sentence as authorization to update
   only Fuse Bead Designer;
5. use the host's native Plugin management capability when available;
6. on Codex CLI, replace the old pinned Marketplace ref with the confirmed
   stable tag and reinstall the named Plugin;
7. read the installed version after the operation and require it to equal the
   confirmed target; and
8. report success and require a new task before using the new Skill.

The update Skill must not run project examples, create a virtual environment,
install pattern-generation dependencies, change another Marketplace, or use
`main` as the target ref. It must not bypass a host safety prompt; a host may
still require the user to approve the filesystem or network operation.

## Codex Update Transaction

Codex currently exposes Marketplace refresh rather than a cross-tag
`plugin update` command. A Marketplace installed from immutable `v0.3.0` stays
on that tag when refreshed, so changing versions requires rebinding the
Marketplace to the confirmed stable tag.

The update workflow records the old tag before making changes. If the new
Marketplace cannot be added or the Plugin cannot be verified at the target
version, the Agent attempts to restore the old stable tag and reports the
failure. It must never claim success from command exit status alone.

Host-specific commands remain procedural guidance inside the update Skill
rather than being executed by `check_update.py`. This keeps discovery
read-only, makes permission boundaries visible to the Agent, and lets
non-Codex hosts use their own Plugin or Skill installer.

The full Codex Plugin contains the dedicated update Skill. The standalone
Agent Skill archive contains the checker, policy, and bounded fallback
instructions for asking its host to replace the installed Skill from the
confirmed stable tag; it does not pretend that every host exposes the same
installer.

## Pattern Skill Integration

The existing `create-fuse-bead-patterns` Skill adds one startup step:

1. run the checker without `--force`;
2. parse its JSON output;
3. retain only the `update-available` notice for the final response; and
4. continue the pattern workflow regardless of check outcome.

The checker must not become a prerequisite for classification, image editing,
compilation, verification, or delivery. If the pattern task fails for an
unrelated reason, update information must not obscure that failure.

## Cache and Privacy

The checker stores only:

- the attempt timestamp;
- installed version;
- latest stable version when known; and
- result state.

It stores no image paths, prompts, email addresses, credentials, tokens, or
GitHub response bodies.

Default cache locations follow the host platform:

- macOS: `~/Library/Caches/fuse-bead-designer/update-check.json`
- Linux: `${XDG_CACHE_HOME:-~/.cache}/fuse-bead-designer/update-check.json`
- Windows: `%LOCALAPPDATA%\fuse-bead-designer\update-check.json`

If the default location is not writable, the checker returns `unavailable`
without changing another directory. Tests and managed hosts can supply a cache
file explicitly.

## Testing

Unit tests cover:

- numeric SemVer ordering, including `v0.10.0` over `v0.9.9`;
- rejection of prerelease, malformed, and unrelated tags;
- update available, up to date, recent cache, forced check, offline, timeout,
  malformed JSON, rate limit, and unwritable cache behavior;
- JSON output with no traceback for expected failures;
- the 24-hour boundary;
- cache contents containing only the allowed fields; and
- no installer or subprocess side effects in the checker.

Repository contract tests cover:

- both Skills are declared and packaged;
- the pattern Skill runs a non-blocking check and only surfaces an available
  update;
- the update Skill requires explicit confirmation and a stable target;
- Codex updates verify the installed version and describe rollback;
- README presents natural-language update usage before developer commands; and
- all `0.3.1` version declarations stay synchronized.

Release validation covers:

- the full test suite;
- Skill and Plugin validators;
- deterministic Plugin and standalone Skill archives;
- archive roots and embedded version metadata; and
- absence of private paths, credentials, cache files, and generated runtime
  state.

## Documentation

The Chinese README remains primary. Both README files add:

- an “Automatically discover updates” section;
- the exact confirmation sentence;
- an explanation that checks occur at most once per 24 hours;
- offline and failure behavior;
- the requirement to start a new task after updating; and
- a developer note distinguishing pinned stable tags from branch tracking.

`AGENTS.md` gains a bounded update contract so installing, checking, and
updating remain separate user intents.

## Release

The implementation ships as `v0.3.1`. The release process updates all version
sources, builds both archives once from the reviewed commit, verifies their
contents, fast-forwards `main`, creates tag `v0.3.1`, and pushes `main` and the
tag.

## Non-goals

- Silent or forced automatic updates.
- Tracking `main` by default.
- Updating Codex itself.
- Updating another Plugin or Marketplace.
- Running pattern examples as an update smoke test.
- Installing optional pattern-generation dependencies during an update.
- Guaranteeing automatic updates on hosts that do not expose a Plugin or Skill
  installation mechanism.
