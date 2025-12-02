import logging
from typing import TypedDict, Optional, Dict, Any, Literal
from typing import Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END, START

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from src.tools import verify_input, search_rag, search_internet, verify_output
from src.core.config import config
from src.prompts import PromptTemplates, BotCapabilities
from src.memory import get_context_window_manager, get_conversation_memory


logger = logging.getLogger(__name__)


# Define the enhanced state
class AgentState(TypedDict):
    """Agent state"""

    messages: Annotated[list[BaseMessage], add_messages]
    user_id: int
    # Optional configuration
    bot_config: Optional[Dict[str, Any]]
    # Context information
    conversation_context: Optional[Dict[str, Any]]
    # Metadata
    metadata: Optional[Dict[str, Any]]


# Agent configuration
class AgentConfig:
    """Configuration for agent behavior"""

    def __init__(
        self,
        bot_name: str = "AI Assistant",
        tool_usage_mode: str = "strict",  # "strict" or "flexible"
        personality: str = "friendly",  # "professional", "friendly", "concise", "detailed"
        enable_memory: bool = True,
        enable_internet_search: bool = False,
        max_context_tokens: int = 4000,
    ):
        self.bot_name = bot_name
        self.tool_usage_mode = tool_usage_mode
        self.personality = personality
        self.enable_memory = enable_memory
        self.enable_internet_search = enable_internet_search
        self.max_context_tokens = max_context_tokens

        # Create capabilities based on config
        self.capabilities = BotCapabilities(
            rag_search=True,
            internet_search=enable_internet_search,
            document_upload=True,
            conversation_history=enable_memory,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "bot_name": self.bot_name,
            "tool_usage_mode": self.tool_usage_mode,
            "personality": self.personality,
            "enable_memory": self.enable_memory,
            "enable_internet_search": self.enable_internet_search,
            "max_context_tokens": self.max_context_tokens,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        """Create config from dictionary"""
        return cls(**data)


# Default configuration
DEFAULT_CONFIG = AgentConfig()

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    google_api_key=config.GOOGLE_API_KEY, model=config.LLM_MODEL_NAME
)

# Bind tools
tools = [verify_input, search_rag, search_internet, verify_output]
llm_with_tools = llm.bind_tools(tools)

# Initialize memory and context managers
memory_manager = get_conversation_memory()
context_manager = get_context_window_manager()


# Define the agent node with dynamic prompts
async def agent(state: AgentState):
    """
    Main agent node that processes messages and decides on tool usage.

    Uses dynamic prompts based on configuration and conversation context.
    """
    messages = state["messages"]
    user_id = state.get("user_id")

    # Get or create agent config
    bot_config = state.get("bot_config", {})
    agent_config = AgentConfig.from_dict(bot_config) if bot_config else DEFAULT_CONFIG

    # Get conversation context
    conversation_context = state.get("conversation_context", {})

    # Check if this is the first message
    is_first_message = len(messages) == 1

    # Generate dynamic system prompt
    system_prompt = PromptTemplates.get_system_prompt(
        bot_name=agent_config.bot_name,
        capabilities=agent_config.capabilities,
        tool_usage_mode=agent_config.tool_usage_mode,
        conversation_context=conversation_context,
        user_preferences={"personality": agent_config.personality},
        is_first_message=is_first_message,
    )

    logger.info("[Agent] Processing message for user %s", user_id)
    logger.debug("[Agent] System prompt: %s...", system_prompt[:100])

    # Validate we have messages to process
    if not messages:
        logger.error("[Agent] No messages provided")

        return {"messages": [AIMessage(content="Error: No messages to process")]}

    # Manage context window if memory is enabled
    if agent_config.enable_memory and len(messages) > 5:
        try:
            prepared_messages = await context_manager.prepare_messages(
                messages=messages, system_prompt=system_prompt, reserve_tokens=1000
            )
            logger.info(
                "[Agent] Context managed: %d -> %d messages",
                len(messages),
                len(prepared_messages),
            )
        except Exception as e:  # pylint: disable=broad-except
            logger.warning(
                "[Agent] Context management failed: %s, using original messages",
                e,
                exc_info=True,
            )
            prepared_messages = [SystemMessage(content=system_prompt)] + messages
    else:
        # Simple approach: prepend system message
        prepared_messages = [SystemMessage(content=system_prompt)] + messages

    # Ensure we have at least one non-system message for Gemini API
    non_system_messages = [
        m for m in prepared_messages if not isinstance(m, SystemMessage)
    ]
    if not non_system_messages:
        logger.error("[Agent] No non-system messages found after preparation")
        return {"messages": [AIMessage(content="Error: No user messages to process")]}

    # Log message structure for debugging
    msg_structure = [
        f"{type(m).__name__}(len={len(str(m.content))})" for m in prepared_messages
    ]
    logger.debug("[Agent] Prepared messages structure: %s", msg_structure)

    # Invoke LLM with tools
    try:
        response = llm_with_tools.invoke(prepared_messages)
        logger.info(
            "[Agent] LLM response received, has tool calls: %s",
            bool(response.tool_calls),
        )
    except Exception as e:
        logger.error("[Agent] LLM invocation failed: %s", e)
        # Log full message details on failure
        for i, m in enumerate(prepared_messages):
            logger.error(
                "Msg %d: %s Content: %s...", i, type(m).__name__, str(m.content)[:100]
            )
        # Return error message
        return {"messages": [AIMessage(content=f"I encountered an error: {str(e)}")]}

    # Pass state to tool calls if they need user_id
    if hasattr(response, "tool_calls") and response.tool_calls:
        for tool_call in response.tool_calls:
            if "state" in tool_call.get("args", {}):
                tool_call["args"]["state"] = state

    return {"messages": [response]}


