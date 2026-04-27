from __future__ import annotations

from array import array
from math import pi, sin

import pygame


class AudioPlayer:
    def __init__(self) -> None:
        self.enabled = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.load()

    def load(self) -> None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except pygame.error:
            self.enabled = False
            self.sounds = {}
            return

        self.enabled = True
        self.sounds = {
            "patch": build_tone(760, 45, 0.18, 0.35),
            "level": build_chord((520, 660, 820), 160, 0.22),
            "pickup": build_tone(940, 70, 0.2, 0.22),
            "hit": build_tone(180, 90, 0.24, 0.18),
            "deploy": build_chord((420, 560, 740), 140, 0.18),
            "crisis": build_tone(130, 220, 0.22, 0.05),
            "fail": build_chord((280, 210, 160), 260, 0.22),
            "pause": build_tone(540, 90, 0.18, 0.18),
        }

    def play(self, key: str) -> None:
        if self.enabled and key in self.sounds:
            self.sounds[key].play()


def build_tone(
    frequency: float,
    duration_ms: int,
    volume: float,
    decay: float,
) -> pygame.mixer.Sound:
    sample_rate = 44100
    sample_count = int(sample_rate * (duration_ms / 1000))
    samples = array("h")
    for index in range(sample_count):
        t = index / sample_rate
        envelope = max(0.0, 1.0 - (index / max(1, sample_count)) / max(decay, 0.01))
        value = int(32767 * volume * envelope * sin(2 * pi * frequency * t))
        samples.append(value)
    return pygame.mixer.Sound(buffer=samples.tobytes())


def build_chord(
    frequencies: tuple[float, ...],
    duration_ms: int,
    volume: float,
) -> pygame.mixer.Sound:
    sample_rate = 44100
    sample_count = int(sample_rate * (duration_ms / 1000))
    samples = array("h")
    for index in range(sample_count):
        t = index / sample_rate
        envelope = max(0.0, 1.0 - index / max(1, sample_count))
        mixed = sum(sin(2 * pi * frequency * t) for frequency in frequencies) / len(frequencies)
        value = int(32767 * volume * envelope * mixed)
        samples.append(value)
    return pygame.mixer.Sound(buffer=samples.tobytes())
