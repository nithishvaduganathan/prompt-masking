"""
Flask Routes for Privacy-Preserving Chatbot API
"""

from flask import Blueprint, request, jsonify, render_template
from app.masking import mask_prompt, unmask_response
from app.llm_client import get_llm_client
from typing import Dict, Any
import traceback

# Create Blueprint
main_bp = Blueprint('main', __name__)

# Store session mappings (in production, use proper session management or database)
session_mappings = {}


@main_bp.route('/')
def index():
    """Render the main chatbot interface"""
    return render_template('index.html')


@main_bp.route('/api/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint - handles end-to-end privacy-preserving conversation
    
    Request JSON:
        {
            "message": "user query text",
            "session_id": "optional session identifier",
            "use_spacy": false (optional)
        }
    
    Response JSON:
        {
            "success": true,
            "original_prompt": "original user query",
            "masked_prompt": "masked query with placeholders",
            "llm_response": "masked LLM response",
            "final_response": "unmasked final response",
            "detected_entities": ["list of detected sensitive entities"],
            "session_id": "session identifier"
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: message'
            }), 400
        
        original_message = data['message']
        session_id = data.get('session_id', 'default')
        use_spacy = data.get('use_spacy', False)
        
        # Step 1: Mask the prompt
        masking_result = mask_prompt(original_message, use_spacy=use_spacy)
        
        # Store mappings for this session
        if session_id not in session_mappings:
            session_mappings[session_id] = {}
        session_mappings[session_id].update(masking_result.mappings)
        
        # Step 2: Send masked prompt to LLM
        llm_client = get_llm_client(use_simulation=True)
        llm_response = llm_client.generate_response(masking_result.masked_text)
        
        # Step 3: Unmask the LLM response
        final_response = unmask_response(llm_response, masking_result.mappings)
        
        return jsonify({
            'success': True,
            'original_prompt': original_message,
            'masked_prompt': masking_result.masked_text,
            'llm_response': llm_response,
            'final_response': final_response,
            'detected_entities': masking_result.detected_entities,
            'session_id': session_id
        })
    
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@main_bp.route('/api/mask', methods=['POST'])
def mask():
    """
    Endpoint to mask text only
    
    Request JSON:
        {
            "text": "text to mask",
            "use_spacy": false (optional)
        }
    
    Response JSON:
        {
            "success": true,
            "original_text": "original text",
            "masked_text": "masked text",
            "mappings": {"[PLACEHOLDER_0]": "original_value"},
            "detected_entities": ["list of entities"]
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: text'
            }), 400
        
        text = data['text']
        use_spacy = data.get('use_spacy', False)
        
        result = mask_prompt(text, use_spacy=use_spacy)
        
        return jsonify({
            'success': True,
            'original_text': result.original_text,
            'masked_text': result.masked_text,
            'mappings': result.mappings,
            'detected_entities': result.detected_entities
        })
    
    except Exception as e:
        print(f"Error in mask endpoint: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@main_bp.route('/api/unmask', methods=['POST'])
def unmask():
    """
    Endpoint to unmask text
    
    Request JSON:
        {
            "masked_text": "text with placeholders",
            "mappings": {"[PLACEHOLDER_0]": "original_value"}
        }
    
    Response JSON:
        {
            "success": true,
            "masked_text": "text with placeholders",
            "unmasked_text": "original text restored"
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'masked_text' not in data or 'mappings' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: masked_text and mappings'
            }), 400
        
        masked_text = data['masked_text']
        mappings = data['mappings']
        
        unmasked = unmask_response(masked_text, mappings)
        
        return jsonify({
            'success': True,
            'masked_text': masked_text,
            'unmasked_text': unmasked
        })
    
    except Exception as e:
        print(f"Error in unmask endpoint: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@main_bp.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Privacy-Preserving AI Chatbot'
    })
