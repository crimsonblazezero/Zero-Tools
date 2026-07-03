// tts.mjs — multi-provider TTS for the media audio engine. The provider chain,
// auto-detected from env, is the one documented in ../SKILL.md:
//
//   1. HeyGen (Starfish)  — $HEYGEN_API_KEY / $HYPERFRAMES_API_KEY / ~/.heygen.
//        Direct v3 REST (NOT `hyperframes tts`, which in the published build is
//        Kokoro-only and silently ignores a HeyGen key). Returns word_timestamps
//        in the same call, so no separate transcribe pass.
//   2. ElevenLabs         — $ELEVENLABS_API_KEY + `pip install elevenlabs`. No
//        word timings → caller chains transcribeWav().
//   3. Kokoro-82M (local) — always available, via the published `hyperframes tts`
//        CLI. No word timings → caller chains transcribeWav().
//
// "HeyGen available" is decided by CREDENTIAL presence (heygenCredential), never
// by the CLI — see the note above.

import { spawn, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir, homedir } from "node:os";
import { dirname, join } from "node:path";
import { heygenAuthHeaders, heygenCredential, heygenJSON } from "./heygen.mjs";

// ── provider detection ────────────────────────────────────────────────────────
export function heygenAvailable() {
  return heygenCredential() !== null;
}
export function elevenlabsAvailable() {
  if (!process.env.ELEVENLABS_API_KEY) return false;
  const r = spawnSync("python3", ["-c", "import elevenlabs"], { stdio: "ignore" });
  return r.status === 0;
}

// First available provider wins; an explicit choice is honored (and validated).
export function pickProvider(userProvider) {
  if (userProvider) {
    if (!["heygen", "elevenlabs", "kokoro", "minimax", "edge"].includes(userProvider))
      throw new Error(`invalid provider "${userProvider}" (heygen | elevenlabs | kokoro | minimax | edge)`);
    if (userProvider === "heygen" && !heygenAvailable())
      throw new Error(
        "provider=heygen but no HeyGen credentials (set $HEYGEN_API_KEY or run `hyperframes auth login`)",
      );
    if (userProvider === "elevenlabs" && !process.env.ELEVENLABS_API_KEY)
      throw new Error("provider=elevenlabs but $ELEVENLABS_API_KEY is not set");
    if (userProvider === "minimax" && !process.env.MINIMAX_API_KEY)
      throw new Error("provider=minimax but $MINIMAX_API_KEY is not set");
    return userProvider;
  }
  return heygenAvailable() ? "heygen" : elevenlabsAvailable() ? "elevenlabs" : process.env.MINIMAX_API_KEY ? "minimax" : "edge";
}

// ── voice resolution ──────────────────────────────────────────────────────────
// HeyGen /v3/voices/speech only accepts STARFISH voice_ids; auto-pick the first
// English public starfish voice when none is pinned. ElevenLabs/Kokoro have
// their own defaults.
export async function resolveVoiceId({ provider, userVoice, lang = "en" }) {
  if (userVoice) return userVoice;
  if (provider === "elevenlabs") return "21m00Tcm4TlvDq8ikWAM"; // Rachel
  if (provider === "minimax") return "female-yujie"; // Default premium Chinese voice
  if (provider === "edge") return "zh-CN-YunxiNeural"; // Default premium free Chinese voice
  if (provider === "kokoro") {
    if (lang === "en") return "am_michael";
    throw new Error("Kokoro non-English needs an explicit --voice (see references/tts.md)");
  }
  // heygen
  const payload = await heygenJSON(`/voices?engine=starfish&type=public&limit=50`, {
    headers: heygenAuthHeaders(),
  });
  const voices = payload.data ?? payload.voices ?? [];
  const pick = voices.find((v) => v.language === "English") ?? voices[0];
  if (!pick) throw new Error("no public starfish voice to default to — pass --voice");
  return pick.voice_id;
}

// ── helpers ─────────────────────────────────────────────────────────────────
export function withWordIds(words) {
  return (words ?? []).map((w, i) => ({ id: `w${i}`, text: w.text, start: w.start, end: w.end }));
}

export function ffprobeDuration(absPath) {
  const r = spawnSync(
    "ffprobe",
    ["-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", absPath],
    { encoding: "utf8" },
  );
  if (r.status !== 0) return NaN;
  return parseFloat(String(r.stdout).trim());
}

