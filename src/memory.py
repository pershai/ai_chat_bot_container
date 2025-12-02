"""
Conversation memory and context management.

This module handles conversation summarization, context window management,
and intelligent memory retention for long conversations.
"""

import tiktoken
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from src.core.config import config
from src.prompts import PromptTemplates


class ConversationMemory:
    """
    Manages conversation memory with automatic summarization.

    Keeps recent messages in full detail while summarizing older messages
    to stay within token limits.
    """

    def __init__(
        self,
        max_tokens: int = 4000,
        recent_messages_count: int = 10,
        encoding_name: str = "cl100k_base",
    ):
        """
        Initialize conversation memory manager.

        Args:
            max_tokens: Maximum tokens to keep in context
            recent_messages_count: Number of recent messages to keep in full
            encoding_name: Tokenizer encoding to use
        """
        self.max_tokens = max_tokens
        self.recent_messages_count = recent_messages_count
        self.encoding = tiktoken.get_encoding(encoding_name)
        self._llm = None
        self.summary_cache: dict[str, str] = {}

    def get_llm(self):
        """Lazy load LLM instance"""
        if self._llm is None:
            self._llm = ChatGoogleGenerativeAI(
                google_api_key=config.GOOGLE_API_KEY, model=config.LLM_MODEL_NAME
            )
        return self._llm

    def count_tokens(self, messages: list[BaseMessage]) -> int:
        """
        Count total tokens in a list of messages.

        Args:
            messages: List of messages to count

        Returns:
            Total token count
        """
        total = 0
        for msg in messages:
            content = str(msg.content)
            total += len(self.encoding.encode(content))
        return total

    def _extract_message_contents(self, messages: list[BaseMessage]) -> list[str]:
        """Extract content strings from messages for summarization"""
        contents = []
        for msg in messages:
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            contents.append(f"{role}: {msg.content}")
        return contents

    async def summarize_messages(self, messages: list[BaseMessage]) -> str:
        """
        Summarize a list of messages into a concise summary.

        Args:
            messages: Messages to summarize

        Returns:
            Summary text
        """
        # Create cache key from message contents
        cache_key = str(hash(tuple(str(m.content) for m in messages)))

        # Check cache
        if cache_key in self.summary_cache:
            return self.summary_cache[cache_key]

        # Extract message contents
        message_contents = self._extract_message_contents(messages)

        # Generate summary prompt
        summary_prompt = PromptTemplates.get_conversation_summary_prompt(
            message_contents
        )

        # Get summary from LLM
        response = await self.get_llm().ainvoke([HumanMessage(content=summary_prompt)])
        summary = response.content

        # Cache the summary
        self.summary_cache[cache_key] = summary

        return summary

    async def manage_context(
        self, messages: list[BaseMessage], force_summarize: bool = False
    ) -> tuple[list[BaseMessage], str | None]:
        """
        Manage conversation context by summarizing old messages if needed.

        Args:
            messages: Current message history
            force_summarize: Force summarization even if under token limit

        Returns:
            Tuple of (managed_messages, summary_text)
            - managed_messages: Optimized message list
            - summary_text: Summary of older messages (if created)
        """
        token_count = self.count_tokens(messages)

        # If under limit and not forcing, return as-is
        if token_count <= self.max_tokens and not force_summarize:
            return messages, None

        # If we have few messages, just return them (nothing to summarize)
        if len(messages) <= self.recent_messages_count:
            return messages, None

        # Split into old and recent messages
        old_messages = messages[: -self.recent_messages_count]
        recent_messages = messages[-self.recent_messages_count :]

        # Summarize old messages
        summary = await self.summarize_messages(old_messages)

        # Create a system message with the summary
        summary_message = SystemMessage(
            content=f"Previous conversation summary: {summary}"
        )

        # Combine summary with recent messages
        managed_messages = [summary_message] + recent_messages

        return managed_messages, summary

    async def extract_topics(self, messages: list[BaseMessage]) -> list[str]:
        """
        Extract main topics from conversation.

        Args:
            messages: Messages to analyze

        Returns:
            List of topic strings
        """
        # Combine message contents
        message_contents = self._extract_message_contents(messages)
        combined_text = "\n".join(message_contents)

        # Generate topic extraction prompt
        topic_prompt = PromptTemplates.get_topic_extraction_prompt(combined_text)

        # Get topics from LLM
        response = await self.get_llm().ainvoke([HumanMessage(content=topic_prompt)])
        topics_text = response.content

        # Parse comma-separated topics
        topics = [t.strip() for t in topics_text.split(",")]

        return topics[:5]  # Limit to 5 topics

    async def get_conversation_context(
        self,
        messages: list[BaseMessage],
        doc_count: int = 0,
        doc_topics: list[str] | None = None,
    ) -> dict:
        """
        Generate conversation context dictionary for prompt generation.

        Args:
            messages: Current conversation messages
            doc_count: Number of documents in user's knowledge base
            doc_topics: Topics covered by user's documents

        Returns:
            Context dictionary with summary, topics, and document info
        """
        context = {"doc_count": doc_count, "doc_topics": doc_topics or []}

        # If we have enough messages, generate summary and topics
        if len(messages) >= 4:
            # Get summary of conversation so far
            summary = await self.summarize_messages(
                messages[:-1]
            )  # Exclude current message
            context["summary"] = summary

            # Extract topics
            topics = await self.extract_topics(messages)
            context["topics"] = topics

        return context

    def clear_cache(self):
        """Clear the summary cache"""
        self.summary_cache.clear()


