import abc
import copy
import enum
import traceback
import random
import os
from termbox import *
from .logger import create_logger


__all__ = [
    'Color',
    'Size',
    'Vector2',
    'Rect',
    'Cell',
    'Terminal',
]


basedir = os.path.abspath(os.path.dirname(__file__))

mapdir = os.path.join(basedir, '../maps')

DEFAULT_SQUARE = 0x0020

DEFAULT_COLOR = DEFAULT

logger = create_logger(__name__)


class Color(enum.IntEnum):
    """
    Color enum representing terminal colors.
    """
    Default = DEFAULT
    Black = BLACK
    Red = RED
    Green = GREEN
    Yellow = YELLOW
    Blue = BLUE
    Magenta = MAGENTA
    Cyan = CYAN
    White = WHITE
    Random = 0x09

    @classmethod
    def random_color(cls):
        return random.randint(cls.Default, cls.Random-1)


class Shape(enum.Enum):
    """
    """
    Square = ord(' ')
    Bullet = ord('•')
    Star = ord('*')
    Default = Square


class Vector2:
    def __init__(self, x=None, y=None):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Vector2(
            self.x+other.x,
            self.y+other.y
        )

    def __sub__(self, other):
        return Vector2(
            self.x-other.x,
            self.y-other.y
        )

    def __repr__(self):
        return '<Vector2(x={},y={})>'.format(
            self.x, self.y
        )

    def __str__(self):
        return '(x={},y={})'.format(
            self.x, self.y
        )


class Dir(enum.Enum):
    Left = Vector2(-2, 0)
    Right = Vector2(2, 0)
    Up = Vector2(0, -1)
    Down = Vector2(0, 1)


class Rect:
    """
    Rectangle.
    """
    def __init__(self, x1=0, y1=0, x2=0, y2=0):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    @property
    def lb(self):
        """
        Left bottom
        """
        return Vector2(self.x1, self.y1)

    @property
    def lt(self):
        """
        Left top
        """
        return Vector2(self.x1, self.y2)

    @property
    def rb(self):
        """
        Right bottom
        """
        return Vector2(self.x2, self.y1)

    @property
    def rt(self):
        """
        Right top
        """
        return Vector2(self.x2, self.y2)

    def get_pos(self):
        return self.get_center()

    def get_center(self):
        return Vector2(
            self.x1 + (self.x2 - self.x1),
            self.y1 + (self.y2 - self.y1)
        )

    def get_width(self):
        return abs(self.x2 - self.x1) + 1

    def get_height(self):
        return abs(self.y2 - self.y1) + 1

    def __repr__(self):
        return '<Rect(lb={},lt={},rt={},rb={},w={},h={})>'.format(
            str(self.lb),
            str(self.lt),
            str(self.rt),
            str(self.rb),
            self.get_width(),
            self.get_height(),
        )


class Cell:
    """
    Cell.
    """
    def __init__(self, x=None, y=None, fg=None, bg=None, c=None):
        self.c = c or Shape.Default.value
        self.x = x
        self.y = y
        self.fg = fg or Color.Default
        self.bg = bg or Color.Default


class Size(enum.IntEnum):
    w1xh1 = 1
    w3xh3 = 3
    w5xh5 = 5
    w7xh7 = 7
    w9xh9 = 9
    w11xh11 = 11
    w13xh13 = 13
    w15xh15 = 15
    w17xh17 = 17
    w19xh19 = 19
    MinSize = w1xh1
    MaxSize = w19xh19


def render_objects(tm, objects):
    """
    Render objects
    """
    if not tm:
        raise RuntimeError('Null terminal')
    if not tm.tb:
        raise RuntimeError('Null termbox')
    if not tm.player:
        raise RuntimeError('Null player')

    center = tm.center()
    player_pos = tm.player.get_pos()
    for o in objects:
        if not o:
            continue
        o.render(
            tm,
            dx=player_pos.x-center.x,
            dy=player_pos.y-center.y,
        )


def render(tm, cells):
    """
    Render cells
    """
    if not tm.tb:
        raise RuntimeError('Null termbox')
    for cell in cells:
        tm.tb.change_cell(
            cell.x,
            cell.y,
            cell.c,
            cell.fg,
            cell.bg
        )


