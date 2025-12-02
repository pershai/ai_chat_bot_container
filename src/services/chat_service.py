from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage
from src.agent import app_graph, create_agent_state, AgentConfig
from src.core.cache import get_cached, set_cached, get_cache_key
from src.services import conversation_service
from src.memory import get_conversation_memory
import logging

logger = logging.getLogger(__name__)


async def process_chat(
    message: str,
    user_id: int,
    db: Session = None,
    conversation_id: int = None,
    bot_config: Optional[Dict[str, Any]] = None,
    enable_context_building: bool = True,
) -> str:
    """
    Process a chat message through the agent with enhanced features.

    Args:
        message: User's message
        user_id: User identifier
        db: Database session
        conversation_id: Optional conversation ID for history
        bot_config: Optional bot configuration (personality, mode, etc.)
        enable_context_building: Whether to build conversation context

    Returns:
        Agent's response string
    """
    logger.info(f"Processing chat for user {user_id}, conversation {conversation_id}")

    # Check cache first (only if no conversation_id, as history changes context)
    if not conversation_id:
        cache_key = get_cache_key("chat", user_id, message)
        cached_response = get_cached(cache_key)
        if cached_response:
            logger.info("Returning cached response")
            return cached_response

    # Prepare messages list
    messages = []

    # Load history if conversation_id is provided
    if conversation_id and db:
        try:
            history = conversation_service.get_conversation_messages(
                db, conversation_id
            )
            for msg in history:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    messages.append(AIMessage(content=msg.content))
            logger.info(f"Loaded {len(messages)} messages from conversation history")
        except Exception as e:
            logger.error(f"Failed to load conversation history: {e}")
            # Continue without history

    # Add current message
    messages.append(HumanMessage(content=message))

    # Build conversation context if enabled
    conversation_context = None
    if enable_context_building and len(messages) > 1:
        try:
            memory = get_conversation_memory()

            # Get document count for this user (if we have db access)
            doc_count = 0
            doc_topics = []
            if db:
                try:
                    from src.models.document import Document

                    doc_count = (
                        db.query(Document).filter(Document.user_id == user_id).count()
                    )
                    # You could also extract topics from documents here
                except Exception as e:
                    logger.warning(f"Failed to get document count: {e}")

            # Build context
            conversation_context = await memory.get_conversation_context(
                messages=messages[:-1],  # Exclude current message
                doc_count=doc_count,
                doc_topics=doc_topics,
            )
            logger.debug(f"Built conversation context: {conversation_context}")
        except Exception as e:
            logger.warning(f"Failed to build conversation context: {e}")
            conversation_context = None

    # Create agent state with all enhancements
    try:
        state = create_agent_state(
            messages=messages,
            user_id=user_id,
            bot_config=bot_config,
            conversation_context=conversation_context,
            metadata={
                "conversation_id": conversation_id,
                "message_count": len(messages),
            },
        )

        # Process through agent
        logger.info("Invoking agent graph")
        result = await app_graph.ainvoke(state)

        # Extract response - handle both string and structured content
        last_message = result["messages"][-1]
        raw_content = last_message.content

        # Handle structured content (list of dicts with 'text' field)
        if isinstance(raw_content, list):
            # Extract text from structured response
            text_parts = []
            for item in raw_content:
                if isinstance(item, dict) and "text" in item:
                    text_parts.append(item["text"])
                elif isinstance(item, str):
                    text_parts.append(item)
            response = " ".join(text_parts) if text_parts else str(raw_content)
        elif isinstance(raw_content, dict):
            # If it's a dict, try to get 'text' field
            response = raw_content.get("text", str(raw_content))
        else:
            # Plain string response
            response = str(raw_content)

        logger.info(f"Agent response generated: {len(response)} chars")

    except Exception as e:
        logger.error(f"Agent processing failed: {e}", exc_info=True)
        response = (
            f"I apologize, but I encountered an error processing your request: {str(e)}"
        )

    # Save to database if conversation_id is provided
    if conversation_id and db:
        try:
            conversation_service.add_message(db, conversation_id, "user", message)
            conversation_service.add_message(db, conversation_id, "assistant", response)
            logger.info("Messages saved to database")
        except Exception as e:
            logger.error(f"Failed to save messages to database: {e}", exc_info=True)
            # Don't fail the request if we can't save to DB

    # Cache the response (only if no conversation_id)
    if not conversation_id:
        try:
            set_cached(cache_key, response, ttl=3600)
            logger.debug("Response cached")
        except Exception as e:
            logger.warning(f"Failed to cache response: {e}")

    return response


async def process_chat_with_config(
    message: str,
    user_id: int,
    db: Session = None,
    conversation_id: int = None,
    personality: str = "friendly",
    tool_mode: str = "strict",
    enable_internet: bool = False,
) -> str:
    """
    Convenience function to process chat with specific configuration.

    Args:
        message: User's message
        user_id: User identifier
        db: Database session
        conversation_id: Optional conversation ID
        personality: Bot personality ("friendly", "professional", "concise", "detailed")
        tool_mode: Tool usage mode ("strict" or "flexible")
        enable_internet: Whether to enable internet search

    Returns:
        Agent's response string
    """
    # Create bot configuration
    config = AgentConfig(
        personality=personality,
        tool_usage_mode=tool_mode,
        enable_internet_search=enable_internet,
    )

    return await process_chat(
        message=message,
        user_id=user_id,
        db=db,
        conversation_id=conversation_id,
        bot_config=config.to_dict(),
    )
