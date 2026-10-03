"""
Soundtrack Synthesizer for PWD301 LMS Launch Film
Tempo: 129.0 BPM (Electronic / Tech / Punchy / Modern SaaS)
Duration: 70.0 Seconds
Outputs: showcase/assets/audio/bgm_129bpm.wav & .mp3
"""

import numpy as np
import scipy.io.wavfile as wavfile
import subprocess
import os

SAMPLE_RATE = 44100
DURATION = 70.0
BPM = 129.0
BEAT_DUR = 60.0 / BPM  # ~0.4651s
SIXTEENTH = BEAT_DUR / 4.0

total_samples = int(SAMPLE_RATE * DURATION)
audio_left = np.zeros(total_samples, dtype=np.float32)
audio_right = np.zeros(total_samples, dtype=np.float32)

t_axis = np.arange(total_samples) / SAMPLE_RATE

# --- 1. Synthesize Drum Components ---
# Kick Drum (0.3s)
kick_len = int(SAMPLE_RATE * 0.35)
t_k = np.arange(kick_len) / SAMPLE_RATE
f_k = 45.0 + 130.0 * np.exp(-t_k * 30.0)
kick = np.sin(2.0 * np.pi * np.cumsum(f_k) / SAMPLE_RATE) * np.exp(-t_k * 10.0)
kick = np.tanh(kick * 2.2) * 0.85

# Snare / Clap (0.25s)
snare_len = int(SAMPLE_RATE * 0.25)
t_sn = np.arange(snare_len) / SAMPLE_RATE
noise = np.random.uniform(-1, 1, snare_len)
body = np.sin(2.0 * np.pi * 200.0 * t_sn)
snare = (noise * 0.75 + body * 0.25) * np.exp(-t_sn * 22.0)
snare = np.tanh(snare * 1.8) * 0.65

# Hi-Hat Closed (0.06s)
hat_len = int(SAMPLE_RATE * 0.07)
t_h = np.arange(hat_len) / SAMPLE_RATE
hat = np.random.uniform(-1, 1, hat_len) * np.exp(-t_h * 75.0) * 0.35

# Open Hat (0.2s)
ohat_len = int(SAMPLE_RATE * 0.2)
t_oh = np.arange(ohat_len) / SAMPLE_RATE
ohat = np.random.uniform(-1, 1, ohat_len) * np.exp(-t_oh * 18.0) * 0.4


# Bass Synth Note Generator
def get_bass_note(freq, duration_sec):
    n_samples = int(SAMPLE_RATE * duration_sec)
    t = np.arange(n_samples) / SAMPLE_RATE
    # Sawtooth with lowpass envelope
    saw = 2.0 * (t * freq - np.floor(0.5 + t * freq))
    sub = np.sin(2.0 * np.pi * (freq / 2.0) * t) * 0.6
    env = np.exp(-t * (4.0 / duration_sec))
    return np.tanh((saw * 0.6 + sub) * 1.5) * env * 0.5


# Pluck / Arp Note Generator
def get_pluck_note(freq, duration_sec=0.25):
    n_samples = int(SAMPLE_RATE * duration_sec)
    t = np.arange(n_samples) / SAMPLE_RATE
    wave = (
        np.sin(2.0 * np.pi * freq * t)
        + 0.4 * np.sin(2.0 * np.pi * freq * 2.0 * t)
        + 0.2 * np.sin(2.0 * np.pi * freq * 3.0 * t)
    )
    env = np.exp(-t * 16.0)
    return wave * env * 0.35


# Pitch map (D minor pentatonic / tech scale)
# D2=73.42, F2=87.31, G2=98.00, A2=110.0, C3=130.81, D3=146.83, F3=174.61, A3=220.0, C4=261.63, D4=293.66, F4=349.23, A4=440.0
PITCH_D2, PITCH_F2, PITCH_G2, PITCH_A2 = 73.42, 87.31, 98.00, 110.00
PITCH_C3, PITCH_D3, PITCH_F3, PITCH_A3 = 130.81, 146.83, 174.61, 220.00
PITCH_C4, PITCH_D4, PITCH_F4, PITCH_A4 = 261.63, 293.66, 349.23, 440.00


def mix_sample(dest, src, start_sample, volume=1.0, pan=0.0):
    end_sample = min(start_sample + len(src), total_samples)
    actual_len = end_sample - start_sample
    if actual_len <= 0 or start_sample >= total_samples:
        return
    l_gain = np.clip(1.0 - pan, 0.0, 1.0) * volume
    r_gain = np.clip(1.0 + pan, 0.0, 1.0) * volume
    audio_left[start_sample:end_sample] += src[:actual_len] * l_gain
    audio_right[start_sample:end_sample] += src[:actual_len] * r_gain


print("[Soundtrack] Generating rhythm and synth arrangement...")

# 2. Arrange Beats & Tracks across 70 seconds
n_beats = int(DURATION / BEAT_DUR)