function spawnP(cmd, args, opts) {
  const isWin = process.platform === "win32";
  const actualCmd = isWin && cmd === "npx" ? "npx.cmd" : cmd;
  const actualOpts = isWin && actualCmd === "npx.cmd" ? { shell: true, ...opts } : opts;
  console.log(`[spawnP] Spawning: ${actualCmd} ${args.join(" ")}`);
  return new Promise((resolve) => {
    const p = spawn(actualCmd, args, { stdio: "pipe", ...actualOpts });
    let errStr = "";
    let outStr = "";
    if (p.stderr) {
      p.stderr.on("data", (data) => {
        errStr += data.toString();
      });
    }
    if (p.stdout) {
      p.stdout.on("data", (data) => {
        outStr += data.toString();
      });
    }
    p.on("exit", (code) => {
      console.log(`[spawnP] Exited with code ${code}.\nStdout: ${outStr.trim()}\nStderr: ${errStr.trim()}`);
      resolve({ status: code ?? -1 });
    });
    p.on("error", (err) => {
      console.error(`[spawnP] Error spawning: ${err.message}`);
      resolve({ status: -1 });
    });
  });
}

// mp3/whatever bytes → wav 44.1k mono at destWav (ffmpeg detects true format).
function transcodeToWav(bytes, destWav) {
  const td = mkdtempSync(join(tmpdir(), "hf-tts-"));
  const tmp = join(td, "a.mp3");
  writeFileSync(tmp, bytes);
  mkdirSync(dirname(destWav), { recursive: true });
  const ff = spawnSync(
    "ffmpeg",
    ["-y", "-loglevel", "error", "-i", tmp, "-ar", "44100", "-ac", "1", destWav],
    { stdio: "ignore" },
  );
  rmSync(td, { recursive: true, force: true });
  return ff.status === 0 && existsSync(destWav);
}

const ELEVENLABS_PY = `
import os, sys
from elevenlabs.client import ElevenLabs
from elevenlabs import save
client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
text = open(sys.argv[1]).read()
audio = client.text_to_speech.convert(
    text=text, voice_id=sys.argv[2],
    model_id="eleven_multilingual_v2", output_format="mp3_44100_128",
)
save(audio, sys.argv[3])
`;

// ── synthesize one line ───────────────────────────────────────────────────────
// Writes wav at wavAbs. Returns { ok, words } — words is the raw
// [{text,start,end}] array for HeyGen (native), or null for ElevenLabs/Kokoro
// (caller must transcribeWav). Never throws; failures return { ok:false }.
async function synthesizeMinimax({ text, voiceId, lang, speed, wavAbs }) {
  try {
    const apiKey = process.env.MINIMAX_API_KEY;
    if (!apiKey) return { ok: false, words: null };
    
    const url = "https://api.minimax.chat/v1/t2a_v2";
    const payload = {
      model: "speech-01",
      text: text,
      stream: false,
      voice_setting: {
        voice_id: voiceId || "female-yujie",
        speed: speed || 1.0,
        pitch: 0,
        volume: 1.0
      },
      audio_setting: {
        audio_sample_rate: 24000,
        format: "mp3"
      }
    };
    
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${apiKey}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });
    
    if (!res.ok) {
      console.error(`[MiniMax TTS] API Error: ${res.status} ${res.statusText}`);
      return { ok: false, words: null };
    }
    
    const bytes = Buffer.from(await res.arrayBuffer());
    if (wavAbs.endsWith(".wav")) {
      if (!transcodeToWav(bytes, wavAbs)) return { ok: false, words: null };
    } else {
      mkdirSync(dirname(wavAbs), { recursive: true });
      writeFileSync(wavAbs, bytes);
    }
    return { ok: true, words: null };
  } catch (e) {
    console.error(`[MiniMax TTS] error:`, e);
    return { ok: false, words: null };
  }
}

async function synthesizeEdge({ text, voiceId, lang, speed, wavAbs, hyperframesDir }) {
  try {
    const python = process.platform === "win32" ? "python" : "python3";
    const scriptPath = join(hyperframesDir, "videos", "ad-panel-intro", "synth-edge.py");
    
    // Ensure output directory exists
    mkdirSync(dirname(wavAbs), { recursive: true });
    
    const r = await spawnP(
      python,
      [scriptPath, text, voiceId || "zh-CN-YunxiNeural", wavAbs],
      {}
    );
    return { ok: r.status === 0 && existsSync(wavAbs), words: null };
  } catch (e) {
    console.error(`[Edge TTS] error:`, e);
    return { ok: false, words: null };
  }
}