# Custom tool node that passes state to tools
def call_tools(state: AgentState):
    """
    Execute tool calls from the agent's response.

    Handles state injection for tools that need user context.
    """
    logger.debug("[Tools] State keys: %s", state.keys())
    logger.debug("[Tools] user_id: %s", state.get("user_id"))

    messages = state["messages"]
    last_message = messages[-1]

    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        logger.warning("[Tools] No tool calls found in last message")
        return {"messages": []}

    logger.info("[Tools] Executing %d tool calls", len(last_message.tool_calls))

    tool_results = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        logger.debug("[Tools] Calling tool: %s with args: %s", tool_name, tool_args)

        # Find the tool
        tool_map = {t.name: t for t in tools}
        if tool_name not in tool_map:
            logger.error("[Tools] Tool not found: %s", tool_name)
            tool_results.append(
                ToolMessage(
                    content=f"Error: Tool '{tool_name}' not found",
                    tool_call_id=tool_call["id"],
                    name=tool_name,
                )
            )
            continue

        tool = tool_map[tool_name]

        # Inject state for tools that need it
        if tool_name == "search_rag":
            tool_args["state"] = {"user_id": state.get("user_id")}
            logger.debug("[Tools] Injected state into search_rag: %s", tool_args)

        # Call the tool with error handling
        try:
            result = tool.invoke(tool_args)
            logger.info("[Tools] Tool %s executed successfully", tool_name)
            logger.debug("[Tools] Result preview: %s...", str(result)[:100])
        except Exception as e:
            logger.error("[Tools] Tool %s failed: %s", tool_name, e)
            result = f"Error executing {tool_name}: {str(e)}"

        # Create tool message
        tool_results.append(
            ToolMessage(
                content=str(result), tool_call_id=tool_call["id"], name=tool_name
            )
        )

    return {"messages": tool_results}


# Define the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", agent)
workflow.add_node("tools", call_tools)

# Add edges
workflow.add_edge(START, "agent")


def should_continue(state: AgentState) -> Literal["tools", END]:
    """
    Determine if we should continue to tools or end the conversation.
    """
    messages = state["messages"]
    if not messages:
        return END

    last_message = messages[-1]

    # Check if there are tool calls
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.debug(
            "[Router] Continuing to tools (%d calls)", len(last_message.tool_calls)
        )
        return "tools"

    logger.debug("[Router] Ending conversation")
    return END


workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

# Compile the graph
app_graph = workflow.compile()


# Helper function to create initial state
def create_agent_state(
    messages: list[BaseMessage],
    user_id: int,
    bot_config: Optional[Dict[str, Any]] = None,
    conversation_context: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AgentState:
    """
    Create an agent state with all necessary fields.

    Args:
        messages: List of conversation messages
        user_id: User identifier
        bot_config: Optional bot configuration
        conversation_context: Optional conversation context
        metadata: Optional metadata

    Returns:
        Complete AgentState dictionary
    """
    return {
        "messages": messages,
        "user_id": user_id,
        "bot_config": bot_config,
        "conversation_context": conversation_context,
        "metadata": metadata,
    }