for b in range(n_beats):
    t_beat = b * BEAT_DUR
    sample_idx = int(t_beat * SAMPLE_RATE)
    bar_num = b // 4
    beat_in_bar = b % 4

    # Intro (Bars 0-1, 0.0s - 3.7s): subtle pulse
    if bar_num < 2:
        if beat_in_bar == 0:
            mix_sample(audio_left, kick * 0.7, sample_idx, volume=0.6, pan=0.0)
        continue

    # Main energy (Bar 2 to Bar 34: 3.7s - 63.0s)
    if bar_num < 34:
        # Kick on 1 and 3 (four-on-the-floor energy for driving tech feel)
        if bar_num >= 4:
            # 4-on-the-floor
            mix_sample(audio_left, kick, sample_idx, volume=0.85, pan=0.0)
        else:
            if beat_in_bar in [0, 2]:
                mix_sample(audio_left, kick, sample_idx, volume=0.8, pan=0.0)

        # Snare on 2 and 4
        if beat_in_bar in [1, 3]:
            mix_sample(audio_left, snare, sample_idx, volume=0.75, pan=0.0)

        # Hi-Hats on 16th notes
        for s in range(4):
            s_idx = sample_idx + int(s * SIXTEENTH * SAMPLE_RATE)
            if s % 2 == 1:
                # Upbeat open/closed hat
                mix_sample(audio_left, hat, s_idx, volume=0.45, pan=-0.2 if s == 1 else 0.2)
            else:
                mix_sample(audio_left, hat, s_idx, volume=0.25, pan=0.0)

        # Bassline progression (D minor)
        # Bar progression: Dm -> Dm -> F -> G
        chord_root = [PITCH_D2, PITCH_D2, PITCH_F2, PITCH_G2][bar_num % 4]
        # Rolling 16th bass
        for s in range(4):
            b_note_pitch = chord_root if s in [0, 2] else chord_root * 1.5
            b_sample = get_bass_note(b_note_pitch, SIXTEENTH * 0.85)
            s_idx = sample_idx + int(s * SIXTEENTH * SAMPLE_RATE)
            mix_sample(audio_left, b_sample, s_idx, volume=0.65, pan=0.0)

        # Arpeggio Lead (from Bar 6 onward)
        if bar_num >= 6:
            arp_notes = [
                PITCH_D3,
                PITCH_F3,
                PITCH_A3,
                PITCH_D4,
                PITCH_C4,
                PITCH_A3,
                PITCH_F3,
                PITCH_A3,
            ]
            for s in range(2):
                note_pitch = arp_notes[(b * 2 + s) % len(arp_notes)]
                arp_samp = get_pluck_note(note_pitch, SIXTEENTH * 1.5)
                s_idx = sample_idx + int(s * 2 * SIXTEENTH * SAMPLE_RATE)
                pan_val = 0.35 if (b + s) % 2 == 0 else -0.35
                mix_sample(audio_left, arp_samp, s_idx, volume=0.5, pan=pan_val)

    # Staccato Outro Build (Bars 34-35: 63.0s - 66.5s)
    elif bar_num < 36:
        # Rapid staccato kicks and claps matching the 3D ecosystem orbit
        mix_sample(audio_left, kick, sample_idx, volume=0.9, pan=0.0)
        mix_sample(
            audio_left, snare, sample_idx + int(SIXTEENTH * 2 * SAMPLE_RATE), volume=0.8, pan=0.0
        )

    # Grand Outro (Bars 36+: 66.5s - 70.0s)
    else:
        if b == 36 * 4:  # Exactly at 66.97s (Scene 12 Logo Reveal)
            # Massive sub bass hit
            sub_len = int(SAMPLE_RATE * 3.0)
            t_sub = np.arange(sub_len) / SAMPLE_RATE
            sub_hit = np.sin(2.0 * np.pi * (50.0 * np.exp(-t_sub * 0.8)) * t_sub) * np.exp(
                -t_sub * 0.8
            )
            mix_sample(audio_left, np.tanh(sub_hit * 2.0), sample_idx, volume=1.0, pan=0.0)
            # Outro chord
            for f in [PITCH_D3, PITCH_A3, PITCH_D4, PITCH_F4]:
                chord_s = get_pluck_note(f, 3.5)
                mix_sample(audio_left, chord_s, sample_idx, volume=0.7, pan=0.0)

# 3. Master Soft Limiting & Normalization
print("[Soundtrack] Normalizing and mastering audio...")
max_val = max(np.max(np.abs(audio_left)), np.max(np.abs(audio_right)))
if max_val > 0:
    audio_left = (audio_left / max_val) * 0.92
    audio_right = (audio_right / max_val) * 0.92

# Fade out last 1.5 seconds smoothly
fade_samples = int(SAMPLE_RATE * 1.5)
fade_env = np.linspace(1.0, 0.0, fade_samples)
audio_left[-fade_samples:] *= fade_env
audio_right[-fade_samples:] *= fade_env

# 4. Save to WAV
out_wav = os.path.abspath("showcase/assets/audio/bgm_129bpm.wav")
stereo = np.vstack(
    [(audio_left * 32767).astype(np.int16), (audio_right * 32767).astype(np.int16)]
).T
wavfile.write(out_wav, SAMPLE_RATE, stereo)
print(f"[Soundtrack] Saved WAV: {out_wav} ({os.path.getsize(out_wav)} bytes)")

# Convert to MP3 via ffmpeg
out_mp3 = os.path.abspath("showcase/assets/audio/bgm_129bpm.mp3")
ffmpeg_bin = r"C:\Users\LENOVO\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.EXE"
cmd = [ffmpeg_bin, "-y", "-i", out_wav, "-b:a", "192k", out_mp3]
subprocess.run(cmd, capture_output=True)
print(f"[Soundtrack] Converted MP3: {out_mp3} ({os.path.getsize(out_mp3)} bytes)")
