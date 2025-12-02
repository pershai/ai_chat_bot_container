"""
Dynamic prompt templates for the AI agent.

This module provides configurable system prompts that can be customized
based on user preferences, conversation context, and bot capabilities.
"""

from dataclasses import dataclass


@dataclass
class BotCapabilities:
    """Define what the bot can do"""

    rag_search: bool = True
    internet_search: bool = False
    document_upload: bool = True
    conversation_history: bool = True

    def to_string(self) -> str:
        """Convert capabilities to human-readable string"""
        caps = []
        if self.rag_search:
            caps.append("search your uploaded documents")
        if self.internet_search:
            caps.append("search the internet")
        if self.document_upload:
            caps.append("help you manage your knowledge base")
        if self.conversation_history:
            caps.append("remember our conversation history")

        return ", ".join(caps) if caps else "answer your questions"


class PromptTemplates:
    """Centralized prompt template management"""

    # Base system prompt template
    SYSTEM_BASE = """You are {bot_name}, a helpful and knowledgeable AI assistant.

Your capabilities include: {capabilities}

{context_info}

Please be concise, accurate, and helpful in your responses."""

    # Tool usage instructions
    TOOL_USAGE_STRICT = """Your standard procedure for EVERY user query:

1. ALWAYS verify the user input using the 'verify_input' tool first
2. If the input is safe, search the knowledge base using 'search_rag'
3. If you find relevant information in the RAG, answer based on that information
4. If the RAG search returns no results or 'No relevant information found', you MUST answer: 'I can't find the information about your topic'
5. Do NOT use internet search unless the user explicitly asks for it
6. ALWAYS verify your final answer using 'verify_output' before responding

Follow these steps in order for every query."""

    TOOL_USAGE_FLEXIBLE = """You have access to several tools to help answer questions:

- verify_input: Check if user input is safe (use for potentially sensitive queries)
- search_rag: Search the user's uploaded documents (use when the question might be answered by their documents)
- search_internet: Search the web (only use if explicitly requested or if RAG has no results and user wants current information)
- verify_output: Validate your response (use for important or sensitive responses)

Use your judgment to decide which tools are appropriate for each query."""

    # Context-specific additions
    CONTEXT_WITH_HISTORY = """
Current conversation context:
- We have been discussing: {conversation_summary}
- Previous topics: {topics}
"""

    CONTEXT_WITH_DOCUMENTS = """
Available knowledge base:
- You have access to {doc_count} uploaded documents
- Topics covered: {doc_topics}
"""

    CONTEXT_FIRST_MESSAGE = """
This is the start of a new conversation. Introduce yourself briefly and ask how you can help."""

    # Personality variations
    PERSONALITY_PROFESSIONAL = "Maintain a professional and formal tone."
    PERSONALITY_FRIENDLY = "Be warm, friendly, and conversational."
    PERSONALITY_CONCISE = "Keep responses brief and to the point."
    PERSONALITY_DETAILED = "Provide detailed explanations with examples."

    @classmethod
    def get_system_prompt(
        cls,
        bot_name: str = "AI Assistant",
        capabilities: BotCapabilities | None = None,
        tool_usage_mode: str = "strict",  # "strict" or "flexible"
        conversation_context: dict | None = None,
        user_preferences: dict | None = None,
        is_first_message: bool = False,
    ) -> str:
        """
        Generate a dynamic system prompt based on context and preferences.

        Args:
            bot_name: Name of the bot
            capabilities: BotCapabilities object defining what the bot can do
            tool_usage_mode: "strict" for enforced tool usage, "flexible" for agent discretion
            conversation_context: Dict with conversation history info
            user_preferences: Dict with user-specific preferences (personality, etc.)
            is_first_message: Whether this is the first message in a conversation

        Returns:
            Complete system prompt string
        """
        if capabilities is None:
            capabilities = BotCapabilities()

        if user_preferences is None:
            user_preferences = {}

        # Build context information
        context_parts = []

        # Add conversation context
        if conversation_context:
            if is_first_message:
                context_parts.append(cls.CONTEXT_FIRST_MESSAGE)
            elif conversation_context.get("summary"):
                context_parts.append(
                    cls.CONTEXT_WITH_HISTORY.format(
                        conversation_summary=conversation_context.get("summary", ""),
                        topics=", ".join(conversation_context.get("topics", [])),
                    )
                )

        # Add document context
        if conversation_context and conversation_context.get("doc_count", 0) > 0:
            context_parts.append(
                cls.CONTEXT_WITH_DOCUMENTS.format(
                    doc_count=conversation_context.get("doc_count", 0),
                    doc_topics=", ".join(
                        conversation_context.get("doc_topics", ["various topics"])
                    ),
                )
            )

        # Add personality
        personality = user_preferences.get("personality", "friendly")
        if personality == "professional":
            context_parts.append(cls.PERSONALITY_PROFESSIONAL)
        elif personality == "friendly":
            context_parts.append(cls.PERSONALITY_FRIENDLY)
        elif personality == "concise":
            context_parts.append(cls.PERSONALITY_CONCISE)
        elif personality == "detailed":
            context_parts.append(cls.PERSONALITY_DETAILED)

        context_info = "\n".join(context_parts) if context_parts else ""

        # Build base prompt
        base_prompt = cls.SYSTEM_BASE.format(
            bot_name=bot_name,
            capabilities=capabilities.to_string(),
            context_info=context_info,
        )

        # Add tool usage instructions
        if tool_usage_mode == "strict":
            tool_instructions = cls.TOOL_USAGE_STRICT
        else:
            tool_instructions = cls.TOOL_USAGE_FLEXIBLE

        # Combine all parts
        full_prompt = f"{base_prompt}\n\n{tool_instructions}"

        return full_prompt

    @classmethod
    def get_conversation_summary_prompt(cls, messages: list[str]) -> str:
        """
        Generate a prompt for summarizing conversation history.

        Args:
            messages: List of message contents to summarize

        Returns:
            Prompt for the LLM to generate a summary
        """
        conversation_text = "\n".join([f"- {msg}" for msg in messages])

        return f"""Please provide a brief summary of the following conversation in 2-3 sentences.
Focus on the main topics discussed and any important conclusions or decisions.

Conversation:
{conversation_text}

Summary:"""

    @classmethod
    def get_topic_extraction_prompt(cls, text: str) -> str:
        """
        Generate a prompt for extracting topics from text.

        Args:
            text: Text to extract topics from

        Returns:
            Prompt for topic extraction
        """
        return f"""Extract the main topics from the following text as a comma-separated list.
Limit to 3-5 most important topics.

Text: {text}

Topics:"""


# Preset configurations for common use cases
class PromptPresets:
    """Pre-configured prompt settings for common scenarios"""

    @staticmethod
    def customer_support() -> dict:
        """Configuration for customer support bot"""
        return {
            "bot_name": "Support Assistant",
            "capabilities": BotCapabilities(
                rag_search=True,
                internet_search=False,
                document_upload=True,
                conversation_history=True,
            ),
            "tool_usage_mode": "strict",
            "user_preferences": {"personality": "professional"},
        }

    @staticmethod
    def research_assistant() -> dict:
        """Configuration for research assistant bot"""
        return {
            "bot_name": "Research Assistant",
            "capabilities": BotCapabilities(
                rag_search=True,
                internet_search=True,
                document_upload=True,
                conversation_history=True,
            ),
            "tool_usage_mode": "flexible",
            "user_preferences": {"personality": "detailed"},
        }

    @staticmethod
    def quick_qa() -> dict:
        """Configuration for quick Q&A bot"""
        return {
            "bot_name": "Quick Assistant",
            "capabilities": BotCapabilities(
                rag_search=True,
                internet_search=False,
                document_upload=False,
                conversation_history=False,
            ),
            "tool_usage_mode": "flexible",
            "user_preferences": {"personality": "concise"},
        }
