"""A timing game."""
import contextlib
import random
import time

import numpy as np

with contextlib.redirect_stdout(None):
    import pygame

np.set_printoptions(sign="+")

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

CLOCK = pygame.time.Clock()

DEBUG = False


class Sprite:
    def __init__(self, field, start_position=None):
        if start_position:
            self.position = np.array(start_position, dtype=float)
        else:
            self.position = np.array(
                (random.randrange(field.width), random.randrange(field.height)),
                dtype=float,
            )

        self.rect = pygame.Rect(self.position, (60, 60))

        self.image = pygame.Surface(self.rect.size)
        self.image.fill(BLACK)

        self.field = field

        self.velocity = np.random.randint(-10, 10, size=2).astype(float)
        self.acceleration = np.random.randint(-2, 2, size=2).astype(float)
        self._duration = random.randrange(20, 30)
        self.max_speed = 10

    def add_random(self):
        self.velocity = np.array(
            (
                min(self.velocity[0] + self.acceleration[0], self.max_speed),
                min(self.velocity[1] + self.acceleration[1], self.max_speed),
            ),
            dtype=float,
        )
        self._duration -= 1
        if self._duration == 0:
            self.acceleration = np.random.randint(-2, 2, size=2).astype(float)
            self._duration = random.randrange(20, 30)

    def move(self):
        self.position += self.velocity
        self.rect.update(self.position, self.rect.size)
        if self.rect.left < self.field.left:
            self.position[0] = self.field.left
            self.velocity[0] = -1 * self.velocity[0]
            self.acceleration[0] = -1 * self.acceleration[0]
        if self.rect.right > self.field.right:
            self.position[0] = self.field.right - self.rect.width
            self.velocity[0] = -1 * self.velocity[0]
            self.acceleration[0] = -1 * self.acceleration[0]
        if self.rect.top < self.field.top:
            self.position[1] = self.field.top
            self.velocity[1] = -1 * self.velocity[1]
            self.acceleration[1] = -1 * self.acceleration[1]
        if self.rect.bottom > self.field.bottom:
            self.position[1] = self.field.bottom - self.rect.height
            self.velocity[1] = -1 * self.velocity[1]
            self.acceleration[1] = -1 * self.acceleration[1]

        self.add_random()

    def draw(self, surf):
        surf.blit(self.image, self.rect)

    def is_hit(self, hit_position):
        return self.rect.collidepoint(hit_position)


class App:
    """Play button masher"""

    def __init__(self):
        """Initialize pygame and the application"""
        pygame.init()
        pygame.display.set_caption("Squash the bug!")
        self.screen = pygame.display.set_mode((1000, 800))

        self.sprite = Sprite(self.screen.get_rect())
        self.font = pygame.font.SysFont(None, 20)

        self.running = True

    def run(self):
        """Run the main event loop."""
        start = time.time()
        done = False
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.sprite.is_hit(event.pos):
                        done = True
            if not done:
                self.sprite.move()
            self.draw()
            CLOCK.tick(60)

        score = time.time() - start if done else None
        return score

    def draw(self):
        self.screen.fill(WHITE)
        self.sprite.draw(self.screen)
        if DEBUG:
            texts = [
                self.font.render(f"pos: {self.sprite.position}", True, BLACK),
                self.font.render(f"vel: {self.sprite.velocity}", True, BLACK),
                self.font.render(f"acc: {self.sprite.acceleration}", True, BLACK),
                self.font.render(f"dur: {self.sprite._duration}", True, BLACK),
            ]
            for i, text in enumerate(texts):
                self.screen.blit(text, (10, 10 + 20 * i))
        pygame.display.update()


if __name__ == "__main__":
    App().run()
