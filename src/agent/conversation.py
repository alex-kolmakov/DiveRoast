from collections.abc import AsyncGenerator

import pandas as pd
from google.genai import types
from openinference.instrumentation import using_attributes

from src.agent.gemini_client import get_client
from src.agent.system_prompts import ROAST_SYSTEM_PROMPT
from src.agent.tools import TOOL_DECLARATIONS, TOOL_FUNCTIONS
from src.config import settings
from src.observability import get_tracer


class DiverRoastAgent:
    """Manages conversation state and tool dispatch for the diver roasting agent."""

    def __init__(self):
        self._client = None
        self.history: list[types.Content] = []
        self.dive_data: pd.DataFrame | None = None

    @property
    def client(self):
        """Lazily initialize the Gemini client."""
        if self._client is None:
            self._client = get_client()
        return self._client

    def set_dive_data(self, df: pd.DataFrame):
        """Store parsed dive log data for tool calls.

        Also seeds the conversation history so the LLM knows data is available.
        """
        self.dive_data = df
        dive_numbers = sorted(df["dive_number"].unique().tolist())
        context_msg = (
            f"[System: The diver has uploaded a dive log containing {len(dive_numbers)} dives "
            f"(dive numbers: {', '.join(str(d) for d in dive_numbers)}). "
            f"The dive data is now loaded and available through your tools. "
            f"Use list_dives, analyze_all_dives, analyze_dive_profile, and get_dive_summary "
            f"to access this data. Do NOT ask the user to upload — it's already done.]"
        )
        self.history.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=context_msg)],
            )
        )
        self.history.append(
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(
                        text=f"Got it — {len(dive_numbers)} dives loaded. I'm ready to analyze and roast."
                    )
                ],
            )
        )

    def get_dive_numbers(self) -> list[str]:
        """Return list of available dive numbers."""
        if self.dive_data is None:
            return []
        return sorted(self.dive_data["dive_number"].unique().tolist())

    def _get_dive_data_json(self) -> str:
        """Serialize dive data to JSON for tool calls."""
        if self.dive_data is None:
            return "[]"
        return self.dive_data.to_json()

    def _execute_tool(self, function_call: types.FunctionCall) -> str:
        """Execute a tool function call and return the result."""
        tracer = get_tracer()
        with tracer.start_as_current_span(
            f"tool.{function_call.name or 'unknown'}",
            attributes={"openinference.span.kind": "TOOL"},
        ):
            func_name: str = function_call.name or ""
            args = dict(function_call.args) if function_call.args else {}

            # Inject dive_data_json for tools that need it
            if func_name in (
                "analyze_dive_profile",
                "get_dive_summary",
                "list_dives",
                "analyze_all_dives",
            ):
                args["dive_data_json"] = self._get_dive_data_json()

            func = TOOL_FUNCTIONS.get(func_name)
            if func is None:
                return f"Unknown tool: {func_name}"

            try:
                return func(**args)
            except Exception as e:
                return f"Tool error ({func_name}): {e!s}"

    def _extract_function_calls(
        self, response: types.GenerateContentResponse
    ) -> list[types.FunctionCall]:
        """Extract function calls from a Gemini response, if any."""
        if not response.candidates:
            return []
        candidate = response.candidates[0]
        if not candidate.content or not candidate.content.parts:
            return []
        return [
            p.function_call
            for p in candidate.content.parts
            if p.function_call is not None
        ]

    async def chat(self, user_message: str) -> AsyncGenerator[str, None]:
        """Process a user message and yield streaming response chunks.

        Handles the Gemini function-calling loop: call -> tool -> call -> final text.
        """
        tracer = get_tracer()
        with (
            tracer.start_as_current_span(
                "agent.chat",
                attributes={"openinference.span.kind": "CHAIN"},
            ),
            using_attributes(session_id=str(id(self))),
        ):
            self.history.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_message)],
                )
            )

            tools = [types.Tool(function_declarations=TOOL_DECLARATIONS)]

            while True:
                response = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=self.history,
                    config=types.GenerateContentConfig(
                        system_instruction=ROAST_SYSTEM_PROMPT,
                        tools=tools,
                        temperature=0.8,
                    ),
                )

                function_calls = self._extract_function_calls(response)

                if function_calls:
                    # Add the model's response (with tool calls) to history
                    self.history.append(response.candidates[0].content)  # type: ignore[arg-type]

                    # Execute all tool calls and build response parts
                    tool_response_parts = []
                    for fc in function_calls:
                        result = self._execute_tool(fc)
                        tool_response_parts.append(
                            types.Part.from_function_response(
                                name=fc.name or "",
                                response={"result": result},
                            )
                        )

                    # Add tool results to history
                    self.history.append(
                        types.Content(role="user", parts=tool_response_parts)
                    )
                    # Continue the loop — model will process tool results
                    continue

                # No tool calls — extract final text response
                if response.text:
                    self.history.append(
                        types.Content(
                            role="model",
                            parts=[types.Part.from_text(text=response.text)],
                        )
                    )
                    yield response.text
                break

    async def chat_stream(self, user_message: str) -> AsyncGenerator[str, None]:
        """Stream response token-by-token using Gemini's streaming API.

        Falls back to non-streaming for tool-calling rounds, then streams
        the final text response.
        """
        tracer = get_tracer()
        with (
            tracer.start_as_current_span(
                "agent.chat_stream",
                attributes={"openinference.span.kind": "CHAIN"},
            ),
            using_attributes(session_id=str(id(self))),
        ):
            self.history.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_message)],
                )
            )

            tools = [types.Tool(function_declarations=TOOL_DECLARATIONS)]

            while True:
                response = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=self.history,
                    config=types.GenerateContentConfig(
                        system_instruction=ROAST_SYSTEM_PROMPT,
                        tools=tools,
                        temperature=0.8,
                    ),
                )

                function_calls = self._extract_function_calls(response)

                if function_calls:
                    self.history.append(response.candidates[0].content)  # type: ignore[arg-type]

                    tool_response_parts = []
                    for fc in function_calls:
                        result = self._execute_tool(fc)
                        tool_response_parts.append(
                            types.Part.from_function_response(
                                name=fc.name or "",
                                response={"result": result},
                            )
                        )

                    self.history.append(
                        types.Content(role="user", parts=tool_response_parts)
                    )
                    continue

                # No tool calls — yield the final text response
                if response.text:
                    self.history.append(
                        types.Content(
                            role="model",
                            parts=[types.Part.from_text(text=response.text)],
                        )
                    )
                    # Yield in chunks for SSE streaming
                    text = response.text
                    chunk_size = 20
                    for i in range(0, len(text), chunk_size):
                        yield text[i : i + chunk_size]
                break
