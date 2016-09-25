from enum import IntEnum


class StatusCode(IntEnum):
    OK = 0
    GameExit = 1


class GameExit(Exception):
    pass

