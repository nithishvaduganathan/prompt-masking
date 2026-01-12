"""
LLM Integration Module
Handles communication with Large Language Models (OpenAI or simulated)
"""

import os
from typing import Optional, Dict, Any
import random


class LLMClient:
    """
    Client for interacting with Large Language Models
    Supports OpenAI API or simulated responses for testing
    """
    
    def __init__(self, api_key: Optional[str] = None, use_simulation: bool = True):
        """
        Initialize LLM Client
        
        Args:
            api_key: OpenAI API key (optional if using simulation)
            use_simulation: If True, use simulated responses instead of real API
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.use_simulation = use_simulation
        
        if not use_simulation and self.api_key:
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI client: {e}")
                print("Falling back to simulation mode")
                self.use_simulation = True
        else:
            self.use_simulation = True
    
    def generate_response(self, prompt: str, max_tokens: int = 500) -> str:
        """
        Generate a response from the LLM
        
        Args:
            prompt: The input prompt (should be masked)
            max_tokens: Maximum tokens in response
            
        Returns:
            LLM response text
        """
        if self.use_simulation:
            return self._simulate_response(prompt)
        else:
            return self._call_openai_api(prompt, max_tokens)
    
    def _simulate_response(self, prompt: str) -> str:
        """
        Generate a simulated response for testing without API costs
        
        Args:
            prompt: Input prompt
            
        Returns:
            Simulated response
        """
        # Intelligent simulation based on prompt content
        prompt_lower = prompt.lower()
        
        # Mental health related responses
        if any(term in prompt_lower for term in ['mental_health', 'anxiety', 'depression', 'stress']):
            responses = [
                "I understand you're dealing with [MENTAL_HEALTH_0]. It's important to seek professional help. "
                "Consider talking to a licensed therapist or counselor who can provide personalized support. "
                "Remember, taking care of your mental health is just as important as physical health.",
                
                "Dealing with [MENTAL_HEALTH_0] can be challenging. Here are some steps that might help: "
                "1) Reach out to a mental health professional, 2) Practice self-care activities, "
                "3) Connect with supportive friends or family, 4) Consider mindfulness or meditation practices. "
                "Would you like more specific information on any of these?",
                
                "Thank you for sharing about [MENTAL_HEALTH_0]. Many people experience similar challenges. "
                "Professional support can make a significant difference. If you're in crisis, please contact "
                "a crisis helpline immediately. Otherwise, scheduling an appointment with a therapist can be "
                "a great first step toward feeling better."
            ]
            return random.choice(responses)
        
        # Disease/health related responses
        elif any(term in prompt_lower for term in ['disease', 'diabetes', 'cancer', 'health condition']):
            responses = [
                "For [DISEASE_0], it's crucial to work closely with healthcare professionals. "
                "They can provide proper diagnosis, treatment plans, and ongoing monitoring. "
                "Additionally, maintaining a healthy lifestyle through proper diet, exercise, and "
                "medication adherence (if prescribed) is important.",
                
                "Managing [DISEASE_0] requires comprehensive medical care. I recommend: "
                "1) Consulting with a specialist, 2) Following prescribed treatment plans, "
                "3) Regular check-ups and monitoring, 4) Staying informed about your condition. "
                "Your healthcare team can provide personalized guidance.",
                
                "Living with [DISEASE_0] can present challenges, but modern medicine offers many "
                "treatment options. Work with your healthcare provider to develop a management plan "
                "that works for you. Support groups and patient education resources can also be helpful."
            ]
            return random.choice(responses)
        
        # Contact/personal information queries
        elif any(term in prompt_lower for term in ['email', 'phone', 'contact']):
            responses = [
                "I can help you with that. Based on your contact information ([EMAIL_0] or [PHONE_0]), "
                "here's what I suggest: Make sure to keep your contact details updated and verify "
                "the information before sharing with others.",
                
                "Thanks for providing your contact details. For privacy reasons, always be careful about "
                "where you share information like [EMAIL_0] and [PHONE_0]. Use secure channels when possible."
            ]
            return random.choice(responses)
        
        # Location-based queries
        elif any(term in prompt_lower for term in ['location', 'city', 'state', 'country']):
            responses = [
                "In [LOCATION_0], there are various resources available. I can help you find specific "
                "services or information relevant to your area. What specific assistance are you looking for?",
                
                "For someone in [LOCATION_0], I recommend checking local resources and services. "
                "Many areas have community programs and support systems available."
            ]
            return random.choice(responses)
        
        # Age-related queries
        elif 'age' in prompt_lower:
            responses = [
                "At [AGE_0], it's important to consider age-appropriate recommendations. "
                "Everyone's situation is unique, so personalized advice from professionals is valuable.",
                
                "For someone who is [AGE_0], there are specific considerations to keep in mind. "
                "I'm here to provide general information, but professional consultation is recommended "
                "for personalized guidance."
            ]
            return random.choice(responses)
        
        # General helpful responses
        else:
            responses = [
                "I understand your concern. Based on the information you've provided, I recommend "
                "consulting with appropriate professionals who can give you personalized advice. "
                "Is there anything specific you'd like to know more about?",
                
                "Thank you for your question. While I can provide general information, it's always best "
                "to seek professional advice for personal matters. What specific aspect would you like "
                "me to explain further?",
                
                "I'm here to help. Based on your query, it seems you're looking for guidance on a "
                "sensitive matter. Remember that professional experts in relevant fields can provide "
                "the most accurate and personalized assistance. How can I assist you further?",
                
                "That's an important question. Here's some general information that might help: "
                "Always prioritize your well-being and don't hesitate to reach out to qualified "
                "professionals when needed. What else would you like to know?"
            ]
            return random.choice(responses)
    
    def _call_openai_api(self, prompt: str, max_tokens: int) -> str:
        """
        Call OpenAI API for real LLM response
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens in response
            
        Returns:
            API response text
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful and empathetic AI assistant. "
                     "Provide supportive, informative responses while maintaining user privacy."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            # Fallback to simulation on error
            return self._simulate_response(prompt)


# Singleton instance for the application
_llm_client = None


def get_llm_client(api_key: Optional[str] = None, use_simulation: bool = True) -> LLMClient:
    """
    Get or create LLM client singleton
    
    Args:
        api_key: OpenAI API key
        use_simulation: Whether to use simulation mode
        
    Returns:
        LLMClient instance
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient(api_key=api_key, use_simulation=use_simulation)
    return _llm_client
