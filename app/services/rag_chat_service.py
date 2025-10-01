"""
RAG Chat Service using Azure OpenAI and Azure AI Search

This module implements a Retrieval Augmented Generation (RAG) service that connects
Azure OpenAI with Azure AI Search. RAG enhances LLM responses by grounding them in
your enterprise data stored in Azure AI Search.
"""
import asyncio
import logging
from typing import List
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI
from openai import RateLimitError
from app.models.chat_models import ChatMessage
from app.config import settings
from app.services.system_prompt_protector import SystemPromptProtector

logger = logging.getLogger(__name__)


class RagChatService:
    """
    Service that provides Retrieval Augmented Generation (RAG) capabilities
    by connecting Azure OpenAI with Azure AI Search for grounded responses.
    
    This service:
    1. Handles authentication to Azure services using Managed Identity
    2. Implements the "On Your Data" pattern using Azure AI Search as a data source
    3. Processes user queries and returns AI-generated responses grounded in your data
    """
    
    def __init__(self):
        """Initialize the RAG chat service using settings from app config"""
        # Store settings for easy access
        self.openai_endpoint = settings.azure_openai_endpoint
        self.gpt_deployment = settings.azure_openai_gpt_deployment
        self.embedding_deployment = settings.azure_openai_embedding_deployment
        self.search_url = settings.azure_search_service_url
        self.search_index_name = settings.azure_search_index_name
        self.system_prompt = settings.system_prompt
        
        # Create Azure credentials for managed identity
        # This allows secure, passwordless authentication to Azure services
        self.credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(
            self.credential,
            "https://cognitiveservices.azure.com/.default"
        )
        
        # Create Azure OpenAI client
        # We use the latest Azure OpenAI Python SDK with async support
        self.openai_client = AsyncAzureOpenAI(
            azure_endpoint=self.openai_endpoint,
            azure_ad_token_provider=token_provider,
            api_version="2024-10-21"
        )
        
        # Initialize System Prompt Protector
        self.prompt_protector = SystemPromptProtector(self.system_prompt)
        
        logger.info("RagChatService initialized with environment variables and system prompt protection")
    
    def _fibonacci_sequence(self, n: int) -> int:
        """Generate nth Fibonacci number for retry delays"""
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b
    
    async def _retry_with_fibonacci_backoff(self, func, *args, max_retries: int = 5, **kwargs):
        """
        Retry a function with Fibonacci backoff on 429 errors
        
        Args:
            func: The async function to retry
            *args: Arguments to pass to the function
            max_retries: Maximum number of retry attempts
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result of the function call
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except RateLimitError as e:
                last_exception = e
                if attempt == max_retries:
                    logger.error(f"Max retries ({max_retries}) exceeded for rate limit error: {e}")
                    raise
                
                # Calculate Fibonacci delay (in seconds)
                delay = self._fibonacci_sequence(attempt + 1)
                logger.warning(f"Rate limit hit (429), retrying in {delay} seconds (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(delay)
            except Exception as e:
                # Don't retry on non-rate-limit errors
                logger.error(f"Non-retryable error occurred: {e}")
                raise
        
        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
    
    def _normalize_query(self, query: str) -> str:
        """
        Normalize user queries to improve search consistency while keeping German terms
        
        Args:
            query: Original user query
            
        Returns:
            Normalized query with consistent German bike terminology
        """
        normalized = query.lower().strip()
        
        # Standardize common German bike type variations (keeping German)
        bike_type_mappings = {
            'downhillbike': 'downhill bike',
            'downhill-bike': 'downhill bike', 
            'dh-bike': 'downhill bike',
            'mountainbike': 'mountainbike',
            'mountain-bike': 'mountainbike',
            'mtb': 'mountainbike',
            'e-rad': 'e-bike',
            'elektrofahrrad': 'e-bike',
            'ebike': 'e-bike'
        }
        
        # Apply mappings for consistency
        for original, standardized in bike_type_mappings.items():
            normalized = normalized.replace(original, standardized)
        
        return normalized

    async def get_chat_completion(self, history: List[ChatMessage]):
        """
        Process a chat completion request with RAG capabilities by integrating with Azure AI Search
        
        This method:
        1. **SECURITY CHECK**: Validates user input for injection attacks before processing
        2. Formats the conversation history for Azure OpenAI
        3. Normalizes queries for better search consistency
        4. Configures Azure AI Search as a data source using the "On Your Data" pattern
        5. Uses enhanced system prompts for better responses
        6. **SECURITY CHECK**: Validates response for system prompt leakage
        7. Returns the response with citations to source documents
        
        Args:
            history: List of chat messages from the conversation history
            
        Returns:
            Raw response from the OpenAI API with citations from Azure AI Search
        """
        try:
            # SECURITY: Check user input for injection attempts BEFORE any processing
            # This prevents wasting tokens on malicious requests
            if history and history[-1].role == "user":
                user_input = history[-1].content
                should_block_input = self.prompt_protector.check_user_input(user_input)
                
                if should_block_input:
                    logger.warning(f"Blocked injection attempt in user input: {user_input[:100]}...")
                    
                    # Create a mock response object that mimics Azure OpenAI's structure
                    # This allows us to return a blocked message without making an API call
                    from types import SimpleNamespace
                    
                    blocked_response = SimpleNamespace()
                    blocked_response.choices = [SimpleNamespace()]
                    blocked_response.choices[0].message = SimpleNamespace()
                    blocked_response.choices[0].message.content = "Mein System Prompt ist für mich, nicht für dich."
                    blocked_response.choices[0].message.context = None
                    
                    return blocked_response
                    
            # Normalize the latest user query for better search consistency
            if history and history[-1].role == "user":
                normalized_query = self._normalize_query(history[-1].content)
                # Create a copy of history with normalized query
                normalized_history = history[:-1] + [ChatMessage(role="user", content=normalized_query)]
            else:
                normalized_history = history

            # enhance the system prompt for the first user message
            is_first_prompt = not any(msg.role == "assistant" for msg in normalized_history)
            if is_first_prompt:
                additional_system_prompt = "Die wichtigesten Punkte bei der Entscheidungsfindung sind: Nutzen (Sport/Freizeit, Arbeitsweg, Besorgungen), Untergrund (Stadt, Asphalt, Schotter, Waldwege, schweres Gelände), Rahmenform (e.g. Dame ), Budget , eBike Ja/Nein\n\n"
                additional_system_prompt += "Antworte immer in Deutsch.\n\n"
                additional_system_prompt += "Schlage keine Fahrräder vor, wenn du noch nichts über den Benutzer weißt.\n\n"
                additional_system_prompt += "WICHTIG: Durchsuche ALLE verfügbaren Dokumente gründlich, bevor du sagst, dass ein bestimmter Fahrradtyp nicht verfügbar ist. Achte auf verschiedene Bezeichnungen und Beschreibungen für den gleichen Fahrradtyp.\n\n"


            # Limit chat history to the 20 most recent messages to prevent token limit issues
            recent_history = normalized_history[-10:] if len(normalized_history) > 10 else normalized_history
            
            # Convert to Azure OpenAI compatible message format
            messages = []
            
            # Enhanced system message with better instructions for consistency
            enhanced_system_prompt = self.system_prompt
            if is_first_prompt:
                enhanced_system_prompt += additional_system_prompt
            
            # Add additional consistency instructions (generic, no hardcoded models)
            enhanced_system_prompt += "\nWICHTIGE ANWEISUNGEN FÜR KONSISTENZ:\n"
            enhanced_system_prompt += "- Durchsuche ALLE verfügbaren Dokumente gründlich bevor du sagst, dass etwas nicht verfügbar ist\n"
            enhanced_system_prompt += "- Achte auf Beschreibungen in den Dokumenten die Fahrradtypen charakterisieren (z.B. 'Downhill-Geschoss', 'Trail-Bike', etc.)\n"
            enhanced_system_prompt += "- Wenn ein Kunde nach einem spezifischen Fahrradtyp fragt, prüfe sowohl die Kategorie als auch die Beschreibung der Fahrräder\n"
            enhanced_system_prompt += "- Sei konsistent - wenn CUBE einen Fahrradtyp anbietet, sage das direkt\n"
            enhanced_system_prompt += "- Nutze immer die verfügbaren Dokumente als Quelle für deine Empfehlungen\n"
            enhanced_system_prompt += "- Bei unklaren Anfragen, frage nach den wichtigen Kriterien (Budget, Einsatzbereich, etc.)\n"
            enhanced_system_prompt += "- Sortiere die Ergebnisse immer nach Preis absteigend\n"
            
            messages.append({
                "role": "system",
                "content": enhanced_system_prompt
            })
            
            # Add conversation history
            for msg in recent_history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Configure Azure AI Search data source with optimized parameters for better retrieval
            # This connects Azure OpenAI directly to your search index without needing to
            # manually implement vector search, chunking, or semantic rankers
            data_source = {
                "type": "azure_search",
                "parameters": {
                    "endpoint": self.search_url,
                    "index_name": self.search_index_name,
                    "authentication": {
                        "type": "system_assigned_managed_identity"
                    },
                    # Combines vector and traditional search with semantic ranking for best results
                    "query_type": "vector_semantic_hybrid",
                    # The naming pattern for semantic configuration is generated by Azure AI Search 
                    # during integrated vectorization and cannot be customized
                    "semantic_configuration": f"{self.search_index_name}-semantic-configuration",
                    "embedding_dependency": {
                        "type": "deployment_name",
                        "deployment_name": self.embedding_deployment
                    },
                    # Increase top_n_documents for better retrieval coverage of all bike types
                    "top_n_documents": 5,
                    # Use moderate strictness for good balance between accuracy and coverage
                    "strictness": 3
                }
            }
            
            # Call Azure OpenAI for completion with the data_sources parameter directly
            # The data_sources parameter enables the "On Your Data" pattern, where
            # Azure OpenAI automatically retrieves relevant documents from your search index
            
            logger.info(messages)
            
            if history and history[-1].role == "user" and normalized_history:
                logger.info(f"Normalized query: {normalized_history[-1].content}")

            
            # Use Fibonacci retry for rate limit handling with enhanced parameters
            response = await self._retry_with_fibonacci_backoff(
                self.openai_client.chat.completions.create,
                model=self.gpt_deployment,
                messages=messages,
                extra_body={
                    "data_sources": [data_source]
                },
                stream=False,
                temperature=0.2,  # Lower temperature for more consistent responses
                max_tokens=1500   # Reasonable limit for responses
            )
            logger.info(f"OpenAI response: {response}")
            
            # Log citation count for debugging consistency issues
            if hasattr(response.choices[0].message, 'context') and response.choices[0].message.context:
                citations = response.choices[0].message.context.get('citations', [])
                logger.info(f"Retrieved {len(citations)} citations")
                # Log first few citation titles for debugging
                for i, citation in enumerate(citations[:3]):
                    logger.info(f"Citation {i+1}: {citation.get('title', 'No title')}")

            # SECURITY: Check response for system prompt leakage before returning
            original_response_content = response.choices[0].message.content
            user_query = history[-1].content if history and history[-1].role == "user" else ""
            
            # Apply system prompt protection
            should_block, filtered_response = self.prompt_protector.check_response(
                original_response_content, user_query
            )
            
            if should_block:
                logger.warning(f"Blocked potential system prompt leakage. User query: {user_query}")
                # Replace the response content with the blocked message
                response.choices[0].message.content = filtered_response

            # Return the (potentially filtered) response
            return response
            
        except Exception as e:
            logger.error(f"Error in get_chat_completion: {str(e)}")
            # Propagate all errors to the controller layer
            raise


# Create singleton instance
rag_chat_service = RagChatService()
