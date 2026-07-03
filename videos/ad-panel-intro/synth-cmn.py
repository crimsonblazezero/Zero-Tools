import sys, os, json, inspect

# On Windows, hook espeak-ng-loader before importing kokoro
if os.name == 'nt':
    try:
        import espeakng_loader
        os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = espeakng_loader.get_library_path()
        os.environ["ESPEAK_DATA_PATH"] = espeakng_loader.get_data_path()
    except Exception as e:
        print("Warning: failed to load espeakng_loader:", e, file=sys.stderr)

model_path = sys.argv[1]
voices_path = sys.argv[2]
text = sys.argv[3]
voice = sys.argv[4]
speed = float(sys.argv[5])
output_path = sys.argv[6]
lang = sys.argv[7] if len(sys.argv) > 7 else ""

# Map 'zh' to 'cmn'
if lang == 'zh' or lang.startswith('zh'):
    lang = 'cmn'

import kokoro_onnx
import soundfile as sf

model = kokoro_onnx.Kokoro(model_path, voices_path)

kwargs = {"voice": voice, "speed": speed}
supports_lang = "lang" in inspect.signature(model.create).parameters
if lang and supports_lang:
    kwargs["lang"] = lang

samples, sample_rate = model.create(text, **kwargs)
sf.write(output_path, samples, sample_rate)

duration = len(samples) / sample_rate
print(json.dumps({
    "outputPath": output_path,
    "sampleRate": sample_rate,
    "durationSeconds": round(duration, 3),
    "langApplied": bool(lang and supports_lang),
}))
