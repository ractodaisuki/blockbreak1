from dataclasses import dataclass
import math

import pyxel


WIDTH = 160
HEIGHT = 120
PADDLE_WIDTH = 26
PADDLE_HEIGHT = 4
BALL_RADIUS = 2
PADDLE_SPEED = 2.8
INITIAL_LIVES = 3
BALL_START_SPEED_X = 0.8
BALL_START_SPEED_Y = -1.25
BALL_SPEED_MAX = 2.4
BALL_SPEED_STEP = 0.04
BRICK_COLS = 10
BRICK_ROWS = 5
BRICK_WIDTH = 13
BRICK_HEIGHT = 6
BRICK_GAP = 2
BRICK_OFFSET_X = 8
BRICK_OFFSET_Y = 18
STATE_TITLE = "title"
STATE_PLAYING = "playing"
STATE_CLEAR = "clear"
STATE_GAME_OVER = "game_over"


@dataclass
class Paddle:
    x: float
    y: float
    width: int = PADDLE_WIDTH
    height: int = PADDLE_HEIGHT
    speed: float = PADDLE_SPEED


@dataclass
class Ball:
    x: float
    y: float
    vx: float
    vy: float
    radius: int = BALL_RADIUS


@dataclass
class Brick:
    x: int
    y: int
    width: int
    height: int
    color: int
    alive: bool = True


