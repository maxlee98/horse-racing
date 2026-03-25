"""Custom exceptions for the betting game."""


class GameException(Exception):
    """Base exception for all game-related errors."""
    pass


class RoomNotFoundException(GameException):
    """Raised when a room is not found."""
    pass


class NotAuthorizedException(GameException):
    """Raised when a user is not authorized to perform an action."""
    pass


class InvalidBetException(GameException):
    """Raised when a bet is invalid."""
    pass


class RoomFullException(GameException):
    """Raised when a room is full."""
    pass


class InvalidOperationException(GameException):
    """Raised when an operation cannot be performed in current state."""
    pass


class GameModeNotSupportedException(GameException):
    """Raised when a game mode is not supported."""
    pass
