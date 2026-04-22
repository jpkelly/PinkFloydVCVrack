#!/usr/bin/env python3
"""
Build a VCV Rack 2 patch that emulates the background sounds from
Pink Floyd's "On the Run" (Dark Side of the Moon).

Output: ./Pink Floyd.vcv  (zstd-compressed tar archive containing patch.json)

Uses only FREE plugins from the VCV Library:
  - VCV Fundamental           (core signal chain; known port IDs)
  - Erica Synths  (EricaCopies/BlackWaveTableVCO, BlackOctasource, FusionDelay)
  - Bastl         (BastlPizza/Pizza)

The Fundamental chain is fully cabled. The Bastl/Erica modules are placed in
the rack unconnected (their port IDs aren't published in open source), ready
for you to wire up in-app. See README.md for the signal flow and how to swap
the Fundamental VCO/Delay for the Erica equivalents.
"""
from __future__ import annotations
import json, os, subprocess, shutil, tempfile, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
OUT_VCV = ROOT / "Pink Floyd.vcv"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def v(semitones_from_C4: float) -> float:
    """Convert semitones-from-C4 to 1V/oct voltage."""
    return semitones_from_C4 / 12.0

# Note voltages (1V/oct, C4 = 0V)
C4, D4, E4, F4, Fs4, G4, A4, B4 = 0, 2, 4, 5, 6, 7, 9, 11
C5, D5, E5 = 12, 14, 16

# ---------------------------------------------------------------------------
# Module factory
# ---------------------------------------------------------------------------
_next_id = 0
def nid():
    global _next_id
    i = _next_id
    _next_id += 1
    return i

def mod(plugin, model, pos, params=None, data=None, version="2.0.0"):
    m = {
        "id": nid(),
        "plugin": plugin,
        "model": model,
        "version": version,
        "pos": list(pos),
        "params": [{"id": k, "value": float(val)} for k, val in (params or {}).items()],
    }
    if data is not None:
        m["data"] = data
    return m

def cable(src_id, src_port, dst_id, dst_port, color="#fc2d5a"):
    return {
        "id": nid(),
        "outputModuleId": src_id,
        "outputId": src_port,
        "inputModuleId": dst_id,
        "inputId": dst_port,
        "color": color,
    }

# ---------------------------------------------------------------------------
# Core signal chain — VCV Fundamental (port/param IDs verified from source)
# ---------------------------------------------------------------------------
# Layout: row 0, left to right, in HP units.
# SEQ3 ~ 22hp | VCO 10 | VCF 8 | ADSR 10 | VCA 8 | Mixer 10 | Delay 10 | Noise 3 | LFO 10

# --- SEQ3 (22hp) -----------------------------------------------------------
# Params:
#   0 TEMPO  (display = 60 * 2^param bpm)   -> want ~660 bpm (11 Hz, fast 16ths)
#   3 STEPS                                 -> 8
#   4..11  CV row 1 step 1..8               -> the pitch pattern
#   28..35 GATE buttons (bool-ish)          -> all on (1.0)
# The "On the Run" pulse: an 8-step running figure in E minor, approx.
# E4 A4 G4 A4 E4 D4 G4 E4
seq_notes = [E4, A4, G4, A4, E4, D4, G4, E4]
seq_params = {
    0: 3.459,   # TEMPO: log2(11 Hz) so bpm ≈ 60*11 = 660 -> 16ths at ~165 bpm feel
    1: 0.0,     # RUN button (momentary)
    2: 0.0,     # RESET button
    3: 8.0,     # STEPS = 8
    36: 1.0,    # TEMPO_CV attenuator
    37: 1.0,    # STEPS_CV attenuator
    38: 0.0,    # CLOCK button
}
for i, n in enumerate(seq_notes):
    seq_params[4 + i] = v(n)          # row 1 CV = pitch (V)
    seq_params[12 + i] = 0.0          # row 2 CV (unused)
    seq_params[20 + i] = 0.0          # row 3 CV (unused)
    # NOTE: gate buttons MUST be 0.0 on load. They're BooleanTriggers — a non-
    # zero saved value causes a 0->1 transition on the first process() call,
    # which *toggles* that step's gate off (wiping out our data.gates=[1]*8).
    seq_params[28 + i] = 0.0

seq3 = mod("Fundamental", "SEQ3", (0, 0), seq_params,
           data={"running": True, "gates": [1]*8, "clockPassthrough": False})