class ContextWindowManager:
    """
    Manages the context window for LLM calls.

    Ensures we stay within token limits while preserving important context.
    """

    def __init__(self, max_tokens: int = 8000):
        """
        Initialize context window manager.

        Args:
            max_tokens: Maximum tokens for the entire context (prompt + completion)
        """
        self.max_tokens = max_tokens
        self.memory = ConversationMemory(
            max_tokens=int(max_tokens * 0.7)
        )  # 70% for context

    async def prepare_messages(
        self,
        messages: list[BaseMessage],
        system_prompt: str,
        reserve_tokens: int = 1000,
    ) -> list[BaseMessage]:
        """
        Prepare messages for LLM call, ensuring they fit within token limits.

        Args:
            messages: Conversation messages
            system_prompt: System prompt to prepend
            reserve_tokens: Tokens to reserve for completion

        Returns:
            Optimized message list ready for LLM
        """
        # Calculate available tokens for messages
        available_tokens = self.max_tokens - reserve_tokens

        # Create system message
        system_message = SystemMessage(content=system_prompt)

        # Manage conversation context
        managed_messages, _ = await self.memory.manage_context(messages)

        # Combine system message with managed messages
        final_messages = [system_message] + managed_messages

        # Final token check
        total_tokens = self.memory.count_tokens(final_messages)

        # If still over limit, truncate from the beginning (after system message)
        # But always keep at least one non-system message for Gemini API
        while total_tokens > available_tokens and len(final_messages) > 2:
            # Remove the oldest non-system message (keep system message + at least 1 user message)
            final_messages.pop(1)
            total_tokens = self.memory.count_tokens(final_messages)

        # Ensure we have at least one non-system message
        non_system_count = sum(
            1 for m in final_messages if not isinstance(m, SystemMessage)
        )
        if non_system_count == 0 and managed_messages:
            # If we somehow lost all non-system messages, add back the last one
            final_messages.append(managed_messages[-1])

        return final_messages


# Singleton instances for easy access
_memory_instance: ConversationMemory | None = None
_context_manager_instance: ContextWindowManager | None = None


def get_conversation_memory() -> ConversationMemory:
    """Get singleton conversation memory instance"""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = ConversationMemory()
    return _memory_instance


def get_context_window_manager() -> ContextWindowManager:
    """Get singleton context window manager instance"""
    global _context_manager_instance
    if _context_manager_instance is None:
        _context_manager_instance = ContextWindowManager()
    return _context_manager_instance
