import ast
import importlib.util
import json
from pathlib import Path
import sys

import pytest


SCRIPT = Path(
    "plugins/fuse-bead-designer/skills/create-fuse-bead-patterns/"
    "scripts/check_update.py"
)
POLICY = SCRIPT.parent.parent / "update-policy.json"
spec = importlib.util.spec_from_file_location("fuse_bead_update_check", SCRIPT)
update_check = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = update_check
spec.loader.exec_module(update_check)
POLICY_OBJECT = update_check.UpdatePolicy(
    repository="MrLQQ/fuse-bead-designer",
    current_version="0.3.1",
    stable_tag_pattern="vMAJOR.MINOR.PATCH",
    check_interval_seconds=86400,
)


def test_select_latest_stable_is_numeric_and_ignores_non_stable_tags():
    assert update_check.select_latest_stable(
        ["v0.9.9", "v0.10.0", "v0.11.0-rc.1", "latest", "v1.0"]
    ) == "v0.10.0"


def test_packaged_policy_is_v031():
    policy = update_check.load_policy(POLICY)

    assert policy.repository == "MrLQQ/fuse-bead-designer"
    assert policy.current_version == "0.3.1"
    assert policy.stable_tag_pattern == "vMAJOR.MINOR.PATCH"
    assert policy.check_interval_seconds == 86400


def test_recent_cache_skips_fetch(tmp_path):
    cache = tmp_path / "update.json"
    cache.write_text(
        json.dumps(
            {
                "checked_at": 100,
                "current_version": "0.3.1",
                "latest_version": "v0.3.1",
                "status": "up-to-date",
            }
        ),
        encoding="utf-8",
    )
    calls = []

    result = update_check.check_for_update(
        POLICY_OBJECT,
        cache,
        now=100 + 86399,
        fetcher=lambda repository, timeout: calls.append(repository),
    )

    assert result["status"] == "recent"
    assert calls == []


def test_exact_interval_boundary_fetches_again(tmp_path):
    cache = tmp_path / "update.json"
    cache.write_text(
        json.dumps(
            {
                "checked_at": 100,
                "current_version": "0.3.1",
                "latest_version": "v0.3.1",
                "status": "up-to-date",
            }
        ),
        encoding="utf-8",
    )
    calls = []

    result = update_check.check_for_update(
        POLICY_OBJECT,
        cache,
        now=100 + 86400,
        fetcher=lambda repository, timeout: calls.append(repository) or ["v0.3.1"],
    )

    assert result["status"] == "up-to-date"
    assert calls == ["MrLQQ/fuse-bead-designer"]


def test_force_bypasses_a_recent_cache(tmp_path):
    cache = tmp_path / "update.json"
    cache.write_text(
        json.dumps(
            {
                "checked_at": 100,
                "current_version": "0.3.1",
                "latest_version": "v0.3.1",
                "status": "up-to-date",
            }
        ),
        encoding="utf-8",
    )

    result = update_check.check_for_update(
        POLICY_OBJECT,
        cache,
        now=101,
        force=True,
        fetcher=lambda repository, timeout: ["v0.4.0"],
    )

    assert result["status"] == "update-available"
    assert result["latest_version"] == "v0.4.0"


def test_newer_stable_tag_returns_localized_confirmation(tmp_path):
    result = update_check.check_for_update(
        POLICY_OBJECT,
        tmp_path / "update.json",
        now=200,
        fetcher=lambda repository, timeout: ["v0.3.1", "v0.4.0"],
    )

    assert result["status"] == "update-available"
    assert result["latest_version"] == "v0.4.0"
    assert result["confirmation_prompt_zh"] == "确认更新到 v0.4.0"
    assert result["confirmation_prompt_en"] == "Confirm update to v0.4.0"


def test_current_stable_tag_is_up_to_date(tmp_path):
    result = update_check.check_for_update(
        POLICY_OBJECT,
        tmp_path / "update.json",
        now=200,
        fetcher=lambda repository, timeout: ["v0.3.1", "v0.3.0"],
    )

    assert result == {
        "status": "up-to-date",
        "current_version": "0.3.1",
        "latest_version": "v0.3.1",
        "checked_at": 200,
    }


@pytest.mark.parametrize(
    "failure", [TimeoutError(), OSError("offline"), ValueError("bad json")]
)
def test_expected_failures_are_unavailable_and_cached(tmp_path, failure):
    def fail(repository, timeout):
        raise failure

    cache = tmp_path / "update.json"
    result = update_check.check_for_update(POLICY_OBJECT, cache, now=300, fetcher=fail)

    assert result["status"] == "unavailable"
    assert set(json.loads(cache.read_text(encoding="utf-8"))) <= {
        "checked_at",
        "current_version",
        "latest_version",
        "status",
    }


def test_fetch_github_tags_rejects_malformed_and_rate_limited_responses(monkeypatch):
    class Response:
        def __init__(self, payload):
            self.payload = payload

        def read(self):
            return self.payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

    for payload in (b'{"message": "API rate limit exceeded"}', b'[{"id": 1}]'):
        monkeypatch.setattr(
            update_check.urllib.request,
            "urlopen",
            lambda request, timeout: Response(payload),
        )

        with pytest.raises(ValueError):
            update_check.fetch_github_tags("MrLQQ/fuse-bead-designer", 2.0)


def test_unwritable_cache_returns_unavailable(tmp_path):
    result = update_check.check_for_update(
        POLICY_OBJECT,
        tmp_path,
        now=300,
        fetcher=lambda repository, timeout: ["v0.3.1"],
    )

    assert result["status"] == "unavailable"


@pytest.mark.parametrize(
    ("system", "environ", "home", "expected"),
    [
        ("Darwin", {}, Path("/Users/fuse"), Path("/Users/fuse/Library/Caches/fuse-bead-designer/update-check.json")),
        ("Linux", {"XDG_CACHE_HOME": "/var/cache/fuse"}, Path("/home/fuse"), Path("/var/cache/fuse/fuse-bead-designer/update-check.json")),
        ("Linux", {}, Path("/home/fuse"), Path("/home/fuse/.cache/fuse-bead-designer/update-check.json")),
        ("Windows", {"LOCALAPPDATA": "/local-app-data"}, Path("/Users/fuse"), Path("/local-app-data/fuse-bead-designer/update-check.json")),
    ],
)
def test_default_cache_file_uses_platform_cache_location(system, environ, home, expected):
    assert update_check.default_cache_file(system, environ, home) == expected


def test_cli_cache_failure_prints_one_unavailable_json_object(tmp_path, capsys):
    exit_code = update_check.main(["--cache-file", str(tmp_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert "Traceback" not in captured.out
    assert captured.out.count("\n") == 1
    assert json.loads(captured.out)["status"] == "unavailable"


def test_checker_and_tests_never_import_or_call_subprocess():
    for path in (SCRIPT, Path(__file__)):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assert not any(
            isinstance(node, (ast.Import, ast.ImportFrom))
            and any(alias.name == "subprocess" for alias in node.names)
            for node in ast.walk(tree)
        )
        assert not any(
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "subprocess"
            for node in ast.walk(tree)
        )
