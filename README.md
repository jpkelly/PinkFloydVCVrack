# Pink Floyd — "On the Run" VCV Rack Patch

A [VCV Rack 2](https://vcvrack.com/) patch that recreates the background
texture from Pink Floyd's **"On the Run"** (*Dark Side of the Moon*, 1973):
the fast resonant-filter pulse, the noise whooshes, and a tape-style delay
for the echoing space.

Built entirely with **free** plugins from the VCV Library.

---

## What's in this repo

| File | Purpose |
| --- | --- |
| [`build_patch.py`](build_patch.py) | "Source code" — a Python script that builds the patch. Edit it and re-run to regenerate. |
| `Pink Floyd.vcv` | The compiled patch (a zstd-compressed tar archive containing `patch.json`). |

A `.vcv` file is just a tar + zstd bundle. Inside is a human-readable
`patch.json`, so the whole patch is describable as data and diff-friendly.

---

## Signal flow

Row 0 (fully cabled, uses only VCV Fundamental + Rack's built-in Core):

```
 SEQ3 ──CV1──▶ VCO ──SAW──▶ VCF ──▶ VCA ──▶ Mixer.CH1 ──▶ Delay ──▶ Audio-2 L/R
   └─TRIG──▶ ADSR ──▶ VCF.FREQ  &  VCA.LIN
 Noise.WHITE ──▶ Mixer.CH2
 LFO.SIN ─────▶ Mixer.CH2 CV     (slow whoosh amplitude modulation)
```

- **SEQ3** — 8-step sequence (E A G A E D G E in E minor) at ~660 bpm
  → the iconic fast "rrrrrr" pulse.
- **VCO** — sawtooth through a resonant ladder **VCF**, opened by a fast
  percussive **ADSR** for the singing filter sweep on every note.
- **Noise** → **VCA-style amplitude mod via LFO** → dreamy whooshes.
- **Delay** — ~380 ms, ~55% feedback → tape-echo spaciousness.

Row 1 (placed but unconnected — wire these up yourself to experiment):

- **Bastl Pizza** — compact FM oscillator. Try swapping for the VCO.
- **Erica Synths Black WaveTable VCO** — grittier digital lead voice.
- **Erica Synths Black Octasource** — 8-phase LFO; great for patching into
  multiple mixer CVs to create evolving noise textures.
- **Erica Synths Fusion Delay** — BBD delay; swap in for a warmer,
  tape-like echo character.

---

## Requirements

- [VCV Rack 2](https://vcvrack.com/Rack) (v2.6 or later recommended).
- Free plugins (Rack will offer to auto-install any missing ones when the
  patch is opened):
  - [VCV Fundamental](https://library.vcvrack.com/Fundamental) (bundled)
  - [Bastl Pizza](https://library.vcvrack.com/BastlPizza) — free
  - [Erica Synths](https://library.vcvrack.com/EricaCopies) — free

---

## Usage

1. Double-click `Pink Floyd.vcv`, or open it from Rack via **File → Open**.
2. Rack will prompt to install any missing plugins from the Library — accept.
3. On the **Audio-2** module (far right of the rack) click the display and
   pick your audio driver + output device (e.g. *Core Audio → MacBook Pro
   Speakers*). This setting is machine-specific so the patch can't ship it.
4. That's it — sound should start immediately. The sequencer auto-runs on
   load.

> If it's silent, check that **SEQ3's RUN light is lit** (click RUN if not)
> and that Rack's CPU meter is green.

### Tweak knobs for different moods

- **VCF cutoff / resonance** — darker vs singing.
- **ADSR decay** — tighter pluck vs longer sweep.
- **Delay time / feedback** — dubbier or drier.
- **LFO rate** — speed of the noise whooshes.

---

## Rebuilding the patch

The `.vcv` file is regenerated from `build_patch.py`:

```bash
python3 build_patch.py
```

This writes a fresh `Pink Floyd.vcv` in the repo root. No external Python
dependencies — just the standard library and the system `tar` (with zstd,
which macOS and Linux both ship with).

To inspect the JSON inside:

```bash
tar --zstd -xf "Pink Floyd.vcv" -C /tmp/pf && cat /tmp/pf/patch.json
```

---

## License

Patch definition (this repo): MIT.
VCV Rack and the plugins referenced here are the property of their
respective authors.
