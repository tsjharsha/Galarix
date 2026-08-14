# 🎨 Frontend Update - Groq API Integration

Your React frontend has been updated to work with the new **Groq-based backend**!

## 📋 What Changed

### Backend Changes
- **LLM Provider**: Ollama → Groq API (cloud-based, free tier)
- **Endpoint**: `/generate-stream` still works the same way
- **Response Structure**: Now includes detailed schema components

### Frontend Changes
1. **PromptInput.jsx** - Updated to handle new response structure
   - Changed `payload.transactions` → `payload.sample_data`
   - Added support for detailed schema: `variables`, `distributions`, `dependencies`, `constraints`
   - Added detection info display: `detected_entities`, `confidence`, `reasoning`, `llm_based`
   - Better error handling with helpful Groq API messages
   - Updated status messages with emojis for better UX

2. **App.jsx** - Updated to pass new data to components
   - Added state for restored schema components
   - Pass all new props to PromptInput

3. **Header.jsx & Sidebar.jsx** - No changes needed
   - Compatible with existing backend

## 🚀 Key Features Now Available

✅ **Multi-Entity Detection**: Shows when multiple data domains are detected
✅ **Confidence Scores**: Displays how confident the AI is in its classification
✅ **Groq AI Integration**: See if classification was LLM-based or embedding-based
✅ **Schema Components**: View variables, distributions, constraints separately
✅ **Better Error Messages**: Clear guidance if Groq API key is missing

## 📦 Installation & Setup

### 1. Install Dependencies

```bash
cd Finsyn/fintech-synthetic-ui
npm install
```

### 2. Ensure Backend is Running

```bash
cd Finsyn/fintech-backend
pip install -r requirements.txt

# Set Groq API key
export GROQ_API_KEY="your-api-key-here"

# Run backend
python app.py
```

The backend will start on `http://localhost:5000`

### 3. Run Frontend (Development)

```bash
cd Finsyn/fintech-synthetic-ui
npm start
```

Frontend will open on `http://localhost:3000`

## 🔄 Data Flow

```
User Input
   ↓
Frontend: PromptInput.jsx
   ↓ (POST to /generate-stream)
Backend: app.py
   ↓
Groq API (Semantic Classification)
   ↓ (llm_based = true)
Schema Manager (Get data contract)
   ↓
Frontend receives:
  - detected_entities: ["credit_card_activity"]
  - confidence: 0.95
  - llm_based: true
  - schema, variables, distributions, constraints
  - sample_data (synthetic data rows)
   ↓
Display in tabs and table
```

## 🎯 Response Structure (New)

The backend now sends this complete structure:

```json
{
  "done": true,
  "status": "single_entity|multi_entity",
  "detected_entities": ["credit_card_activity"],
  "confidence": 0.95,
  "confidence_profile": {},
  "modifiers": {},
  "reasoning": "user wants credit card transactions",
  "llm_based": true,
  "schema": { "meta": {...} },
  "variables": { "amount": {...}, "merchant": {...} },
  "distributions": { "amount": "normal", "merchant": "categorical" },
  "dependencies": {},
  "constraints": {},
  "dataContract": { /* full contract */ },
  "sample_data": [ /* 3 sample rows */ ]
}
```

## 🐛 Troubleshooting

### Error: "Failed to connect to backend"
- Ensure `http://localhost:5000` is running
- Check that `python app.py` was executed in backend folder
- Look at backend terminal for error messages

### Error: "GROQ_API_KEY missing"
- Backend needs the API key set
- Get it from: https://console.groq.com
- Set it before running: `export GROQ_API_KEY="your-key"`

### Data not showing in table
- Check browser console (F12) for errors
- Verify backend response includes `sample_data` (not `transactions`)
- Check that schema is properly generated

### Slow response
- Groq free tier may have rate limits
- Wait a moment and retry
- Consider using a simpler prompt

## 📊 UI Components Updated

### Detection Info Box
Shows green box with:
- Status (Single/Multi-entity)
- Detected entities
- Confidence percentage
- Whether it's LLM-based or embedding-based

### Schema Tabs
Multiple tabs for viewing different schema aspects:
- **Schema**: Overall structure
- **Variables**: Field definitions
- **Distributions**: Data distribution rules
- **Constraints**: Validation rules

### Chat History
Shows entity detection info with each response

## 🔧 Advanced

### Changing the Groq Model

To use a different Groq model, edit `backend/stage_1_5/ai_client.py`:

```python
MODEL = "llama2-70b-4096"  # or other available models
```

Available models:
- `mixtral-8x7b-32768` (current, good balance)
- `llama2-70b-4096` (larger, slower)
- `gemma-7b-it` (smaller, faster)

### Building for Production

```bash
npm run build
```

Creates optimized build in `build/` folder.

---

**Frontend is ready!** 🎉 Start the backend and frontend to see it in action.
