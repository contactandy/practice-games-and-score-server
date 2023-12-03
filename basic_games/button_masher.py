"""A button mashing game."""
import pygame

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

class Counter:
    """Counter with a draw method"""
    def __init__(self, position):
        self.counter = 0
        self.pos = position
        self.font = pygame.font.SysFont(None, 100)

    def inc(self):
        self.counter += 1

    def draw(self, surf):
        display = f"Score: {self.counter}"
        text = self.font.render(display, True, BLACK)
        rect = text.get_rect(topleft = self.pos)
        surf.blit(text, rect)


class Timer:
    """Timer for seconds with a draw method"""
    def __init__(self, duration, position):
        self.clock = pygame.time.Clock()
        self.event = pygame.USEREVENT
        self.remaining = duration
        pygame.time.set_timer(self.event, 1000)
        self.done = False

        self.pos = position

        self.font = pygame.font.SysFont(None, 100)
        self.max_digits = len(str(duration))

    def tick(self):
        self.remaining -= 1
        if self.remaining == 0:
            pygame.time.set_timer(self.event, 0)
            self.done = True

    def draw(self, surf):
        display = f"Time: {self.remaining:0{self.max_digits}}"
        text = self.font.render(display, True, BLACK)
        rect = text.get_rect(topleft=self.pos)
        surf.blit(text, rect)

class App:
    """Play button masher"""

    def __init__(self):
        """Initialize pygame and the application"""
        pygame.init()
        pygame.display.set_caption("Mash buttons!")
        self.screen = pygame.display.set_mode((500, 500))

        self.timer = Timer(10, (0,0))
        self.counter = Counter((0, 60))

        self.running = True

    def run(self):
        """Run the main event loop."""
        font = pygame.font.SysFont(None, 100)
        text = font.render(str(self.timer.remaining), True, (0, 128, 0))
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == self.timer.event:
                    self.timer.tick()
                elif event.type == pygame.KEYDOWN:
                    if not self.timer.done:
                        self.counter.inc()
            self.draw()

    def draw(self):
        self.screen.fill(WHITE)
        self.timer.draw(self.screen)
        self.counter.draw(self.screen)
        pygame.display.update()


if __name__ == '__main__':
    App().run()
