import tiktoken
from typing import List, Any
from ..models.gpt_model import GPTModel, GPT_4o_mini


# --- Token Estimation ---
def num_tokens_from_string(string: str, gpt_model: GPTModel = GPT_4o_mini) -> int:
    encoding = tiktoken.encoding_for_model(gpt_model.model_name)
    return len(encoding.encode(string))


def num_tokens_from_messages(
    messages: List[Any], model_name: str = "gpt-4o-mini"
) -> int:
    """
    Estimate the number of tokens in a list of LangChain messages.

    Args:
        messages: List of LangChain message objects (HumanMessage, AIMessage, SystemMessage, etc.)
        model_name: The model name to use for encoding

    Returns:
        Estimated token count
    """
    try:
        encoding = tiktoken.encoding_for_model(model_name)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    num_tokens = 0

    for message in messages:
        # Each message has overhead for role formatting
        num_tokens += (
            4  # Every message follows <im_start>{role/name}\n{content}<im_end>\n
        )

        # Get message content
        if hasattr(message, "content"):
            content = message.content
            if isinstance(content, str):
                num_tokens += len(encoding.encode(content))
            elif isinstance(content, list):
                # Handle structured content (for multimodal messages)
                num_tokens += len(encoding.encode(str(content)))

        # Add tokens for tool calls if present
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
                num_tokens += len(encoding.encode(str(tool_call)))

    num_tokens += 2  # Every reply is primed with <im_start>assistant

    return num_tokens


if __name__ == "__main__":
    test_strings = ["\n", " ", "  ", "\t"]
    for test_string in test_strings:
        print(
            f"Number of tokens in '{test_string}': {num_tokens_from_string(test_string)}"
        )
