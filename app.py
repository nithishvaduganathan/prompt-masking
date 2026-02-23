"""
Prompt Masking Local Proxy — Flask Application
"""

import logging
from flask import Flask, render_template, request, jsonify

from config import Config
from services.chat_pipeline import process_message
from services.local_llm import ollama_client
from storage.conversation_store import conversation_store

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = Config.SECRET_KEY


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.route("/api/chat", methods=["POST"])
def chat():
    """Process a user message through the masking pipeline."""
    data = request.get_json(force=True)
    user_message = data.get("message", "").strip()
    conversation_id = data.get("conversation_id")
    masking_enabled = data.get("masking_enabled", True)

    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    try:
        result = process_message(user_message, conversation_id, masking_enabled)
        return jsonify(result)
    except Exception as exc:
        logger.error("Chat error: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@app.route("/api/conversations", methods=["GET"])
def list_conversations():
    """Return all conversations, newest first."""
    convs = conversation_store.list_conversations()
    return jsonify(convs)


@app.route("/api/conversations", methods=["POST"])
def create_conversation():
    """Create a new empty conversation and return its ID."""
    data = request.get_json(force=True) if request.is_json else {}
    title = data.get("title", "New Chat")
    conv_id = conversation_store.create_conversation(title)
    return jsonify({"id": conv_id, "title": title}), 201


@app.route("/api/conversations/<conv_id>", methods=["GET"])
def get_conversation(conv_id):
    """Get conversation + its messages."""
    conv = conversation_store.get_conversation(conv_id)
    if not conv:
        return jsonify({"error": "Conversation not found"}), 404
    messages = conversation_store.get_messages(conv_id)
    conv["messages"] = messages
    return jsonify(conv)


@app.route("/api/conversations/<conv_id>", methods=["DELETE"])
def delete_conversation(conv_id):
    """Delete a conversation and all its messages."""
    ok = conversation_store.delete_conversation(conv_id)
    if not ok:
        return jsonify({"error": "Conversation not found"}), 404
    return jsonify({"success": True})


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    ollama_ok = ollama_client.check_health()
    gemini_ok = bool(Config.GEMINI_API_KEY)
    return jsonify({
        "status": "ok" if (ollama_ok and gemini_ok) else "degraded",
        "ollama": "connected" if ollama_ok else "unavailable",
        "gemini": "configured" if gemini_ok else "missing API key",
    })


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("Starting Prompt Masking Local Proxy …")

    # Quick health report
    if ollama_client.check_health():
        logger.info("✓ Ollama is running with model '%s'", Config.LOCAL_MODEL)
    else:
        logger.warning("✗ Ollama is NOT reachable or model '%s' not found", Config.LOCAL_MODEL)

    if Config.GEMINI_API_KEY:
        logger.info("✓ Gemini API key is configured")
    else:
        logger.warning("✗ GEMINI_API_KEY is not set — chat will not work")

    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)