class Renderable:
    """
    Renderable interface.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.pos = None
        self.prev_pos = None
        self.fg = None
        self.bg = None
        self.prev_direction = None
        self.direction = None

    def render(self, tm=None, dx=0, dy=0, check_intersect=True):
        """
        Render myself.
        """
        pos = self.get_pos()
        if not pos:
            logger.debug('Null pos')
            return
        size = self.get_size()
        fg, bg= self.get_color()

        rect = self.get_rect()
        left = rect.x1
        right = rect.x2
        bottom = rect.y1
        top = rect.y2

        if self.direction:
            trajectory = self.make_trajectory(rect=rect)
            #logger.debug('dir:{}, trajectory:{}'.format(self.direction, str(trajectory)))
        else:
            trajectory = rect
        if check_intersect and tm.map.intersectd_with(rect=trajectory):
            self.pos = self.prev_pos or self.pos
            self.render(tm, dx, dy, check_intersect=False)

        cells = []
        for y in range(bottom, top+1):
            for x in range(left, right+1):
                cell = Cell(x=x-dx, y=y-dy, fg=fg, bg=bg, c=self.get_shape())
                cells.append(cell)
        if tm.debug:
            x = right + 1
            y = bottom + 1
            coord = "xy({},{}),w={},y={}".format(
                x, y, self.get_width(), self.get_height()
            )
            for c in coord:
                cell = Cell(x=x-dx, y=y-dy, fg=fg, c=ord(c))
                cells.append(cell)
                x += 1

        render(tm, cells)

    def move(self, direction: Dir=None, pos: Vector2=None):
        self.prev_direction = self.direction
        if direction:
            self.direction = direction
            self.prev_pos = copy.deepcopy(self.pos)
            self.pos += direction.value
            logger.debug('{} {} {} {}'.format(direction, direction.name, direction.value, self.pos))
        if pos:
            self.prev_pos = copy.deepcopy(self.pos)
            self.pos = pos

    def get_rect(self):
        pos = self.get_pos()
        size = self.get_size()
        diameter = Vector2()
        diameter.y = int((size - 1) / 2)
        diameter.x = int((size - 1) / 2)
        left = pos.x - diameter.x
        right = pos.x + diameter.x
        bottom = pos.y - diameter.y
        top = pos.y + diameter.y
        rect = Rect(
            x1=left,
            y1=bottom,
            x2=right,
            y2=top,
        )
        return rect

    def make_trajectory(self, rect=None):
        rect = rect or self.get_rect()
        if self.direction == Dir.Left:
            trajectory = Rect(
                x1=rect.x1,
                y1=rect.y1,
                x2=rect.x2-Dir.Left.value.x,
                y2=rect.y2,
            )
        elif self.direction == Dir.Right:
            trajectory = Rect(
                x1=rect.x1-Dir.Right.value.x,
                y1=rect.y1,
                x2=rect.x2,
                y2=rect.y2,
            )
        elif self.direction == Dir.Up:
            trajectory = Rect(
                x1=rect.x1,
                y1=rect.y1-Dir.Up.value.y,
                x2=rect.x2,
                y2=rect.y2,
            )
        elif self.direction == Dir.Down:
            trajectory = Rect(
                x1=rect.x1,
                y1=rect.y1,
                x2=rect.x2,
                y2=rect.y2-Dir.Down.value.y,
            )
        else:
            trajectory = rect
        return trajectory

    @abc.abstractmethod
    def get_size(self) -> Size:
        pass

    """
    @abc.abstractmethod
    def get_pos(self):
        pass
    """

    @abc.abstractmethod
    def get_width(self):
        pass

    @abc.abstractmethod
    def get_height(self):
        pass

    def set_color(self, fg=None, bg=None):
        self.fg = fg
        self.bg = bg
        if self.fg == Color.Random:
            self.fg = Color.random_color()
        if self.bg == Color.Random:
            self.bg = Color.random_color()

    def get_color(self):
        return self.fg, self.bg

    @abc.abstractmethod
    def get_shape(self):
        return None


class Map(Renderable):
    """
    Map class.
    """
    def __init__(self):
        self.data = []
        self._lb = None
        self._lt = None
        self._rb = None
        self._rt = None

    def load(self, mapfile):
        with open(mapfile) as f:
            for line in f:
                if not line:
                    continue
                self.data.append(line.strip())
        self._lt = Vector2(0, 0)
        self._lb = Vector2(0, len(self.data))
        self._rt = Vector2(len(self.data[0]), 0)
        self._rb = Vector2(len(self.data[0]), len(self.data))

    def render(self, tm=None, dx=0, dy=0):
        cells = []
        for y, line in enumerate(self.data):
            for x, c in enumerate(line):
                cell = Cell(x=x-dx, y=y-dy, fg=Color.White, c=ord(c))
                cells.append(cell)

        render(tm, cells)

    def intersectd_with(self, pos: Vector2=None, rect: Rect=None):
        """
        """
        if pos:
            try:
                v = self.data[pos.y][pos.x].strip()
                if v:
                    return True
                else:
                    return False
            except IndexError:
                return True
        elif rect:
            if self.intersectd_with(rect.lb) or \
                self.intersectd_with(rect.lt) or \
                self.intersectd_with(rect.rb) or \
                self.intersectd_with(rect.rt):
                return True
            else:
                return False
        else:
            pass

    @property
    def lb(self):
        """
        Left bottom
        """
        return self._lb

    @property
    def lt(self):
        """
        Left top
        """
        return self._lt

    @property
    def rb(self):
        """
        Right bottom
        """
        return self._rb

    @property
    def rt(self):
        """
        Right top
        """
        return self._rt

    @property
    def boundary(self):
        return Rect(
            self.lt.x,
            self.lt.y,
            self.rb.x,
            self.rb.y,
        )


class MouseKey(enum.Enum):
    ESC = KEY_ESC
    Left = KEY_ARROW_LEFT
    Right = KEY_ARROW_RIGHT
    Up = KEY_ARROW_UP
    Down = KEY_ARROW_DOWN
    a = 'a'
    b = 'b'
    c = 'c'
    d = 'd'
    e = 'e'
    f = 'f'
    g = 'g'
    h = 'h'
    i = 'i'
    j = 'j'
    k = 'k'
    l = 'l'
    m = 'm'
    n = 'n'
    o = 'o'
    p = 'p'
    q = 'q'
    r = 'r'
    s = 's'
    t = 't'
    u = 'u'
    v = 'v'
    w = 'w'
    x = 'x'
    y = 'y'
    z = 'z'


class Terminal:
    """
    Terminal class.
    """
    def __init__(self):
        self.tb = Termbox()
        self.debug = False
        self.player = None
        self.map = Map()
        self.map.load(os.path.join(mapdir, 'map.txt'))
        self._keydown_handlers = dict()
        self._on_shutdown = None

    def close(self):
        self.tb.close()
        self.tb = None

    def login(self, player):
        self.player = player

    def set_keydown_handler(self, keys, cb):
        if isinstance(keys, list):
            for key in keys:
                self._keydown_handlers.update({key.value: cb})
        else:
            key = keys
            self._keydown_handlers.update({key.value: cb})

    def get_keydown_handler(self, keyvalue):
        return self._keydown_handlers.get(keyvalue)

    @property
    def on_shutdown(self):
        return self._on_shutdown

    @on_shutdown.setter
    def on_shutdown(self, f):
        self._on_shutdown = f

    @property
    def width(self):
        return self.tb.width()

    @property
    def height(self):
        return self.tb.height()

    @property
    def boundary(self):
        return Rect(x1=0, y1=0, x2=self.width, y2=self.height)

    def center(self):
        x = int(self.width / 2)
        y = int(self.height / 2)
        return Vector2(x, y)

    def clear(self):
        """
        Clear the console
        """
        self.tb.clear()

    def update(self, now, player, objects):
        """
        """
        self.clear()
        self.peek_key_event()
        render_objects(self, [self.map])
        render_objects(self, objects)
        render_objects(self, [player])
        self.tb.present()

    def peek_key_event(self):
        try:
            if not self.tb:
                raise RuntimeError('Null termbox')

            type_, uch, key, mod, w, h, x, y = self.tb.peek_event()
            logger.debug('type:{type},uch={uch},key={key},mod={mod},w={w},h={h},x={x},y={y}'.format(
                type=type_,
                uch=uch,
                key=key,
                mod=mod,
                w=w, h=h, x=x, y=y
            ))
            if key is not None:
                cb = self.get_keydown_handler(key)
                if cb:
                    cb(key)
                if key == KEY_ESC:
                    self.close()
                    if self.on_shutdown:
                        self.on_shutdown()
            if uch:
                cb = self.get_keydown_handler(uch)
                if cb:
                    cb(key)

        except TypeError as e:
            pass
            #logger.error(e)
            #logger.error(traceback.format_exc())