# --- VCO (10hp) ------------------------------------------------------------
# ParamIds: 0 MODE(removed) 1 SYNC 2 FREQ 3 FINE(removed) 4 FM 5 PW 6 PW_CV 7 LINEAR
# In: 0 PITCH 1 FM 2 SYNC 3 PW | Out: 0 SIN 1 TRI 2 SAW 3 SQR
vco = mod("Fundamental", "VCO", (22, 0), {
    1: 1.0,    # hard sync mode (unused)
    2: 0.0,    # FREQ knob = C4 center; pitch set by 1V/oct CV from SEQ3
    4: 0.0,    # FM amount
    5: 0.5,    # PW
    6: 0.0,    # PW CV
    7: 0.0,    # 1V/octave mode (not linear)
})

# --- VCF (8hp) -------------------------------------------------------------
# Params: 0 FREQ 1 FINE(removed) 2 RES 3 FREQ_CV 4 DRIVE 5 RES_CV 6 DRIVE_CV
# In: 0 FREQ 1 RES 2 DRIVE 3 IN | Out: 0 LPF 1 HPF
vcf = mod("Fundamental", "VCF", (32, 0), {
    0: 0.35,   # base cutoff low; envelope sweeps it open on each note
    2: 0.55,   # resonance — enough to sing but not self-oscillate
    3: 0.65,   # env-to-cutoff amount (the VCS3-ish plucky sweep)
    4: 0.10,   # a touch of drive for body
    5: 0.0,    # res CV atten
    6: 0.0,    # drive CV atten
})

# --- ADSR (10hp) -----------------------------------------------------------
# Params: 0 A 1 D 2 S 3 R  4..7 CV attens  8 PUSH
# In: 0 A 1 D 2 S 3 R 4 GATE 5 RETRIG | Out: 0 ENV
adsr = mod("Fundamental", "ADSR", (40, 0), {
    0: 0.02,   # snappy attack
    1: 0.35,   # short decay — tight pluck
    2: 0.00,   # no sustain (percussive)
    3: 0.20,   # short release
    4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0,
    8: 0.0,    # push button (BooleanTrigger — keep 0)
})

# --- VCA (legacy, 8hp) -----------------------------------------------------
# Params: 0 LEVEL1 1 LEVEL2
# In: 0 EXP1 1 LIN1 2 IN1 3 EXP2 4 LIN2 5 IN2 | Out: 0 OUT1 1 OUT2
vca = mod("Fundamental", "VCA", (50, 0), {0: 1.0, 1: 1.0})

# --- VCMixer (10hp) --------------------------------------------------------
# Params: 0 MIX_LVL  1..4 CH LVLs
# In: 0 MIX_CV  1..4 CH_IN  5..8 CV_IN | Out: 0 MIX  1..4 CH_OUT
mixer = mod("Fundamental", "VCMixer", (58, 0), {
    0: 0.85,   # master (a hair below unity to avoid clipping into delay)
    1: 1.0,    # ch1 dry sequence = lead voice
    2: 0.30,   # ch2 noise — subtle wind-bed, not overpowering
    3: 0.0,    # ch3 unused
    4: 0.0,    # ch4 unused
})

# --- Delay (10hp) ----------------------------------------------------------
# Params: 0 TIME 1 FEEDBACK 2 TONE 3 MIX  4..7 CV attens
# In: 0 TIME 1 FB 2 TONE 3 MIX 4 IN 5 CLK | Out: 0 MIX 1 WET
# TIME_PARAM formula: time_s = 0.001 * 10000^param  -> param = log10(time_ms)/4
import math
_delay_time_s = 0.375   # ~dotted 16th at 160 bpm — locks with the sequence
_delay_param = math.log10(_delay_time_s * 1000) / 4.0
delay = mod("Fundamental", "Delay", (68, 0), {
    0: _delay_param,  # ~375 ms
    1: 0.45,          # feedback — musical repeats, no runaway
    2: 0.50,          # tone (neutral)
    3: 0.35,          # wet/dry mix
    4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0,   # CV attenuators
})

# --- Noise (3hp) -----------------------------------------------------------
# No params. Out: 0 WHITE 1 PINK 2 RED 3 VIOLET 4 BLUE 5 GRAY 6 BLACK
noise = mod("Fundamental", "Noise", (78, 0), {})

# --- LFO (10hp) ------------------------------------------------------------
# Params: 0 OFFSET 1 INVERT 2 FREQ 3 FM 4 FM2(removed) 5 PW 6 PWM
# In: 0 FM 1 FM2(removed) 2 RESET 3 PW 4 CLOCK | Out: 0 SIN 1 TRI 2 SAW 3 SQR
lfo = mod("Fundamental", "LFO", (81, 0), {
    0: 1.0,            # unipolar (0..10V) — good for mod amplitude
    1: 0.0,            # not inverted
    2: math.log2(0.15),# ~0.15 Hz slow whoosh (param is log2 Hz)
    3: 0.0, 5: 0.5, 6: 0.0,
})

