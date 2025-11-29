# OMR Evaluator - Integration Guide

## 📦 Files to Include

**Core file (REQUIRED):**
```
omr_evaluator_v2.py  - Complete, production-ready system
```

**Supporting files (OPTIONAL):**
```
.env                 - Stores API key (auto-created)
requirements.txt     - Dependencies
```

## 🔧 Requirements

```
Python 3.8+
pillow>=10.0.0
requests>=2.31.0
pandas>=2.0.0
openpyxl>=3.1.0
```

Auto-installed on first run.

## 🔑 API Setup (One-time)

1. Visit: https://console.groq.com/keys
2. Sign up (FREE, no credit card)
3. Create API Key
4. First run will prompt for key (saves to .env)

## 🚀 Usage

### Option 1: Interactive (File Picker)
```bash
python omr_evaluator_v2.py
```

### Option 2: Command Line
```bash
# Simple answer key (5 questions)
python omr_evaluator_v2.py --image sheet.jpg --key ABCDB

# JSON answer key
python omr_evaluator_v2.py --image sheet.jpg --key answers.json

# Specify output file
python omr_evaluator_v2.py --image sheet.jpg --key ABCDB --output result.json
```

### Option 3: Import as Module
```python
from omr_evaluator_v2 import evaluate_single, MarkCalculator, detect_answers

# Full evaluation
results = evaluate_single("sheet.jpg", "ABCDB")
print(f"Score: {results['total_marks']}/{results['max_marks']}")

# Just detection
api_key = "your_groq_api_key"
answers = detect_answers("sheet.jpg", api_key, num_questions=30)
print(answers)  # {"answers": {"1": "A", "2": "B", ...}, "confidence": 0.95}

# Just calculation
calc = MarkCalculator("ABCDB")
total, max_marks, details = calc.calculate({"1": "A", "2": "B", "3": "C", "4": "D", "5": "A"})
print(f"Score: {total}/{max_marks}")
```

## 📊 Output Format

```json
{
  "image": "sheet.jpg",
  "timestamp": "2025-11-29T10:30:00",
  "detected_answers": {
    "1": "A",
    "2": "B",
    "3": "C",
    "4": "D",
    "5": "A"
  },
  "detection_confidence": 0.95,
  "total_marks": 80,
  "max_marks": 100,
  "percentage": 80.0,
  "details": [
    {"question": "Q1", "correct": "A", "student": "A", "marks": 20, "status": "correct"},
    {"question": "Q2", "correct": "B", "student": "B", "marks": 20, "status": "correct"},
    ...
  ]
}
```

## ⚠️ Known Limitations

| Issue | Workaround |
|-------|------------|
| AI gives different results on each run | Run 2-3 times and use majority vote |
| Watermarked images cause errors | Use clean OMR sheets |
| Windows CMD shows encoding errors | Use `$env:PYTHONIOENCODING='utf-8'` |
| Rate limit (30 req/min) | Add delays between calls |

## 🔌 Integration Points

### For Web Apps (Flask/Django)
```python
from omr_evaluator_v2 import evaluate_single
import os

os.environ['GROQ_API_KEY'] = 'your_key'

@app.route('/evaluate', methods=['POST'])
def evaluate():
    image = request.files['image']
    answer_key = request.form['answer_key']
    
    image_path = save_uploaded_file(image)
    results = evaluate_single(image_path, answer_key)
    
    return jsonify(results)
```

### For Desktop Apps
```python
from omr_evaluator_v2 import evaluate_single, select_file

# Use built-in file picker
image_path = select_file("Select OMR Sheet", [("Images", "*.jpg *.png")])
results = evaluate_single(image_path, "ABCDB")
```

### For Batch Processing
```python
import pandas as pd
from omr_evaluator_v2 import evaluate_single

df = pd.read_excel('students.xlsx')
results = []

for _, row in df.iterrows():
    result = evaluate_single(row['image_path'], row['answer_key'])
    results.append({
        'roll': row['roll_number'],
        'marks': result['total_marks']
    })

pd.DataFrame(results).to_csv('batch_results.csv')
```

## ✅ Checklist Before Sharing

- [ ] Test with a sample OMR image
- [ ] Verify Groq API key works
- [ ] Check all dependencies install correctly
- [ ] Test on target OS (Windows/Linux/Mac)
- [ ] Document any custom answer key formats

## 📞 Support

If issues occur:
1. Check API key is valid
2. Verify image is clear (no watermarks)
3. Try with a simple 5-question test first
4. Check internet connection for API calls

