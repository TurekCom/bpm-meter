from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import wave

import numpy as np

from tempo import SAMPLE_RATE, AudioError, measure_bpm


def write_wave(path, samples):
    with wave.open(str(path), "wb") as file:
        file.setparams((1, 2, SAMPLE_RATE, 0, "NONE", "not compressed"))
        file.writeframes((samples * 32767).astype("<i2").tobytes())


def click_track(bpm, seconds=40):
    samples = np.zeros(seconds * SAMPLE_RATE)
    time = np.arange(SAMPLE_RATE // 20) / SAMPLE_RATE
    click = np.sin(2 * np.pi * 720 * time) * np.exp(-90 * time)
    for beat in np.arange(0.25, seconds - 0.1, 60 / bpm):
        start = round(beat * SAMPLE_RATE)
        samples[start:start + click.size] = click
    return samples


class TempoTest(unittest.TestCase):
    def test_detects_known_tempos(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "próba tempa.wav"
            for bpm in (66, 94, 123.45, 153, 178):
                with self.subTest(bpm=bpm):
                    write_wave(path, click_track(bpm))
                    self.assertAlmostEqual(measure_bpm(path), bpm, delta=0.5)

    def test_rejects_silence_and_unstructured_noise(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "audio.wav"
            noise = np.random.default_rng(28).normal(0, 0.1, 12 * SAMPLE_RATE)
            for samples in (np.zeros_like(noise), noise):
                write_wave(path, samples)
                self.assertIsNone(measure_bpm(path))

    def test_invalid_and_missing_inputs(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "broken.mp3"
            with self.assertRaises(AudioError):
                measure_bpm(path)
            path.write_text("invalid audio")
            with self.assertRaises(AudioError):
                measure_bpm(path)


if __name__ == "__main__":
    unittest.main()
