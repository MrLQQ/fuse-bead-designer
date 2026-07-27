"""Check whether a newer stable Fuse Bead Designer release is available."""

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import platform
import re
import tempfile
import time
from typing import Callable, Iterable, Mapping
import urllib.request


STABLE_TAG = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
CACHE_FIELDS = ("checked_at", "current_version", "latest_version", "status")
DEFAULT_POLICY_FILE = Path(__file__).resolve().parent.parent / "update-policy.json"
LOCK_STALE_SECONDS = 60


@dataclass(frozen=True)
class UpdatePolicy:
    repository: str
    current_version: str
    stable_tag_pattern: str
    check_interval_seconds: int


def load_policy(path: Path) -> UpdatePolicy:
    data = json.loads(path.read_text(encoding="utf-8"))
    return UpdatePolicy(
        repository=data["repository"],
        current_version=data["current_version"],
        stable_tag_pattern=data["stable_tag_pattern"],
        check_interval_seconds=data["check_interval_seconds"],
    )


def parse_stable_tag(tag: str) -> tuple[int, int, int] | None:
    match = STABLE_TAG.fullmatch(tag)
    return tuple(map(int, match.groups())) if match else None


def select_latest_stable(tags: Iterable[str]) -> str | None:
    stable_tags = [(parse_stable_tag(tag), tag) for tag in tags]
    candidates = [(version, tag) for version, tag in stable_tags if version is not None]
    return max(candidates)[1] if candidates else None


def default_cache_file(
    system: str | None = None,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    system = system or platform.system()
    environ = environ if environ is not None else os.environ
    home = home or Path.home()
    if system == "Darwin":
        cache_dir = home / "Library" / "Caches"
    elif system == "Windows":
        cache_dir = Path(environ.get("LOCALAPPDATA", str(home / "AppData" / "Local")))
    else:
        cache_dir = Path(environ.get("XDG_CACHE_HOME", str(home / ".cache")))
    return cache_dir / "fuse-bead-designer" / "update-check.json"


def fetch_github_tags(repository: str, timeout: float) -> list[str]:
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repository}/tags",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "fuse-bead-designer-update-check/1",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list):
        raise ValueError("GitHub tags response is not an array")
    tags = []
    for item in payload:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise ValueError("GitHub tags response has no tag name")
        tags.append(item["name"])
    return tags


def read_cache(cache_file: Path, policy: UpdatePolicy) -> dict[str, object] | None:
    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    if not isinstance(data, dict) or set(data) != set(CACHE_FIELDS):
        raise ValueError("invalid update cache")
    if type(data["checked_at"]) is not int or data["checked_at"] < 0:
        raise ValueError("invalid update cache timestamp")
    if data["current_version"] != policy.current_version:
        raise ValueError("invalid update cache version")
    current = parse_stable_tag(f"v{policy.current_version}")
    latest = data["latest_version"]
    status = data["status"]
    if current is None:
        raise ValueError("invalid policy version")
    if status == "unavailable":
        if latest is not None:
            raise ValueError("invalid unavailable update cache")
    elif status in ("up-to-date", "update-available"):
        if not isinstance(latest, str) or (latest_version := parse_stable_tag(latest)) is None:
            raise ValueError("invalid update cache latest version")
        if status == "up-to-date" and latest_version > current:
            raise ValueError("invalid up-to-date update cache")
        if status == "update-available" and latest_version <= current:
            raise ValueError("invalid available update cache")
    else:
        raise ValueError("invalid update cache status")
    return data


def cache_lock_file(cache_file: Path) -> Path:
    return cache_file.with_name(f".{cache_file.name}.lock")


def acquire_cache_lock(cache_file: Path) -> Path | None:
    lock_file = cache_lock_file(cache_file)
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        while True:
            try:
                descriptor = os.open(
                    lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600
                )
            except FileExistsError:
                try:
                    if time.time() - lock_file.stat().st_mtime <= LOCK_STALE_SECONDS:
                        return None
                    lock_file.unlink()
                except FileNotFoundError:
                    continue
                continue
            try:
                os.write(descriptor, str(time.time()).encode("ascii"))
            finally:
                os.close(descriptor)
            return lock_file
    except OSError:
        return None


