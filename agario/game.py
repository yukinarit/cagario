import abc
import asyncio
import enum
import random
import time
import traceback
import collections
from .terminal import Terminal, Color, Renderable, Size, \
        Vector2, Dir, Shape, MouseKey
from .exceptions import StatusCode, GameExit
from .logger import create_logger


__all__ = [
    'Game',
]

FPS = 40 # Game FPS (Frame Per Second)

FRAME_SEC = 1 / 40 # Second per frame

logger = create_logger(__name__) # Logger for Game


class CollisionState(enum.Enum):
    NotCollided = 0
    Entered = 1
    BeingCollided = 2
    Exited = 3


class Game:
    """
    Game main class.
    """
    def __init__(self):
        self.terminal = Terminal()

        def terminal_on_shutdown():
            raise GameExit()
        self.terminal.on_shutdown = terminal_on_shutdown
        self.player = None
        self.other_players = []
        self.enemies = []
        self.count = 0
        self.enemies = spawn_enemies(
            count=300,
            rect=self.terminal.map.boundary
        )

        # fix me
        self.login(Player(x=10, y=10))

    def run(self):
        """
        Game loop.
        """
        try:
            while True:
                now = time.time() * 1000

                self.update(now)
                time.sleep(FRAME_SEC)

        except GameExit as e:
            return StatusCode.GameExit

        except Exception as e:
            self.terminal.close()
            logger.error(e)
            logger.error(traceback.format_exc())
            return -1

        return 0

    def login(self, player):
        """
        Player login.
        """
        self.player = player
        self.terminal.login(player)
        def move_left(event):
            player.move(Dir.Left)
        def move_right(event):
            player.move(Dir.Right)
        def move_up(event):
            player.move(Dir.Up)
        def move_down(event):
            player.move(Dir.Down)
        def change_size(event):
            self.terminal.debug = not self.terminal.debug
        def expand(event):
            player.expand()
            """
            value = min(
                player.get_size().value + 2,
                Size.MaxSize.value
            )
            player.set_size(value)
            """
        def shrink(event):
            player.shrink()
            """
            value = max(
                player.get_size().value - 2,
                Size.MinSize.value
            )
            player.set_size(value)
            """
        tm = self.terminal
        tm.set_keydown_handler([MouseKey.Left, MouseKey.h], move_left)
        tm.set_keydown_handler([MouseKey.Right, MouseKey.l], move_right)
        tm.set_keydown_handler([MouseKey.Up, MouseKey.k], move_up)
        tm.set_keydown_handler([MouseKey.Down, MouseKey.j], move_down)
        tm.set_keydown_handler(MouseKey.o, expand)
        tm.set_keydown_handler(MouseKey.p, shrink)
        tm.set_keydown_handler(MouseKey.d, change_size)

    def update(self, now):
        """
        Update that is called on every frame.
        """
        self.enemies = [
            enemy for enemy in self.enemies
            if not enemy.being_destroyed
        ]
        self.terminal.update(
            now,
            self.player,
            self.enemies
        )
        self.update_collisions()

    def update_collisions(self):
        """
        Update callisions on every frame.
        """
        for enemy in self.enemies:
            result = check_collision(self.player, enemy)
            if result == CollisionState.Exited:
                pass

        logger.debug('t:{}'.format(self.player.make_trajectory()))
        for other in self.other_players:
            check_collision(self.player, other)


def check_collision(player, other):
    result = CollisionState.NotCollided

    was_being_collided = player.collisions.get(id(other))
    being_collided = collide(player.make_trajectory(), other)

    if not was_being_collided and being_collided:
        player.collisions.update({id(other): being_collided})
        player.on_collision_entered(Collision(other))
        other.on_collision_entered(Collision(player))
        result = CollisionState.Entered

    elif was_being_collided and not being_collided:
        player.collisions.update({id(other): being_collided})
        player.on_collision_exited(Collision(other))
        other.on_collision_exited(Collision(player))
        result = CollisionState.Exited

    else:
        if being_collided:
            result = CollisionState.BeingCollided
        else:
            result = CollisionState.NotCollided

    return result


def collide(lhs, rhs):
    pos1 = lhs.get_pos()
    pos2 = rhs.get_pos()
    if not pos1 or not pos2:
        return False

    xdistance = abs(pos1.x - pos2.x)
    width = int((lhs.get_width() + rhs.get_width()) / 2)

    ydistance = abs(pos1.y - pos2.y)
    height = int((lhs.get_height() + rhs.get_height()) / 2)
    if xdistance < width and ydistance < height:
        return True

    return False


Collision = collections.namedtuple('Collision', ['other'])


class GameObject(Renderable):
    """
    Game object.
    """
    def __init__(self, x=None, y=None):
        Renderable.__init__(self)
        self.pos = Vector2(x, y)
        self.size = Size.w1xh1
        self.collisions = {}
        self.being_destroyed = False

    def get_width(self):
        return self.size.value

    def get_height(self):
        return self.size.value

    def get_size(self) -> Size:
        return self.size

    def set_size(self, size):
        if isinstance(size, Size):
            self.size = size
        else:
            self.size = Size(size)

    def get_pos(self):
        return self.pos

    def on_collision_entered(self, collision=None):
        pass

    def on_collision_exited(self, collision=None):
        pass

    def destroy(self):
        self.being_destroyed = True

    def expand(self):
        value = min(
            self.get_size().value + 2,
            Size.MaxSize.value
        )
        self.set_size(value)

    def shrink(self):
        value = max(
            self.get_size().value - 2,
            Size.MinSize.value
        )
        self.set_size(value)


class Player(GameObject):
    """
    Game player class.
    """
    def __init__(self, x=None, y=None):
        GameObject.__init__(self, x=x, y=y)
        self.set_color(Color.Red, Color.Red)

    def on_collision_entered(self, collision):
        logger.debug('{} collided with {}!'.format(self, collision.other))
        self.set_color(Color.Green, Color.Green)
        self.expand()

    def on_collision_exited(self, collision):
        msg = '{} not collided anymore with {}!'.format(self, collision.other)
        logger.debug(msg)
        self.set_color(Color.Red, Color.Red)

    def __repr__(self):
        return '<Player(x={x},y={y})>'.format(
            x=self.get_pos().x,
            y=self.get_pos().y,
        )


class Enemy(GameObject):
    """
    Enemy class.
    """
    def __init__(self, x, y):
        GameObject.__init__(self, x=x, y=y)
        self.size = Size.w1xh1
        self.set_color(Color.Random)

    def on_collision_entered(self, collision):
        logger.debug('{} collided with {}!'.format(self, collision.other))
        self.set_color(Color.Green)

    def on_collision_exited(self, collision):
        msg = '{} not collided anymore with {}!'.format(self, collision.other)
        logger.debug(msg)
        self.set_color(Color.Blue)
        self.destroy()

    def __repr__(self):
        return '<Enemy(x={x},y={y})>'.format(
            x=self.get_pos().x,
            y=self.get_pos().y,
        )

    def get_shape(self):
        return Shape.Bullet.value


def spawn_enemies(count=10, rect=None, randomness=True):
    """
    Spawn enemies.
    """
    logger.debug('{}'.format(rect))
    logger.debug('{} {} {} {}'.format(
        rect.x1,
        rect.x2,
        rect.y1,
        rect.y2
    ))
    enemies = [
        Enemy(
            x=random.randint(rect.x1, rect.x2-1),
            y=random.randint(rect.y1, rect.y2-1)
        )
        for n in range(0, count)
    ]
    for e in enemies:
        if not e.get_pos():
            logger.debug('get_pos returned None')
    return enemies