class App:
    def __init__(self) -> None:
        pyxel.init(WIDTH, HEIGHT, title="Block Breaker", fps=60)
        pyxel.mouse(True)
        self.stars = [
            [pyxel.rndi(0, WIDTH - 1), pyxel.rndi(0, HEIGHT - 1), pyxel.rndi(1, 2)]
            for _ in range(24)
        ]
        self.score = 0
        self.lives = INITIAL_LIVES
        self.state = STATE_TITLE
        self.paddle = Paddle(x=WIDTH / 2 - PADDLE_WIDTH / 2, y=HEIGHT - 12)
        self.ball = Ball(
            x=WIDTH / 2,
            y=HEIGHT - 18,
            vx=BALL_START_SPEED_X,
            vy=BALL_START_SPEED_Y,
        )
        self.bricks: list[Brick] = []
        self.reset_game()
        pyxel.run(self.update, self.draw)

    def reset_game(self) -> None:
        self.score = 0
        self.lives = INITIAL_LIVES
        self.bricks = self.build_bricks()
        self.reset_round()
        self.state = STATE_TITLE

    def reset_round(self) -> None:
        self.paddle.x = WIDTH / 2 - self.paddle.width / 2
        self.ball.x = WIDTH / 2
        self.ball.y = HEIGHT - 18
        direction = -1 if pyxel.rndi(0, 1) == 0 else 1
        self.ball.vx = BALL_START_SPEED_X * direction
        self.ball.vy = BALL_START_SPEED_Y

    def build_bricks(self) -> list[Brick]:
        colors = [8, 9, 10, 11, 12]
        bricks: list[Brick] = []
        for row in range(BRICK_ROWS):
            for col in range(BRICK_COLS):
                x = BRICK_OFFSET_X + col * (BRICK_WIDTH + BRICK_GAP)
                y = BRICK_OFFSET_Y + row * (BRICK_HEIGHT + BRICK_GAP)
                bricks.append(
                    Brick(
                        x=x,
                        y=y,
                        width=BRICK_WIDTH,
                        height=BRICK_HEIGHT,
                        color=colors[row % len(colors)],
                    )
                )
        return bricks

    def update(self) -> None:
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        self.update_stars()

        if self.state == STATE_TITLE:
            if self.start_pressed():
                self.state = STATE_PLAYING
            return

        if self.state in (STATE_CLEAR, STATE_GAME_OVER):
            if self.start_pressed():
                self.reset_game()
                self.state = STATE_PLAYING
            return

        self.update_paddle()
        self.update_ball()

    def start_pressed(self) -> bool:
        return (
            pyxel.btnp(pyxel.KEY_SPACE)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A)
            or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)
        )

    def update_stars(self) -> None:
        for star in self.stars:
            star[1] += star[2] * 0.35
            if star[1] >= HEIGHT:
                star[0] = pyxel.rndi(0, WIDTH - 1)
                star[1] = 0
                star[2] = pyxel.rndi(1, 2)

    def update_paddle(self) -> None:
        pointer_down = pyxel.btn(pyxel.MOUSE_BUTTON_LEFT)
        pointer_in_bounds = 0 <= pyxel.mouse_x < WIDTH and 10 <= pyxel.mouse_y < HEIGHT
        move_left = pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A)
        move_right = pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D)

        if pointer_down and pointer_in_bounds:
            self.paddle.x = pyxel.mouse_x - self.paddle.width / 2
        elif move_left:
            self.paddle.x -= self.paddle.speed
        elif move_right:
            self.paddle.x += self.paddle.speed

        self.paddle.x = max(4, min(self.paddle.x, WIDTH - self.paddle.width - 4))

    def update_ball(self) -> None:
        previous_x = self.ball.x
        previous_y = self.ball.y
        self.ball.x += self.ball.vx
        self.ball.y += self.ball.vy

        if self.ball.x <= self.ball.radius:
            self.ball.x = self.ball.radius
            self.ball.vx *= -1
        elif self.ball.x >= WIDTH - self.ball.radius:
            self.ball.x = WIDTH - self.ball.radius
            self.ball.vx *= -1

        if self.ball.y <= 10 + self.ball.radius:
            self.ball.y = 10 + self.ball.radius
            self.ball.vy *= -1

        if self.ball.y >= HEIGHT + self.ball.radius:
            self.lives -= 1
            if self.lives <= 0:
                self.state = STATE_GAME_OVER
            else:
                self.reset_round()
            return

        if self.ball_hits_paddle():
            hit = (self.ball.x - self.paddle.x) / self.paddle.width
            angle = (hit - 0.5) * 1.8
            speed = min(BALL_SPEED_MAX, math.hypot(self.ball.vx, self.ball.vy) + BALL_SPEED_STEP)
            self.ball.vx = math.sin(angle) * speed
            self.ball.vy = -abs(math.cos(angle) * speed)
            self.ball.y = self.paddle.y - self.ball.radius - 1

        if self.hit_brick(previous_x, previous_y):
            remaining = sum(1 for brick in self.bricks if brick.alive)
            if remaining == 0:
                self.state = STATE_CLEAR

    def ball_hits_paddle(self) -> bool:
        return (
            self.ball.y + self.ball.radius >= self.paddle.y
            and self.ball.y - self.ball.radius <= self.paddle.y + self.paddle.height
            and self.ball.x + self.ball.radius >= self.paddle.x
            and self.ball.x - self.ball.radius <= self.paddle.x + self.paddle.width
            and self.ball.vy > 0
        )

    def hit_brick(self, previous_x: float, previous_y: float) -> bool:
        for brick in self.bricks:
            if not brick.alive:
                continue

            overlaps = (
                self.ball.x + self.ball.radius >= brick.x
                and self.ball.x - self.ball.radius <= brick.x + brick.width
                and self.ball.y + self.ball.radius >= brick.y
                and self.ball.y - self.ball.radius <= brick.y + brick.height
            )
            if not overlaps:
                continue

            brick.alive = False
            self.score += 10

            was_left = previous_x + self.ball.radius <= brick.x
            was_right = previous_x - self.ball.radius >= brick.x + brick.width
            was_above = previous_y + self.ball.radius <= brick.y
            was_below = previous_y - self.ball.radius >= brick.y + brick.height

            # Use the previous position to choose a stable bounce direction.
            if was_left or was_right:
                self.ball.vx *= -1
            elif was_above or was_below:
                self.ball.vy *= -1
            else:
                self.ball.vy *= -1

            return True

        return False

    def draw(self) -> None:
        pyxel.cls(1)
        self.draw_stars()
        self.draw_frame()
        self.draw_hud()
        self.draw_bricks()
        self.draw_paddle()
        self.draw_ball()

        if self.state == STATE_TITLE:
            self.draw_overlay("BLOCK BREAKER", "SPACE TO START")
        elif self.state == STATE_CLEAR:
            self.draw_overlay("STAGE CLEAR", "SPACE TO RETRY")
        elif self.state == STATE_GAME_OVER:
            self.draw_overlay("GAME OVER", "SPACE TO RETRY")

    def draw_stars(self) -> None:
        for x, y, speed in self.stars:
            color = 5 if speed == 1 else 6
            pyxel.pset(int(x), int(y), color)

    def draw_frame(self) -> None:
        pyxel.rectb(0, 10, WIDTH, HEIGHT - 10, 13)
        pyxel.line(0, 10, WIDTH, 10, 13)

    def draw_hud(self) -> None:
        pyxel.text(6, 3, f"SCORE {self.score:04d}", 7)
        pyxel.text(WIDTH - 42, 3, f"LIFE {self.lives}", 7)

    def draw_bricks(self) -> None:
        for brick in self.bricks:
            if not brick.alive:
                continue
            pyxel.rect(brick.x, brick.y, brick.width, brick.height, brick.color)
            pyxel.rectb(brick.x, brick.y, brick.width, brick.height, 7)

    def draw_paddle(self) -> None:
        pyxel.rect(int(self.paddle.x), int(self.paddle.y), self.paddle.width, self.paddle.height, 7)

    def draw_ball(self) -> None:
        pyxel.circ(int(self.ball.x), int(self.ball.y), self.ball.radius, 10)

    def draw_overlay(self, title: str, subtitle: str) -> None:
        pyxel.rect(24, 42, 112, 34, 0)
        pyxel.rectb(24, 42, 112, 34, 7)
        title_x = WIDTH // 2 - len(title) * 2
        subtitle_x = WIDTH // 2 - len(subtitle) * 2
        pyxel.text(title_x, 50, title, 8)
        pyxel.text(subtitle_x, 62, subtitle, 7)
        if self.state == STATE_TITLE:
            pyxel.text(34, 84, "MOVE: DRAG OR A/D", 6)
            pyxel.text(32, 92, "START: TAP OR SPACE", 6)


App()
