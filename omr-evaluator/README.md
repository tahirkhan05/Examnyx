# Open Source OMR Evaluator

Automated OMR (Optical Mark Recognition) sheet evaluation using Llama 3.2 Vision via Groq's FREE API.

## 🌟 Features

- ✅ **Zero datasets required** - works on any OMR image immediately
- ✅ **Auto-installs dependencies** - no manual pip install needed
- ✅ **Auto-manages API key** - one-time setup, saved for future
- ✅ **Two-model ensemble** - Llama 3.2 Vision 11B + 90B cross-validate
- ✅ **Automatic flagging** - disagreements and double bubbles detected
- ✅ **100% free** - uses Groq's free API tier
- ✅ **JSON export** - structured data for integration
- ✅ **File picker** - browse and select images via GUI

## 🚀 Quick Start

### First Time Setup (2 minutes)

1. **Get Groq API Key** (free):
   - Visit: https://console.groq.com/keys
   - Sign up / Log in (free, no credit card)
   - Click "Create API Key"
   - Copy the key

2. **Run the evaluator**:
   ```bash
   python omr_evaluator.py
   ```
   A file picker will open - select your OMR sheet image.

3. **Paste API key when prompted** (one-time only)

That's it! The system handles everything else.

### Future Usage

```bash
# Option 1: File picker (GUI)
python omr_evaluator.py

# Option 2: Direct path
python omr_evaluator.py any_image.jpg
```

## 📊 How It Works

1. **Llama 3.2 Vision 11B** analyzes the OMR sheet (primary)
2. **Llama 3.2 Vision 90B** validates independently (larger model)
3. **Ensemble voting** compares results:
   - Both agree → 99% confidence ✅
   - Disagree → 70% confidence, flagged for review ⚠️

## 📄 Output

### Console Output
```
======================================================================
📊 EVALUATION RESULTS
======================================================================

✅ Overall Confidence: 94.5%
📝 Total Questions Detected: 50
⚠️  Model Disagreements: 3
🚩 Double Bubbles Found: 1

----------------------------------------------------------------------
DETECTED ANSWERS:
----------------------------------------------------------------------
Q  1:     A ( 99%) ✅ AGREED
Q  2:     B ( 99%) ✅ AGREED
Q  3:     C ( 70%) ⚠️ DISPUTED
       └─> Llama: C, Qwen: D
...

💾 Complete results saved to: omr_results.json
```

### JSON File (omr_results.json)
```json
{
  "answers": {
    "1": {
      "answer": "A",
      "confidence": 0.99,
      "status": "AGREED"
    },
    "3": {
      "answer": "C",
      "confidence": 0.70,
      "status": "DISPUTED",
      "llama_says": "C",
      "qwen_says": "D"
    }
  },
  "overall_confidence": 0.945,
  "disagreements": ["3", "15"],
  "double_bubbles": [8]
}
```

## 💰 Cost

**$0** - Uses free HuggingFace Inference API (rate-limited but sufficient for demos and small-scale use)

## ⚙️ System Requirements

- Python 3.8 or higher
- Internet connection (for API calls)
- ~50MB disk space for dependencies

## 🔧 Troubleshooting

**"Module not found" error:**
- The script auto-installs packages. If it fails, manually run:
  ```bash
  pip install -r requirements.txt
  ```

**"Invalid API key" error:**
- Get a new key from https://console.groq.com/keys
- Delete `.env` file and run again to re-enter key

**"Image not found" error:**
- Use the file picker (just run without arguments)
- Or check that your file path is correct
- Supported formats: JPG, JPEG, PNG, GIF, BMP, WEBP

**API timeout:**
- Large images may take longer to process
- Try resizing your image to under 1024px
- Models typically respond in 5-30 seconds

**Rate limiting (429 error):**
- Groq free tier: ~30 requests/minute
- Wait 1-2 minutes and try again

**Emojis not showing (Windows):**
- Run in Windows Terminal instead of CMD
- Or set: `$env:PYTHONIOENCODING='utf-8'` before running

## 📁 Files Generated

- `.env` - Stores your HuggingFace token (created on first run)
- `omr_results.json` - Evaluation results in JSON format

## 🔒 Security

- Your HuggingFace token is stored locally in `.env`
- Never commit `.env` to version control (it's in `.gitignore`)
- Token is only sent to HuggingFace's official API

## 📝 License

Open source - use freely for any purpose.

## 🙏 Credits

- **Llama 3.2 Vision** by Meta AI
- **Qwen2-VL** by Alibaba Cloud
- **HuggingFace** for free inference API

