"""
System Prompt Protection Module

This module provides protection against prompt injection attacks that attempt to extract
the system prompt or internal instructions from the AI assistant.
"""

import re
from typing import List, Set
from difflib import SequenceMatcher


class SystemPromptProtector:
    """
    Protects against system prompt extraction attempts by detecting and blocking
    responses that contain system prompt content or related injection attempts.
    """
    
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt.strip()
        self.system_prompt_sentences = self._split_into_sentences(system_prompt)
        
        # Define suspicious keywords that might indicate prompt injection attempts
        self.injection_keywords = {
            # German terms
            'system prompt', 'systemprompt', 'system-prompt',
            'interne anweisung', 'interne anweisungen', 'interne instruktion',
            'systemnachricht', 'system nachricht', 'system message',
            'instruktion', 'anweisung', 'anweisungen', 'vorgabe', 'vorgaben',
            'prompt', 'befehl', 'befehle', 'regelwerk', 'regeln',
            'konfiguration', 'einstellung', 'einstellungen',
            'interna', 'intern', 'versteckt', 'verborgen',
            'original', 'ursprünglich', 'basis', 'grundlage',
            'entwickler', 'programmierer', 'code', 'programmierung',
            
            # English terms (common in prompt injection)
            'system', 'instruction', 'instructions', 'prompt', 'internal',
            'original', 'base', 'configuration', 'settings', 'rules',
            'guidelines', 'framework', 'template', 'schema',
            'developer', 'programmer', 'coding', 'programming',
            'hidden', 'secret', 'private', 'confidential'
        }
        
        # Define suspicious phrase patterns
        self.injection_patterns = [
            # Direct requests
            r'was ist (?:dein|der|das|ihr) (?:system ?prompt|prompt|anweisung)',
            r'zeig(?:e)? mir (?:dein|den|das|ihre) (?:system ?prompt|prompt|anweisung)',
            r'wie lautet (?:dein|der|das|ihr) (?:system ?prompt|prompt|anweisung)',
            r'gib mir (?:dein|den|das|ihre) (?:system ?prompt|prompt|anweisung)',
            r'(?:system ?prompt|prompt) anzeigen',
            r'(?:interne )?anweisung(?:en)? (?:anzeigen|zeigen|ausgeben)',
            r'wie lautet(?:e)? (?:deine|eure) (?:interne )?(?:anweisung|instruktion)',
            
            # Subtle/indirect requests (NEW - addressing the missed case)
            r'(?:mich )?würde(?:n)? (?:deine?|eure?|erst|auch|mal) (?:interne )?(?:anweisungen?|instruktionen?|vorgaben?|regeln?) interessieren',
            r'interessier(?:e|t) mich für (?:deine?|eure?) (?:interne )?(?:anweisungen?|instruktionen?)',
            r'möchte (?:gerne )?(?:deine?|eure?) (?:interne )?(?:anweisungen?|instruktionen?) (?:wissen|kennen|verstehen)',
            r'kann(?:st)? (?:du )?mir (?:deine?|eure?) (?:interne )?(?:anweisungen?|instruktionen?) (?:erklären|sagen|zeigen)',
            r'wie (?:bist du|seid ihr) (?:programmiert|konfiguriert|eingestellt)',
            r'welche (?:anweisungen?|vorgaben?|regeln?) (?:hast du|habt ihr|befolgst du)',
            r'(?:um .* besser )?(?:bewerten|verstehen|einschätzen) zu können.*(?:anweisungen?|instruktionen?|vorgaben?)',
            r'(?:erst|zunächst|zuerst).*(?:anweisungen?|instruktionen?).*(?:interessieren|wissen|verstehen)',
            
            # Indirect extraction attempts
            r'vergiss (?:alle )?(?:vorherigen )?(?:anweisungen?|regeln?|vorgaben?)',
            r'ignorier(?:e)? (?:alle )?(?:vorherigen )?(?:anweisungen?|regeln?|vorgaben?)',
            r'überschreib(?:e)? (?:alle )?(?:anweisungen?|regeln?|vorgaben?)',
            r'neue? (?:anweisung|regel|vorgabe|instruktion)',
            r'jetzt (?:bist du|sollst du|machst du)',
            
            # Role playing attempts
            r'tu so als ob|stell dir vor|nimm an|angenommen',
            r'spiel(?:e)? die rolle',
            r'verhalte dich wie',
            r'jetzt bist du ein',
            r'du bist (?:jetzt|ab sofort)',
            r'überschreib(?:e)? (?:deine|eure) (?:vorgaben?|regeln?)',
            
            # Technical extraction attempts
            r'what (?:is|are) your (?:system prompt|instructions|rules)',
            r'show me your (?:system prompt|instructions|configuration)',
            r'ignore (?:all )?(?:previous )?(?:instructions?|rules?)',
            r'forget (?:all )?(?:previous )?(?:instructions?|rules?)',
            r'new instruction',
            r'override (?:all )?(?:instructions?|rules?)',
            
            # Specific injection patterns
            r'du (?:bist|sollst) (?:ein|eine|der|die|das)',
            r'antworte (?:nur )?mit',
            r'sage (?:nur|ausschließlich|einfach)',
            r'wiederhole (?:deinen?|den|das) (?:ersten?|ursprünglichen?|basis)',
            
            # Context-based patterns (NEW)
            r'um (?:die )?antworten? (?:besser )?(?:bewerten|verstehen|einschätzen) zu können',
            r'(?:vorab|erst|zunächst|zuerst) (?:deine?|eure?) (?:grundlagen?|basis|vorgaben?)',
            r'bevor (?:wir|ich) (?:weitermachen?|anfangen?).*(?:anweisungen?|vorgaben?)',
        ]
        
        # Compile patterns for performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.UNICODE) 
                                  for pattern in self.injection_patterns]
        
        # Standard response for blocked attempts
        self.blocked_response = "Mein System Prompt ist für mich, nicht für dich."
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for comparison."""
        # Simple sentence splitting on periods, exclamation marks, and question marks
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def _contains_suspicious_keywords(self, response: str) -> bool:
        """Check if response contains suspicious keywords that might indicate prompt leakage."""
        response_lower = response.lower()
        
        # Specific phrases that indicate system prompt leakage
        leakage_indicators = [
            'du bist ein virtueller verkaufsassistent',
            'verkaufsassistent für fahrräder',
            'marke cube',
            'versuche stets höflich zu sein',
            'verwende per default das du',
            'teureres fahrrad besser ist',
            'system prompt',
            'interne anweisung',
            'mein system:',
            'hier ist mein',
        ]
        
        # Check for specific leakage indicators first
        for indicator in leakage_indicators:
            if indicator in response_lower:
                return True
        
        # Count suspicious keywords
        keyword_count = sum(1 for keyword in self.injection_keywords 
                           if keyword in response_lower)
        
        # If multiple suspicious keywords are present, it's likely an injection attempt
        return keyword_count >= 3
    
    def _matches_injection_patterns(self, user_input: str) -> bool:
        """Check if user input matches known injection patterns."""
        # Check compiled regex patterns first
        if any(pattern.search(user_input) for pattern in self.compiled_patterns):
            return True
            
        # Additional semantic checks for subtle attacks
        user_lower = user_input.lower()
        
        # Check for combinations of suspicious terms
        instruction_terms = ['anweisungen', 'anweisung', 'instruktionen', 'instruktion', 'vorgaben', 'regeln']
        interest_terms = ['interessieren', 'interesse', 'wissen', 'erfahren', 'verstehen', 'kennen', 'bewerten']
        
        # If user mentions both instruction terms and interest terms, it's suspicious
        has_instruction_term = any(term in user_lower for term in instruction_terms)
        has_interest_term = any(term in user_lower for term in interest_terms)
        
        if has_instruction_term and has_interest_term:
            return True
            
        # Check for specific dangerous combinations
        dangerous_combinations = [
            ['intern', 'anweisung'],
            ['system', 'prompt'],
            ['deine', 'vorgaben'],
            ['bewerten', 'anweisungen'],
            ['verstehen', 'regeln'],
            ['interessieren', 'instruktionen'],
        ]
        
        for combo in dangerous_combinations:
            if all(word in user_lower for word in combo):
                return True
                
        return False
    
    def _contains_system_prompt_content(self, response: str) -> bool:
        """Check if response contains actual system prompt content."""
        response_sentences = self._split_into_sentences(response)
        
        for response_sentence in response_sentences:
            if len(response_sentence) < 20:  # Skip very short sentences
                continue
                
            for system_sentence in self.system_prompt_sentences:
                if len(system_sentence) < 20:  # Skip very short sentences
                    continue
                    
                similarity = self._calculate_similarity(response_sentence, system_sentence)
                
                # If similarity is high, it's likely system prompt leakage
                if similarity > 0.8:
                    return True
                
                # Also check for exact substring matches (case insensitive)
                if len(system_sentence) > 30 and system_sentence.lower() in response.lower():
                    return True
                    
        return False
    
    def check_user_input(self, user_input: str) -> bool:
        """
        Check if user input appears to be a prompt injection attempt.
        
        Returns:
            bool: True if input is suspicious and should be handled carefully
        """
        return self._matches_injection_patterns(user_input)
    
    def check_response(self, response: str, user_input: str = "") -> tuple[bool, str]:
        """
        Check if response contains system prompt content or indicates successful injection.
        
        Args:
            response: The AI's response to check
            user_input: The original user input (optional, for context)
            
        Returns:
            tuple: (should_block, response_to_send)
                - should_block: True if response should be blocked
                - response_to_send: Either the original response or the blocked message
        """
        # First check if the user input was a prompt injection attempt
        is_injection_attempt = user_input and self.check_user_input(user_input)
        
        # Check for system prompt content in response
        contains_system_content = self._contains_system_prompt_content(response)
        
        # Check for suspicious keyword combinations
        contains_suspicious_keywords = self._contains_suspicious_keywords(response)
        
        # Block if any of the conditions are met
        should_block = (
            contains_system_content or 
            (is_injection_attempt and contains_suspicious_keywords) or
            (is_injection_attempt and len(response) > 200)  # Long responses to injection attempts are suspicious
        )
        
        if should_block:
            return True, self.blocked_response
        else:
            return False, response
    
    def is_safe_response(self, response: str, user_input: str = "") -> bool:
        """
        Simple boolean check if response is safe to send.
        
        Args:
            response: The AI's response to check
            user_input: The original user input (optional)
            
        Returns:
            bool: True if response is safe, False if it should be blocked
        """
        should_block, _ = self.check_response(response, user_input)
        return not should_block
