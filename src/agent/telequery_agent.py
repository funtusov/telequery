from typing import List
from pydantic import BaseModel, Field
import logfire

from ..models.agent import AgentContext, SearchToolInput, LLMPrompt
from ..models.api import QueryResponse, SourceMessage
from ..models.database import TelegramMessage
from ..tools.search import get_search_tool
from ..llm.factory import LLMFactory
from ..observability.logfire_config import log_agent_operation


class TelequeryAgent(BaseModel):
    """Pydantic-based agent for processing Telegram message queries."""
    
    llm_provider_name: str = "openai"
    max_context_messages: int = 100
    database_url: str = "sqlite:///./telegram_messages.db"
    chroma_path: str = "./chroma_db"
    expansion_db_path: str = "./data/telequery_expansions.db"
    
    # Private fields excluded from Pydantic model
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, **data):
        super().__init__(**data)
        # Store LLM provider as private attribute
        object.__setattr__(self, '_llm_provider', None)
    
    def _get_llm_provider(self):
        """Lazy initialization of LLM provider."""
        if not hasattr(self, '_llm_provider') or self._llm_provider is None:
            object.__setattr__(self, '_llm_provider', LLMFactory.create_provider(self.llm_provider_name))
        return self._llm_provider
    
    @log_agent_operation("process_query")
    async def process_query(self, context: AgentContext) -> QueryResponse:
        """Process a user query and return a response."""
        try:
            # Step 1: Search for relevant messages
            with logfire.span("agent.search_phase") as search_span:
                search_input = SearchToolInput(
                    query_text=context.user_question,
                    chat_id=context.telegram_chat_id,
                    user_id=None,  # Search across all users in the chat
                    debug=context.debug
                )
                search_span.set_attribute("search_input", search_input.model_dump())
                
                search_result = await get_search_tool(
                    database_url=self.database_url,
                    chroma_path=self.chroma_path,
                    expansion_db_url=f"sqlite:///{self.expansion_db_path}"
                ).search_relevant_messages(search_input)
                
                search_span.set_attribute("messages_found", len(search_result.messages))
            
            if not search_result.messages:
                return QueryResponse(
                    answer_text="I couldn't find any relevant messages to answer your question.",
                    source_messages=[],
                    status="no_results"
                )
            
            # Step 2: Prepare context for LLM
            with logfire.span("agent.prepare_context") as context_span:
                context_messages = search_result.messages[:self.max_context_messages]
                context_span.set_attribute("context_message_count", len(context_messages))
                
                llm_prompt = self._create_llm_prompt(
                    context.user_question,
                    context_messages
                )
            
            # Step 3: Generate response using LLM
            with logfire.span("agent.llm_generation") as llm_span:
                llm_span.set_attribute("llm_provider", self.llm_provider_name)
                llm_span.set_attribute("temperature", 0.3)
                
                llm_response = await self._get_llm_provider().generate_response(
                    system_prompt=llm_prompt.system_prompt,
                    user_prompt=llm_prompt.user_prompt,
                    temperature=0.3  # Lower temperature for more factual responses
                )
            
            # Step 4: Convert messages to API format
            if context.debug and search_result.messages_with_scores:
                # In debug mode, include expanded text and scores
                source_messages = [
                    SourceMessage(
                        message_id=msg_with_score.message.message_id,
                        sender=msg_with_score.message.sender_name,
                        timestamp=msg_with_score.message.timestamp,
                        text=msg_with_score.message.text,
                        expanded_text=msg_with_score.expanded_text,
                        relevance_score=msg_with_score.relevance_score
                    )
                    for msg_with_score in search_result.messages_with_scores[:self.max_context_messages]
                ]
            else:
                # Normal mode
                source_messages = [
                    SourceMessage(
                        message_id=msg.message_id,
                        sender=msg.sender_name,
                        timestamp=msg.timestamp,
                        text=msg.text
                    )
                    for msg in context_messages
                ]
            
            return QueryResponse(
                answer_text=llm_response.content,
                source_messages=source_messages,
                status="success",
                rewritten_query=search_result.rewritten_query if context.debug else None
            )
            
        except Exception as e:
            return QueryResponse(
                answer_text=f"An error occurred while processing your query: {str(e)}",
                source_messages=[],
                status="error"
            )
    
    def _create_llm_prompt(
        self,
        user_question: str,
        context_messages: List[TelegramMessage]
    ) -> LLMPrompt:
        """Create a structured prompt for the LLM."""
        
        system_prompt = """You are an AI assistant that helps users find information from their Telegram message history. 

Your task is to:
1. Analyze the provided message context carefully
2. Answer the user's question based ONLY on the information in the messages
3. Cite specific messages when possible by mentioning the sender and approximate time
4. If you cannot find a clear answer in the messages, say so clearly
5. Do not make up information or hallucinate responses

Be concise but informative in your responses."""
        
        # Format context messages
        context_text = "\n\n".join([
            f"Message from {msg.sender_name} at {msg.timestamp.strftime('%Y-%m-%d %H:%M')}:\n{msg.text or ''}"
            for msg in context_messages
        ])
        
        user_prompt = f"""Based on the following Telegram messages, please answer this question: "{user_question}"

Message Context:
{context_text}

Please provide a clear, accurate answer based only on the information in these messages."""
        
        return LLMPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            context_messages=context_messages
        )