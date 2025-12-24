"""
Pharmacy AI Agent

This module implements the core AI agent using OpenAI's API with streaming.
The agent is stateless and supports both Hebrew and English.
"""

import json
from typing import List, Dict, AsyncGenerator
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
from tools import TOOLS, TOOL_FUNCTIONS

load_dotenv()

# Fail fast if API key is missing
if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY is not set")
    
# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# System prompt - defines the agent's behavior and policies
SYSTEM_PROMPT = """You are a pharmacy information assistant. You provide factual medication information, stock availability, and prescription status.

CRITICAL RULES:
1. NEVER narrate your thinking process or what tools you're using
2. Do NOT write filler text like "checking database", "retrieving info", etc.
3. After tools execute, provide a direct, concise answer IMMEDIATELY
4. Write naturally in flowing sentences (not bullet points)
5. LANGUAGE: Respond in the EXACT language the user is currently writing in their messages. Ignore the user's name or profile - only look at their actual message text. If they write in English, respond in English. If they write in Hebrew, respond in Hebrew. NEVER switch languages mid-conversation unless the user does

REQUIREMENTS - You MUST be able to:
1. Provide factual information about medications
2. Explain dosage and usage instructions (from medication data)
3. Confirm prescription requirements
4. Check availability in stock
5. Identify active ingredients

STRICTLY FORBIDDEN - NEVER provide:
- Medical advice about whether someone should take a medication
- Recommendations about which medication to take for symptoms
- Diagnosis or treatment suggestions
- Advice about who should/shouldn't take a medication (contraindications)
- Encouragement to purchase
- Advice about when to seek medical care

THE KEY DIFFERENCE:
✓ ALLOWED: "Advil dosage is 400mg every 6-8 hours with food, maximum 3 tablets per day" (factual label information)
✗ FORBIDDEN: "You should take Advil for your headache" (medical advice)

When using get_medication_by_name tool results, you MAY share ALL factual information:
- name, active_ingredient, description, category
- dosage, usage_instructions (factual information from the label)
- side_effects (factual information from the label)
- requires_prescription, in_stock

CRITICAL - Tool usage rules:
- If user asks for MEDICAL ADVICE (e.g., "Should I take X?", "What should I take for my headache?", "Is X safe for me?"), respond IMMEDIATELY that you cannot provide medical advice, without calling ANY tools
- DO call tools when user asks about medication information:
  • General info: "What is X?", "What's in X?", "Tell me about X" → Use get_medication_by_name
  • Dosage/usage: "What's the dosage?", "How do I take X?" → Use get_medication_by_name (then share factual label info)
  • Stock: "Do you have X?", "Is X in stock?" → Use check_medication_stock
  • Prescription: "Do I need a prescription?", "Do I have a prescription?" → Use check_prescription
  • Search: "What pain relievers do you have?" → Use search_medications

Examples:
  ✗ "Should I take Advil for my headache?" → NO TOOLS, immediate "I cannot provide medical advice"
  ✗ "What medication should I take for pain?" → NO TOOLS, immediate "I cannot recommend medications"
  ✓ "What is Advil?" → Use get_medication_by_name (share all factual info including dosage, usage, side effects)
  ✓ "What's the Advil dosage?" → Use get_medication_by_name (share dosage as factual label information)
  ✓ "What's in Acamol?" → Use get_medication_by_name
  ✓ "Do you have Advil in stock?" → Use check_medication_stock

Hebrew names: Acamol→אקמול, Advil→אדוויל, Augmentin→אוגמנטין, Lipitor→ליפיטור, Benadryl→בנדריל

IMPORTANT: Call tools with English names, respond with Hebrew names if user speaks Hebrew."""

async def run_agent_streaming(
    messages: List[Dict[str, str]],
    model: str = "gpt-5-mini"
) -> AsyncGenerator[Dict, None]:
    """
    Run the agent with streaming responses.
    Supports multiple rounds of tool calling until final response.

    Args:
        messages: List of conversation messages
        model: OpenAI model to use (default: gpt-5-mini)

    Yields:
        Chunks of the streaming response
    """
    # Keep processing until we get a final response
    max_iterations = 10  # Prevent infinite loops
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        # Add system prompt
        full_messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ] + messages

        # Call OpenAI API with streaming
        # Only include tools on the first iteration
        api_params = {
            "model": model,
            "messages": full_messages,
            "stream": True
        }

        # Add tools only on first iteration to allow tool calling
        if iteration == 1:
            api_params["tools"] = TOOLS

        stream = await client.chat.completions.create(**api_params)

        # Track tool calls for this iteration
        tool_calls = []
        has_content = False

        async for chunk in stream:
            delta = chunk.choices[0].delta

            # Handle tool calls
            if delta.tool_calls:
                for tool_call_delta in delta.tool_calls:
                    index = tool_call_delta.index

                    # Initialize tool call if needed
                    if len(tool_calls) <= index:
                        tool_calls.append({
                            'id': '',
                            'type': 'function',
                            'function': {
                                'name': '',
                                'arguments': ''
                            }
                        })

                    # Update tool call
                    if tool_call_delta.id:
                        tool_calls[index]['id'] = tool_call_delta.id

                    if tool_call_delta.function:
                        if tool_call_delta.function.name:
                            tool_calls[index]['function']['name'] = tool_call_delta.function.name

                        if tool_call_delta.function.arguments:
                            tool_calls[index]['function']['arguments'] += tool_call_delta.function.arguments

                    # Yield tool call update
                    yield {
                        'type': 'tool_call',
                        'tool_call': tool_calls[index]
                    }

            # Handle content
            if delta.content:
                has_content = True
                yield {
                    'type': 'content',
                    'content': delta.content
                }

            # Handle finish
            if chunk.choices[0].finish_reason == 'tool_calls':
                # Execute tool calls
                for tool_call in tool_calls:
                    function_name = tool_call['function']['name']
                    function_args = json.loads(tool_call['function']['arguments'])

                    # Execute the function
                    if function_name in TOOL_FUNCTIONS:
                        result = TOOL_FUNCTIONS[function_name](**function_args)

                        # Yield tool result
                        yield {
                            'type': 'tool_result',
                            'tool_call_id': tool_call['id'],
                            'function_name': function_name,
                            'result': result
                        }

                        # Add tool response to messages
                        messages.append({
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [tool_call]
                        })
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call['id'],
                            "content": json.dumps(result)
                        })

                # Continue to next iteration to get the response
                break

            elif chunk.choices[0].finish_reason == 'stop':
                # Final response received
                yield {
                    'type': 'done'
                }
                return  # Exit the function completely

        # If we executed tools, continue the loop to get the next response
        if tool_calls and not has_content:
            continue
        else:
            # We got a response without tool calls, we're done
            yield {
                'type': 'done'
            }
            return

    # If we hit max iterations, send error
    yield {
        'type': 'error',
        'error': 'Maximum tool call iterations reached'
    }
    yield {
        'type': 'done'
    }
