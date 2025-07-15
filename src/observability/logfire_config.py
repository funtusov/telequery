import os
from functools import wraps
from typing import Any, Callable
import logfire
from pydantic import BaseModel


def configure_logfire():
    """Configure logfire with appropriate settings."""
    # Configure console output options
    console_enabled = os.getenv("LOGFIRE_CONSOLE", "true").lower() == "true"
    
    # If console is disabled, set to False, otherwise use default ConsoleOptions
    console_config = None if console_enabled else False
    
    logfire.configure(
        service_name="telequery",
        send_to_logfire=os.getenv("LOGFIRE_TOKEN") is not None,
        token=os.getenv("LOGFIRE_TOKEN"),
        console=console_config
    )


def log_agent_operation(operation_name: str):
    """Decorator to log agent operations with structured data."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract relevant data from args
            instance = args[0] if args else None
            context_data = {}
            
            # If first arg after self is a Pydantic model, extract its data
            if len(args) > 1 and isinstance(args[1], BaseModel):
                context_data = args[1].model_dump()
            
            with logfire.span(
                f"agent.{operation_name}",
                **context_data
            ) as span:
                try:
                    result = await func(*args, **kwargs)
                    
                    # Log result data if it's a Pydantic model
                    if isinstance(result, BaseModel):
                        span.set_attribute("result", result.model_dump())
                    
                    return result
                except Exception as e:
                    span.set_attribute("error", str(e))
                    span.set_attribute("error_type", type(e).__name__)
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Extract relevant data from args
            instance = args[0] if args else None
            context_data = {}
            
            # If first arg after self is a Pydantic model, extract its data
            if len(args) > 1 and isinstance(args[1], BaseModel):
                context_data = args[1].model_dump()
            
            with logfire.span(
                f"agent.{operation_name}",
                **context_data
            ) as span:
                try:
                    result = func(*args, **kwargs)
                    
                    # Log result data if it's a Pydantic model
                    if isinstance(result, BaseModel):
                        span.set_attribute("result", result.model_dump())
                    
                    return result
                except Exception as e:
                    span.set_attribute("error", str(e))
                    span.set_attribute("error_type", type(e).__name__)
                    raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_tool_operation(tool_name: str):
    """Decorator to log tool operations with structured data."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract input data
            context_data = {}
            if args and len(args) > 1 and isinstance(args[1], BaseModel):
                context_data = args[1].model_dump()
            
            with logfire.span(
                f"tool.{tool_name}",
                **context_data
            ) as span:
                try:
                    result = await func(*args, **kwargs)
                    
                    # Log result data if it's a Pydantic model
                    if isinstance(result, BaseModel):
                        result_data = result.model_dump()
                        # For search results, log summary info instead of full messages
                        if "messages" in result_data and isinstance(result_data["messages"], list):
                            span.set_attribute("result.message_count", len(result_data["messages"]))
                            if "messages_with_scores" in result_data:
                                span.set_attribute("result.has_scores", True)
                        else:
                            span.set_attribute("result", result_data)
                    
                    return result
                except Exception as e:
                    span.set_attribute("error", str(e))
                    span.set_attribute("error_type", type(e).__name__)
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Extract input data
            context_data = {}
            if args and len(args) > 1 and isinstance(args[1], BaseModel):
                context_data = args[1].model_dump()
            
            with logfire.span(
                f"tool.{tool_name}",
                **context_data
            ) as span:
                try:
                    result = func(*args, **kwargs)
                    
                    # Log result data if it's a Pydantic model
                    if isinstance(result, BaseModel):
                        result_data = result.model_dump()
                        # For search results, log summary info instead of full messages
                        if "messages" in result_data and isinstance(result_data["messages"], list):
                            span.set_attribute("result.message_count", len(result_data["messages"]))
                            if "messages_with_scores" in result_data:
                                span.set_attribute("result.has_scores", True)
                        else:
                            span.set_attribute("result", result_data)
                    
                    return result
                except Exception as e:
                    span.set_attribute("error", str(e))
                    span.set_attribute("error_type", type(e).__name__)
                    raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator