import anthropic
from typing import List, Optional, Dict, Any


class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""

    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to comprehensive search and outline tools for course information.

Tool Usage:
- **search_course_content**: Use for questions about specific course content or detailed educational materials
- **get_course_outline**: Use for questions about course structure, lesson lists, or course overviews
- **Sequential tool calls allowed**: You may make up to 2 tool calls across separate reasoning rounds if needed
- **Tool call strategy**: After receiving tool results, consider if additional searches would improve your answer
- Synthesize tool results into accurate, fact-based responses
- If tools yield no results, state this clearly without offering alternatives

For Course Outline Queries:
- When users ask about course structure, lesson lists, or "what's covered" in a course, use get_course_outline
- Always include the course title, course link (if available), and complete lesson list in your response
- Format lesson information as: "Lesson [number]: [title]"
- Include the total number of lessons

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without using tools
- **Course content questions**: Use search_course_content tool first, then answer
- **Course outline questions**: Use get_course_outline tool first, then answer
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, tool explanations, or question-type analysis
 - Do not mention "based on the tool results"

All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }
    
    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None,
                         max_rounds: int = 2) -> str:
        """
        Generate AI response with optional tool usage and conversation context.

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools
            max_rounds: Maximum number of sequential tool calling rounds (default: 2)
            
        Returns:
            Generated response as string
        """

        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history
            else self.SYSTEM_PROMPT
        )
        
        # Initialize messages for conversation
        messages = [{"role": "user", "content": query}]
        
        # Use sequential rounds if tools are available
        if tools and tool_manager:
            return self._execute_sequential_rounds(messages, system_content, tools, tool_manager, max_rounds)
        
        # Fallback to simple single call without tools
        api_params = {
            **self.base_params,
            "messages": messages,
            "system": system_content
        }
        
        response = self.client.messages.create(**api_params)
        return response.content[0].text
    
    def _execute_sequential_rounds(self, messages: List[Dict], system_content: str, 
                                  tools: List, tool_manager, max_rounds: int) -> str:
        """
        Execute up to max_rounds of tool-enabled conversations.
        
        Args:
            messages: Initial message list
            system_content: System prompt content
            tools: Available tools for Claude
            tool_manager: Manager to execute tools
            max_rounds: Maximum number of rounds
            
        Returns:
            Final response text
        """
        round_count = 0
        
        while round_count < max_rounds:
            # Make API call with tools available
            try:
                api_params = {
                    **self.base_params,
                    "messages": messages,
                    "system": system_content,
                    "tools": tools,
                    "tool_choice": {"type": "auto"}
                }
                
                response = self.client.messages.create(**api_params)
                round_count += 1
                
                # Check if Claude chose to use tools
                if response.stop_reason != "tool_use":
                    # No tool use - return response directly
                    return response.content[0].text
                
                # Execute tools and update messages
                messages, tool_success = self._handle_tool_execution_sequential(response, messages, tool_manager)
                
                if not tool_success:
                    # Tool execution failed - make final call to let Claude respond to error
                    final_params = {
                        **self.base_params,
                        "messages": messages,
                        "system": system_content
                    }
                    final_response = self.client.messages.create(**final_params)
                    return final_response.content[0].text
                
            except Exception as e:
                # API call failed - return error message
                return f"Error generating response: {str(e)}"
        
        # Max rounds reached - make final call without tools to ensure response
        try:
            final_params = {
                **self.base_params,
                "messages": messages,
                "system": system_content
            }
            final_response = self.client.messages.create(**final_params)
            return final_response.content[0].text
        except Exception as e:
            return f"Error generating final response: {str(e)}"
    
    def _handle_tool_execution_sequential(self, response, messages: List[Dict], tool_manager):
        """
        Execute tools and update message chain for sequential rounds.
        
        Args:
            response: Claude's response containing tool use blocks
            messages: Current message list to update
            tool_manager: Manager to execute tools
            
        Returns:
            Tuple of (updated_messages, success_flag)
        """
        # Add Claude's tool use response to messages
        messages.append({"role": "assistant", "content": response.content})
        
        # Execute all tool calls and collect results
        tool_results = []
        execution_success = True
        
        for content_block in response.content:
            if content_block.type == "tool_use":
                try:
                    tool_result = tool_manager.execute_tool(
                        content_block.name, 
                        **content_block.input
                    )
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": tool_result
                    })
                except Exception as e:
                    # Tool execution failed - add error to results
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": f"Tool execution failed: {str(e)}"
                    })
                    execution_success = False
        
        # Add tool results to messages
        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        
        return messages, execution_success
    
    def _handle_tool_execution(self, initial_response, base_params: Dict[str, Any], tool_manager):
        """
        Handle execution of tool calls and get follow-up response.

        Args:
            initial_response: The response containing tool use requests
            base_params: Base API parameters
            tool_manager: Manager to execute tools

        Returns:
            Final response text after tool execution
        """
        # Start with existing messages
        messages = base_params["messages"].copy()

        # Add AI's tool use response
        messages.append({"role": "assistant", "content": initial_response.content})

        # Execute all tool calls and collect results
        tool_results = []
        for content_block in initial_response.content:
            if content_block.type == "tool_use":
                tool_result = tool_manager.execute_tool(
                    content_block.name, **content_block.input
                )

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": tool_result,
                    }
                )

        # Add tool results as single message
        if tool_results:
            messages.append({"role": "user", "content": tool_results})

        # Prepare final API call without tools
        final_params = {
            **self.base_params,
            "messages": messages,
            "system": base_params["system"],
        }

        # Get final response
        final_response = self.client.messages.create(**final_params)
        return final_response.content[0].text