# --- Audio-2 output (Core plugin, ships with Rack) -------------------------
# 2-in/2-out stereo audio interface. Params: 0 LEVEL (0..2, default 1.0)
# Inputs: 0 = L, 1 = R (R is normalled to L so mono into L is fine).
audio = mod("Core", "AudioInterface2", (91, 0), {0: 1.0})

# ---------------------------------------------------------------------------
# Bonus free modules from Bastl / Erica Synths (placed, unconnected)
# ---------------------------------------------------------------------------
pizza       = mod("BastlPizza",  "Pizza",             (0, 1), {})
bwt_vco     = mod("EricaCopies", "BlackWaveTableVCO", (8, 1), {})
octasource  = mod("EricaCopies", "BlackOctasource",   (20, 1), {})
fusion_dly  = mod("EricaCopies", "FusionDelay",       (34, 1), {})

modules = [seq3, vco, vcf, adsr, vca, mixer, delay, noise, lfo, audio,
           pizza, bwt_vco, octasource, fusion_dly]

# ---------------------------------------------------------------------------
# Cables (Fundamental-only, guaranteed valid port IDs)
# ---------------------------------------------------------------------------
RED    = "#fc2d5a"   # audio
YELLOW = "#f9b530"   # CV / pitch
BLUE   = "#2f8ed6"   # gate / trig
GREEN  = "#5fcc3f"   # env / lfo

cables = [
    # pitch CV:   SEQ3 CV1(out 1) -> VCO PITCH(in 0)
    cable(seq3["id"], 1,  vco["id"],   0, YELLOW),
    # gate:       SEQ3 TRIG(out 0) -> ADSR GATE(in 4)
    cable(seq3["id"], 0,  adsr["id"],  4, BLUE),
    # audio:      VCO SAW(out 2)  -> VCF IN(in 3)
    cable(vco["id"],  2,  vcf["id"],   3, RED),
    # env -> filt: ADSR ENV(out 0) -> VCF FREQ(in 0)
    cable(adsr["id"], 0,  vcf["id"],   0, GREEN),
    # audio:      VCF LPF(out 0)  -> VCA IN1(in 2)
    cable(vcf["id"],  0,  vca["id"],   2, RED),
    # env -> VCA: ADSR ENV(out 0) -> VCA LIN1(in 1)
    cable(adsr["id"], 0,  vca["id"],   1, GREEN),
    # dry to mix: VCA OUT1(out 0) -> Mixer CH1(in 1)
    cable(vca["id"],  0,  mixer["id"], 1, RED),
    # noise to mix: Noise WHITE(out 0) -> Mixer CH2(in 2)
    cable(noise["id"],0,  mixer["id"], 2, RED),
    # LFO modulates noise level: LFO SIN(out 0) -> Mixer CH2 CV(in 6)
    cable(lfo["id"],  0,  mixer["id"], 6, GREEN),
    # mix bus -> delay: Mixer MIX(out 0) -> Delay IN(in 4)
    cable(mixer["id"],0,  delay["id"], 4, RED),
    # delay -> audio out L: Delay MIX(out 0) -> Audio2 L(in 0)
    cable(delay["id"],0,  audio["id"], 0, RED),
    # delay -> audio out R: Delay MIX(out 0) -> Audio2 R(in 1)   (stereo duplicate)
    cable(delay["id"],0,  audio["id"], 1, RED),
]

# ---------------------------------------------------------------------------
# Assemble patch.json
# ---------------------------------------------------------------------------
patch = {
    "version":    "2.6.6",
    "zoom":       0.0,
    "gridOffset": [0.0, 0.0],
    "modules":    modules,
    "cables":     cables,
}

# ---------------------------------------------------------------------------
# Pack to .vcv  (tar + zstd)
# ---------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    (td / "modules").mkdir()
    (td / "patch.json").write_text(json.dumps(patch, indent=2))
    # tar --zstd -cf <out> -C <td> ./patch.json ./modules
    subprocess.run(
        ["tar", "--zstd", "-cf", str(OUT_VCV), "-C", str(td), "./patch.json", "./modules"],
        check=True,
    )

print(f"Wrote {OUT_VCV}  ({OUT_VCV.stat().st_size} bytes)")
print(f"      {len(modules)} modules, {len(cables)} cables")
