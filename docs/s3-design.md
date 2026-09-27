# s3 design — installable CLI

## Goal

`pipx install git+https://github.com/khursani8/wayang` (or
`uv tool install`) gives a global `wayang` command. No clone, no
`uv run`.

## Package layout

    pyproject.toml              [project] name=wayang, scripts entry
    src/wayang/cli.py           main() + argparse (moved from tools/wayang.py)
    src/wayang/project.py       loading/merge (from tools/project.py)
    src/wayang/render_checks.py lint + duration guard (from wayang.py)
    src/wayang/tts_providers.py (moved)
    src/wayang/paths.py         resource resolution (below)
    src/wayang/packages/templates/   the 5 templates (package data)
    src/wayang/packages/schema/      project.schema.json (package data)
    src/wayang/packages/backgrounds/ 11 theme PNGs (package data)
    vendors/                    stays repo-only: engines are cloned by setup

## Resource resolution (paths.py)

WAYANG_HOME = env WAYANG_HOME > ~/.wayang.

- package data (templates, schema, backgrounds): importlib.resources from
  the installed package.
- engines: WAYANG_HOME/vendors/<engine>/ — `wayang setup` copies engine
  sources from package data (remotion engine src+configs, hyperframes
  mapper scripts) and runs npm install there.
- user projects: always created in the CURRENT working directory
  (projects/<name>/). User data never goes inside the install.

## Commands gained

- `wayang setup` — create WAYANG_HOME, deploy vendor engines, npm install
  (remotion engine), verify.
- `wayang doctor` — report node/npm/ffmpeg/ffprobe versions, TTS keys
  present or missing, engines deployed or not, with fix hints.

## Render flow from a user directory

`wayang render demo` (run inside ~/my-videos with projects/demo/):
workdir at WAYANG_HOME/.work/<project>/, vendor build.sh invoked from
WAYANG_HOME/vendors/<engine>/, output + timeline.json +
expected-seconds.txt into the project's out/. Same guards as always.

## Repo-local dev compatibility

tools/wayang.py becomes a thin shim calling wayang.cli.main() so every
existing in-repo command keeps working unchanged. Vendor engines stay in
the repo for development.

## Acceptance (all must pass)

1. Fresh venv: `uv tool install /mnt/data/work/wayang` succeeds.
2. `cd $(mktemp -d) && wayang templates` lists the five formats.
3. `wayang init tutorial demo && wayang check demo` reports READY notes.
4. `wayang doctor` lists node/npm/ffmpeg/keys status with hints.
5. With node + key: `wayang render demo` produces demo/out/video.mp4.
6. In the REPO: `uv run tools/wayang.py templates` still works (shim).
