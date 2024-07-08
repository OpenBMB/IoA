from common.registry import Registry

memory_registry = Registry(name="MemoryRegistry")

from .base import BaseMemory
from .chat_history import ChatHistoryMemory