export async function synthesizeOne({
  provider,
  text,
  voiceId,
  lang = "en",
  speed = 1.0,
  wavAbs,
  hyperframesDir,
}) {
  if (provider === "heygen") return synthesizeHeygen({ text, voiceId, lang, speed, wavAbs });
  if (provider === "minimax") return synthesizeMinimax({ text, voiceId, lang, speed, wavAbs });
  if (provider === "edge") return synthesizeEdge({ text, voiceId, lang, speed, wavAbs, hyperframesDir });
  if (provider === "elevenlabs") {
    const r = await spawnP(
      "python3",
      ["-c", ELEVENLABS_PY, writeTmpText(text), voiceId, wavAbs],
      {},
    );
    return { ok: r.status === 0 && existsSync(wavAbs), words: null };
  }
  // kokoro — call python directly to avoid npx command parsing and path bugs on Windows
  const home = homedir();
  let scriptPath = join(home, ".cache", "hyperframes", "tts", "synth-v2.py");
  if (hyperframesDir) {
    const localScript = join(hyperframesDir, "videos", "ad-panel-intro", "synth-cmn.py");
    if (existsSync(localScript)) {
      scriptPath = localScript;
    }
  }
  const modelPath = join(home, ".cache", "hyperframes", "tts", "models", "kokoro-v1.0.onnx");
  const voicesPath = join(home, ".cache", "hyperframes", "tts", "voices", "voices-v1.0.bin");
  
  // Ensure output directory exists
  mkdirSync(dirname(wavAbs), { recursive: true });
  
  const python = process.platform === "win32" ? "python" : "python3";
  const r = await spawnP(
    python,
    [scriptPath, modelPath, voicesPath, text, voiceId, String(speed), wavAbs, lang],
    {}
  );
  return { ok: r.status === 0 && existsSync(wavAbs), words: null };
}

async function synthesizeHeygen({ text, voiceId, lang, speed, wavAbs }) {
  try {
    const body = { text, voice_id: voiceId, speed };
    if (lang !== "en") body.language = lang;
    const payload = await heygenJSON(`/voices/speech`, {
      method: "POST",
      headers: heygenAuthHeaders(),
      body,
    });
    const inner = payload.data ?? payload;
    if (!inner.audio_url) return { ok: false, words: null };
    const res = await fetch(inner.audio_url);
    if (!res.ok) return { ok: false, words: null };
    const bytes = Buffer.from(await res.arrayBuffer());
    // .wav output → transcode to 44.1k mono; .mp3 → raw bytes (no ffmpeg). The
    // engine always asks for .wav; the standalone heygen-tts CLI may ask for .mp3.
    if (wavAbs.endsWith(".wav")) {
      if (!transcodeToWav(bytes, wavAbs)) return { ok: false, words: null };
    } else {
      mkdirSync(dirname(wavAbs), { recursive: true });
      writeFileSync(wavAbs, bytes);
    }
    const words = Array.isArray(inner.word_timestamps)
      ? inner.word_timestamps
          .filter((w) => w && typeof w.word === "string" && isFinite(w.start) && isFinite(w.end))
          .filter((w) => !/^<.*>$/.test(w.word.trim())) // drop <start>/<end> sentinels
          .map((w) => ({ text: w.word, start: w.start, end: w.end }))
      : [];
    return { ok: true, words };
  } catch {
    return { ok: false, words: null };
  }
}

// ElevenLabs/Kokoro have no word timings — run Whisper over the wav. Returns the
// flat [{id,text,start,end}] word array, or null. Each call uses a throwaway
// --dir so parallel scenes don't collide on transcript.json.
export async function transcribeWav({ wavRel, lang = "en", hyperframesDir }) {
  return null; // Bypass Whisper transcription to avoid downloading large models on Windows
  const model = lang === "en" ? "small.en" : "small";
  const td = mkdtempSync(join(tmpdir(), "hf-trans-"));
  const args = ["hyperframes", "transcribe", wavRel, "--model", model, "--dir", td];
  if (lang !== "en") args.push("--language", lang);
  const r = await spawnP("npx", args, { cwd: hyperframesDir });
  let words = null;
  if (r.status === 0) {
    const src = join(td, "transcript.json");
    if (existsSync(src)) {
      try {
        const arr = JSON.parse(readFileSync(src, "utf8"));
        if (Array.isArray(arr) && arr.length) words = arr;
      } catch {}
    }
  }
  rmSync(td, { recursive: true, force: true });
  return words;
}

// ── tiny local utils ──────────────────────────────────────────────────────────
function writeTmpText(text) {
  const td = mkdtempSync(join(tmpdir(), "hf-txt-"));
  const p = join(td, "line.txt");
  writeFileSync(p, text);
  return p;
}
function relTo(base, abs) {
  return abs.startsWith(base + "/") ? abs.slice(base.length + 1) : abs;
}
