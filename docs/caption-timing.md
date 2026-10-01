# Caption upload timing — read before inserting captions at upload time

Found 2026-10-01 by the YouTube agent (ljitdsmo session), verified by isolation:
YouTube REJECTS captions.insert on hours-old uploads with a misleading 400
"invalid metadata values" error naming snippet.language/name/videoId. The video
is fine; the error lies. Same binary, same SRT, same flags succeed on a 1-day-old
video and fail on a 30-minute-old one.

Rules for wayang publish flows:
1. Do NOT insert captions in the same session as the upload. Emit the kit
   (captions.srt included) and schedule the caption insert for later.
2. yutu runs the caption file read inside an fs.FS sandbox under its working
   directory: the file path must be relative and inside YUTU_ROOT/cwd, or the
   insert fails with "path escapes from parent" (see also the credential-path
   quirk, same fs.FS family).
3. Validate first: captions.list until the auto track appears, or just retry
   after ~12h. YouTube auto-captions cover the gap on speech-heavy videos.

Isolation evidence: minimal 1-cue SRT, ms and en, rejected identically on
video jIKFm7nwyr8-successor 7w7RK5txfDE at ~30 min age; identical command
inserted a named track on iHr8vLYL440 at ~18h age the day before.
