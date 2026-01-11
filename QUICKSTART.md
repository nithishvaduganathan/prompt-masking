# Quick Start Guide

## Privacy-Preserving AI Chatbot - Get Started in 5 Minutes

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/nithishvaduganathan/prompt-masking.git
cd prompt-masking
```

2. **Create virtual environment** (recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Optional: Install spaCy model for name detection**
```bash
python -m spacy download en_core_web_sm
```

### Running the Application

#### Option 1: Quick Start (Default)
```bash
python run.py
```

Then open your browser to: http://localhost:5000

#### Option 2: With Debug Mode (Development Only)
```bash
export FLASK_DEBUG=True  # On Windows: set FLASK_DEBUG=True
python run.py
```

#### Option 3: Production Deployment
```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### Testing the System

#### 1. Run the Demo Script
```bash
python demo.py
```

This will showcase masking/unmasking with various examples.

#### 2. Test the Web Interface
1. Start the application: `python run.py`
2. Open browser: http://localhost:5000
3. Try these example queries:
   - "I'm 25 years old and dealing with anxiety"
   - "My email is john@example.com and I have diabetes"
   - "I'm a female living in New York with depression"

#### 3. Test the API Endpoints

**Mask sensitive data:**
```bash
curl -X POST http://localhost:5000/api/mask \
  -H "Content-Type: application/json" \
  -d '{"text": "I have PTSD and my email is test@example.com"}'
```

**Chat endpoint:**
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I am 30 years old with anxiety"}'
```

**Health check:**
```bash
curl http://localhost:5000/api/health
```

### Protected Data Types

The system automatically detects and masks:

- ✅ **Mental Health**: depression, anxiety, PTSD, bipolar, OCD, ADHD, etc.
- ✅ **Medical Conditions**: diabetes, cancer, HIV, COVID-19, heart disease, etc.
- ✅ **Contact Info**: email addresses, phone numbers
- ✅ **Personal Data**: age, gender
- ✅ **Locations**: cities, states, countries
- ✅ **Names**: (with optional spaCy NER)

### Configuration

Create a `.env` file (optional):
```bash
cp .env.example .env
```

Edit `.env` to customize:
```
SECRET_KEY=your-secret-key
FLASK_DEBUG=False
OPENAI_API_KEY=your-api-key  # Optional for real LLM
```

### Using OpenAI Integration

By default, the system uses simulated responses. To use OpenAI:

1. Get an API key from https://platform.openai.com
2. Set environment variable:
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   ```
3. Modify `app/llm_client.py` or set `use_simulation=False`

### Troubleshooting

**Issue**: Dependencies won't install
- **Solution**: Upgrade pip: `pip install --upgrade pip`

**Issue**: spaCy model not found
- **Solution**: Install model: `python -m spacy download en_core_web_sm`
- Or use without spaCy (names won't be masked)

**Issue**: Port 5000 already in use
- **Solution**: Change port in run.py or use: `python run.py --port 8000`

**Issue**: CORS errors in browser
- **Solution**: Check CORS configuration in `app/__init__.py`

### Project Structure

```
prompt-masking/
├── app/
│   ├── __init__.py          # Flask app setup
│   ├── masking/             # Masking logic
│   ├── routes/              # API endpoints
│   ├── templates/           # HTML templates
│   └── static/              # CSS & JavaScript
├── run.py                   # Application entry point
├── demo.py                  # Demonstration script
├── requirements.txt         # Dependencies
└── README.md               # Full documentation
```

### Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API endpoints
- Customize masking patterns in `app/masking/masker.py`
- Modify UI in `app/templates/index.html`
- Add new sensitive data patterns

### Support

For issues or questions:
- Check the [README.md](README.md)
- Review the demo script: `python demo.py`
- Open an issue on GitHub

### Security Note

⚠️ **Important**: This is a research/educational project. For production use with real sensitive data:
- Conduct security audit
- Ensure HIPAA/GDPR compliance
- Use proper authentication
- Enable HTTPS
- Use production WSGI server (Gunicorn)

---

**Enjoy building privacy-preserving AI applications!** 🔐
