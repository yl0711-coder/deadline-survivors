from __future__ import annotations

import pygame

from .constants import GRID, TEXT


def draw_translucent_rect(
    screen: pygame.Surface,
    rect: pygame.Rect,
    color: tuple[int, int, int],
    alpha: int,
    border_radius: int,
) -> None:
    surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(surface, (*color, alpha), surface.get_rect(), border_radius=border_radius)
    screen.blit(surface, rect.topleft)


def draw_bar(
    screen: pygame.Surface,
    font: pygame.font.Font,
    x: int,
    y: int,
    width: int,
    height: int,
    ratio: float,
    color: tuple[int, int, int],
    label: str,
) -> None:
    pygame.draw.rect(screen, GRID, (x, y, width, height), border_radius=999)
    pygame.draw.rect(screen, color, (x, y, width * ratio, height), border_radius=999)
    screen.blit(font.render(label, True, TEXT), (x + width + 12, y - 2))


def wrap_text(font: pygame.font.Font, text: str, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if font.size(trial)[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
