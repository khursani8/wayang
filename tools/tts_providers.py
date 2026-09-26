"""TTS providers for Wayang.

The repo owns no services. Every engine is an API client the user points at
their own endpoint or a hosted API.
"""
import hashlib
import json
import logging
import os
import urllib.error
import urllib.request
import wave

log = logging.getLogger("ce.tts")


class ProviderError(RuntimeError):
    """A configured TTS API call failed."""


def wav_seconds(path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def line_hash(text: str, engine: str, params: dict) -> str:
    payload = json.dumps({"text": text, "engine": engine, "params": params}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


class OpenAIProvider:
    name = "openai"
    ENDPOINT = "https://api.openai.com/v1/audio/speech"

    def available(self):
        if os.environ.get("OPENAI_API_KEY"):
            return True, ""
        return False, "OPENAI_API_KEY is not set"

    def config_hash(self, cfg: dict) -> dict:
        return {k: cfg.get(k) for k in ("voice", "model", "speed", "instructions")}

    def synthesize(self, text: str, cfg: dict, out_path) -> None:
        payload = {
            "model": cfg.get("model", "gpt-4o-mini-tts"),
            "voice": cfg["voice"],
            "input": text,
            "response_format": "wav",
        }
        if cfg.get("speed") is not None:
            payload["speed"] = cfg["speed"]
        if cfg.get("instructions"):
            payload["instructions"] = cfg["instructions"]
        req = urllib.request.Request(
            self.ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                audio = resp.read()
        except urllib.error.HTTPError as e:
            raise ProviderError(f"openai tts http {e.code}: {e.read().decode(errors='replace')[:300]}") from e
        except urllib.error.URLError as e:
            raise ProviderError(f"openai tts connection error: {e.reason}") from e
        out_path.write_bytes(audio)


class RevolabProvider:
    name = "revolab"
    ENDPOINT = "https://api.revolab.ai/v1/tts"

    def available(self):
        if os.environ.get("REVOLAB_API_KEY"):
            return True, ""
        return False, "REVOLAB_API_KEY is not set"

    def config_hash(self, cfg: dict) -> dict:
        return {k: cfg.get(k) for k in ("voice_id", "model", "speed")}

    def synthesize(self, text: str, cfg: dict, out_path) -> None:
        payload = {
            "model": cfg.get("model", "nada-1.0-pro"),
            "text": text,
            "voice_id": cfg["voice_id"],
        }
        if cfg.get("speed") is not None:
            payload["speed"] = cfg["speed"]
        req = urllib.request.Request(
            self.ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {os.environ['REVOLAB_API_KEY']}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                audio = resp.read()
        except urllib.error.HTTPError as e:
            raise ProviderError(f"revolab http {e.code}: {e.read().decode(errors='replace')[:300]}") from e
        except urllib.error.URLError as e:
            raise ProviderError(f"revolab tts connection error: {e.reason}") from e
        out_path.write_bytes(audio)


PROVIDERS = {p.name: p for p in (OpenAIProvider(), RevolabProvider())}
