CONTEXT: Building "content_engine", a framework-agnostic video-template platform.
User picks a template (education, community), fills ONE canonical YAML, and an agent renders a video by reading the target engine's manual at vendors/<engine>/AGENTS.md. First engine: Remotion+VOICEVOX repo (inputs: config/script.yaml, characters.yaml, defaults.yaml, video-settings.yaml; sync scripts map YAML -> src/data/script.ts + settings.generated.ts; generate-voices.ts calls VOICEVOX at localhost:50021 for wav + durations.json; render -> out/video.mp4).

PROPOSED STRUCTURE:
content_engine/
  AGENTS.md                    # platform manual for agents: concepts, flow, contracts
  schema/project.schema.json   # canonical YAML JSON Schema
  templates/education/{template.yaml,README.md,assets/}
  templates/community/{template.yaml,README.md,assets/}
  vendors/remotion/{AGENTS.md,engine/(ported repo),build.sh}
  tools/ce.py                  # thin CLI: init / validate / render dispatch
  projects/<name>/project.yaml + assets/

CANONICAL YAML (single file per project):
meta: {title, template, vendor, language}
characters: {id: {name, color, position, voice: {engine, speaker_id}}}
script: [{id, character, text, scene, pause_after, visual?, se?}]
settings: {video: {width, height, fps}, subtitle/font passthrough}
vendor: {} # engine-specific extras, documented in the vendor AGENTS.md

QUESTIONS (answer as numbered list, max 120 words each):
1. Canonical shared schema + per-vendor mapping, vs per-vendor YAML? Why?
2. Scene timing: engine derives from voice durations. What is the right no-TTS fallback and its pitfalls?
3. What breaks when adding a second engine (motion-canvas, moviepy)? What must vendor AGENTS.md pin down so vendors stay interchangeable?
4. Single-file canonical YAML vs split files (script/characters/settings)?
