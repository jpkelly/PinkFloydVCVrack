# Changelog

All notable changes to this project are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Changed
- README: updated usage steps to reflect built-in Audio-2 module and the
  one-time audio-device selection step.

## [0.3.0] - 2026-04-22

### Changed
- Tuned default parameters so the patch sounds good with zero tweaking:
  - VCF cutoff `0.55 → 0.35`, env-to-cutoff `0.45 → 0.65`, resonance
    `0.70 → 0.55` — plucky, singing sweep on every note without
    self-oscillation.
  - ADSR attack `0.05 → 0.02`, decay `0.40 → 0.35`, release
    `0.30 → 0.20` — tighter percussive pluck.
  - Mixer noise bed `0.80 → 0.30`, master `1.0 → 0.85` — voice no longer
    drowned by noise, headroom into the delay.
  - Delay feedback `0.55 → 0.45`, mix `0.40 → 0.35`, time
    `380 ms → 375 ms` — musical repeats locked to the sequence.
  - LFO `0.25 Hz → 0.15 Hz` — slower, more ambient whoosh.

## [0.2.0] - 2026-04-22

### Added
- **Core `AudioInterface2`** module placed at the right of the rack and
  cabled `Delay.MIX → Audio.L/R` so the patch produces sound out of the
  box. User only needs to pick their output device the first time.

### Fixed
- SEQ3 step gates were being silently toggled OFF on load. The per-step
  gate buttons are `BooleanTrigger`s, so a non-zero saved param value
  caused a 0→1 transition on the first process tick, inverting the
  `data.gates` array. Set gate-button params to `0.0` and rely on
  `data.gates = [1]*8` for step activation. Without this the voice path
  was silent; only the noise bed was audible.

## [0.1.0] - 2026-04-22

### Added
- Initial project scaffold:
  - `build_patch.py` — Python generator that emits a valid
    `Pink Floyd.vcv` (tar + zstd of `patch.json`), using only the Python
    standard library.
  - Row 0 Fundamental signal chain: SEQ3 → VCO → VCF → VCA → VCMixer →
    Delay, with ADSR envelope, Noise, and LFO modulating the noise
    amplitude.
  - Row 1 bonus modules placed (unconnected) for experimentation: Bastl
    Pizza, Erica Synths BlackWaveTableVCO, BlackOctasource, FusionDelay.
  - README with signal-flow diagram, requirements, and usage.
  - `.gitignore` for Rack autosaves, `.DS_Store`, `__pycache__`, logs.
- Public GitHub repository `jpkelly/PinkFloydVCVrack`.