def release_cache_lock(lock_file: Path) -> None:
    try:
        lock_file.unlink()
    except OSError:
        pass


def unavailable_result(policy: UpdatePolicy, now: int) -> dict[str, object]:
    return {
        "status": "unavailable",
        "current_version": policy.current_version,
        "latest_version": None,
        "checked_at": now,
    }


def recent_result(
    policy: UpdatePolicy, cached: Mapping[str, object]
) -> dict[str, object]:
    return {
        "status": "recent",
        "current_version": policy.current_version,
        "latest_version": cached.get("latest_version"),
        "checked_at": cached["checked_at"],
    }


def compare_result(
    policy: UpdatePolicy, latest_version: str | None, now: int
) -> dict[str, object]:
    current = parse_stable_tag(f"v{policy.current_version}")
    latest = parse_stable_tag(latest_version) if latest_version else None
    if current is None or latest is None:
        raise ValueError("policy or GitHub response has no stable version")
    result: dict[str, object] = {
        "status": "up-to-date",
        "current_version": policy.current_version,
        "latest_version": latest_version,
        "checked_at": now,
    }
    if latest > current:
        result["status"] = "update-available"
        result["confirmation_prompt_zh"] = f"确认更新到 {latest_version}"
        result["confirmation_prompt_en"] = f"Confirm update to {latest_version}"
    return result


def persist_or_unavailable(
    cache_file: Path, result: dict[str, object]
) -> dict[str, object]:
    cache_result = {key: result.get(key) for key in CACHE_FIELDS}
    temporary_path: Path | None = None
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=cache_file.parent,
            prefix=f".{cache_file.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            json.dump(cache_result, stream, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
        temporary_path.replace(cache_file)
        return result
    except (OSError, ValueError, TypeError):
        return unavailable_result(
            UpdatePolicy("", str(result["current_version"]), "", 0),
            int(result["checked_at"]),
        )
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


def check_for_update(
    policy: UpdatePolicy,
    cache_file: Path,
    *,
    now: int,
    force: bool = False,
    fetcher: Callable[[str, float], list[str]] = fetch_github_tags,
    timeout: float = 2.0,
) -> dict[str, object]:
    try:
        cached = read_cache(cache_file, policy)
        cache_error = False
    except (OSError, ValueError, json.JSONDecodeError):
        cached = None
        cache_error = True
    if (
        not force
        and cached is not None
        and now - int(cached["checked_at"]) < policy.check_interval_seconds
    ):
        return recent_result(policy, cached)

    lock_file = acquire_cache_lock(cache_file)
    if lock_file is None:
        try:
            cached = read_cache(cache_file, policy)
        except (OSError, ValueError, json.JSONDecodeError):
            return unavailable_result(policy, now)
        if (
            not force
            and cached is not None
            and now - int(cached["checked_at"]) < policy.check_interval_seconds
        ):
            return recent_result(policy, cached)
        return unavailable_result(policy, now)

    try:
        if cache_error:
            return persist_or_unavailable(cache_file, unavailable_result(policy, now))
        try:
            cached = read_cache(cache_file, policy)
            if (
                not force
                and cached is not None
                and now - int(cached["checked_at"]) < policy.check_interval_seconds
            ):
                return recent_result(policy, cached)
            latest = select_latest_stable(fetcher(policy.repository, timeout))
            result = compare_result(policy, latest, now)
        except (OSError, TimeoutError, ValueError, json.JSONDecodeError):
            result = unavailable_result(policy, now)
        return persist_or_unavailable(cache_file, result)
    finally:
        release_cache_lock(lock_file)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY_FILE)
    parser.add_argument("--cache-file", type=Path)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--timeout", type=float, default=2.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    now = int(time.time())
    policy: UpdatePolicy | None = None
    try:
        policy = load_policy(arguments.policy)
        result = check_for_update(
            policy,
            arguments.cache_file or default_cache_file(),
            now=now,
            force=arguments.force,
            timeout=arguments.timeout,
        )
    except (OSError, TimeoutError, ValueError, json.JSONDecodeError):
        result = unavailable_result(
            policy or UpdatePolicy("", "", "", 0), now
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
