from pathlib import Path

import av
import librosa
import numpy as np


SAMPLE_RATE = 22_050
HOP_LENGTH = 256
WINDOW_SAMPLES = SAMPLE_RATE * 30


class AudioError(ValueError):
    pass


def audio_windows(path: Path):
    with path.open("rb") as source, av.open(source) as container:
        if not container.streams.audio:
            raise AudioError("Plik nie zawiera ścieżki audio.")

        resampler = av.AudioResampler(format="fltp", layout="mono", rate=SAMPLE_RATE)
        fifo = av.AudioFifo()
        for frame in container.decode(audio=0):
            frame.pts = None
            for converted in resampler.resample(frame):
                fifo.write(converted)
            for window in fifo.read_many(WINDOW_SAMPLES):
                yield window.to_ndarray()[0]

        for converted in resampler.resample(None):
            fifo.write(converted)
        for window in fifo.read_many(WINDOW_SAMPLES, partial=True):
            yield window.to_ndarray()[0]


def window_tempo(samples):
    if samples.size < 3 * SAMPLE_RATE or np.max(np.abs(samples)) < 1e-5:
        return None

    onset = librosa.onset.onset_strength(y=samples, sr=SAMPLE_RATE, hop_length=HOP_LENGTH)
    bpm, beats = librosa.beat.beat_track(
        onset_envelope=onset, sr=SAMPLE_RATE, hop_length=HOP_LENGTH
    )
    bpm = float(np.asarray(bpm).item())
    if bpm <= 0 or beats.size < 5:
        return None

    frames_per_minute = 60 * SAMPLE_RATE / HOP_LENGTH
    period = frames_per_minute / bpm
    last_lag = round(period * 1.08) + 1
    correlation = librosa.autocorrelate(onset - onset.mean(), max_size=last_lag)
    first_lag = max(1, round(period * 0.92))
    if correlation.size <= first_lag:
        return None
    beat_strength = correlation[first_lag:].max()
    if beat_strength <= 0.09 * correlation[0]:
        return None

    half_period = period / 2
    if bpm <= 115 and half_period >= 2:
        faster_strength = correlation[round(0.92 * half_period):round(1.08 * half_period) + 1].max()
        between = correlation[round(1.2 * half_period):round(0.88 * period)].max()
        if faster_strength >= 0.95 * beat_strength and between < 0.8 * faster_strength:
            period = half_period
            _, beats = librosa.beat.beat_track(
                onset_envelope=onset, sr=SAMPLE_RATE, hop_length=HOP_LENGTH, bpm=float(bpm * 2)
            )

    intervals = np.diff(beats)
    regular = intervals[np.abs(intervals - period) <= 0.12 * period]
    if regular.size < max(4, 0.6 * intervals.size):
        return None
    bpm = float(frames_per_minute / regular.mean())
    return bpm, (regular.size / bpm) * (beat_strength / correlation[0])


def measure_bpm(path: Path) -> float | None:
    try:
        estimates = [result for window in audio_windows(path) if (result := window_tempo(window))]
    except (OSError, av.error.FFmpegError) as error:
        raise AudioError("Nie udało się odczytać pliku audio. Sprawdź jego format i zawartość.") from error

    if not estimates:
        return None

    groups = (
        [(bpm, weight) for bpm, weight in estimates if abs(bpm - center) <= 0.04 * center]
        for center, _ in estimates
    )
    best = max(groups, key=lambda group: sum(weight for _, weight in group))
    return sum(bpm * weight for bpm, weight in best) / sum(weight for _, weight in best)
