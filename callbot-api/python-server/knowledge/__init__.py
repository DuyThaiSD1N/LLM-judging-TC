"""Knowledge module - Knowledge base management"""

from .knowledge_base import (
    KnowledgeBase,
    get_knowledge_base,
    search_relevant_knowledge
)

__all__ = [
    'KnowledgeBase',
    'get_knowledge_base',
    'search_relevant_knowledge'
]
