import logging
import google.generativeai as genai
from typing import Dict, List, Any, Optional
from app import app
from dotenv import load_dotenv
import os

load_dotenv()


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

def initialize_gemini_model():
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            safety_settings=SAFETY_SETTINGS,
            generation_config={
                "temperature": 0.0,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 200,
            }
        )
        return model
    except Exception as e:
        logging.error(f"Error initializing Gemini model: {e}")
        return None

def generate_ai_response(
    query: str, 
    consumption: Optional[Dict[str, Any]] = None,
    generation: Optional[List[Dict[str, Any]]] = None
) -> str:

    logging.info(f"Generating AI response for query: {query}")
    
    try:
        model = initialize_gemini_model()
        if not model:
            return "Sorry, I'm unable to process your request at the moment. The AI assistant is unavailable."
        
        #   context with available prediction data
        context = "I'm an energy management assistant helping with home energy optimization.\n\n"
        
        if consumption and 'total' in consumption and 'devices' in consumption:
            context += "Energy consumption data:\n"
            context += f"- Total predicted consumption: {consumption['total']:.2f} kWh\n"
            context += "- Device breakdown:\n"
            for device, value in consumption['devices'].items():
                context += f"  * {device}: {value:.2f} kWh\n"
            context += "\n"
        
        if generation and len(generation) > 0:
            context += "Solar power generation forecast:\n"
            for day_data in generation:
                context += f"- {day_data['date']}: {day_data['prediction_kwh']:.2f} kWh\n"
            context += "\n"
        
        #    domain knowledge
        context += """
        Important energy concepts:
        - Load shifting: Moving energy usage to times when renewable energy is plentiful
        - Energy efficiency: Reducing energy consumption through better practices or equipment
        - Self-consumption: Using generated solar energy directly rather than exporting to grid
        - Base load: Minimum amount of power needed to meet essential demands
        - Peak load: Maximum power demand, usually during evening hours
        """
        
        prompt = f"""Respond to the user's question {query} with a clear, concise answer that considers
          {context}. don't use markdown format!! only simple text not exceed two ore tree short sentence! and respecte context!"""
        
        response = model.generate_content(prompt)
        
        if hasattr(response, 'text'):
            return response.text
        else:
            logging.error("Received unexpected response format from Gemini API")
            return "I'm sorry, I wasn't able to generate a proper response to your question."
            
    except Exception as e:
        logging.error(f"Error generating AI response: {e}")
        return "I apologize, but I encountered an error while processing your question. Please try again later."
