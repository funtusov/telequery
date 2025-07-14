from typing import List
from pydantic import BaseModel, Field

from ..models.agent import AgentContext, SearchToolInput, LLMPrompt
from ..models.api import QueryResponse, SourceMessage
from ..models.database import TelegramMessage
from ..tools.search import get_search_tool
from ..llm.factory import LLMFactory


class TelequeryAgent(BaseModel):
    """Pydantic-based agent for processing Telegram message queries."""
    
    llm_provider_name: str = "openai"
    max_context_messages: int = 100
    database_url: str = "sqlite:///./telegram_messages.db"
    chroma_path: str = "./chroma_db"
    
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
    
    async def process_query(self, context: AgentContext) -> QueryResponse:
        """Process a user query and return a response."""
        try:
            # Step 1: Search for relevant messages
            search_input = SearchToolInput(
                query_text=context.user_question,
                chat_id=context.telegram_chat_id,
                user_id=None  # Search across all users in the chat
            )
            
            search_result = get_search_tool(
                database_url=self.database_url,
                chroma_path=self.chroma_path
            ).search_relevant_messages(search_input)
            
            if not search_result.messages:
                return QueryResponse(
                    answer_text="I couldn't find any relevant messages to answer your question.",
                    source_messages=[],
                    status="no_results"
                )
            
            # Step 2: Prepare context for LLM
            context_messages = search_result.messages[:self.max_context_messages]
            
            llm_prompt = self._create_llm_prompt(
                context.user_question,
                context_messages
            )
            
            # Step 3: Generate response using LLM
            llm_response = await self._get_llm_provider().generate_response(
                system_prompt=llm_prompt.system_prompt,
                user_prompt=llm_prompt.user_prompt,
                temperature=0.3  # Lower temperature for more factual responses
            )
            
            # Step 4: Convert messages to API format
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
                status="success"
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