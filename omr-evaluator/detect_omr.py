#!/usr/bin/env python3
"""
Dedicated OMR Detection Script
Optimized for IAPT-PRMO style sheets with 30 questions.
"""

import sys
import json
import requests
import base64
import io
from pathlib import Path

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except: pass

from PIL import Image

# ============================================
# CONFIGURATION
# ============================================

def get_groq_token():
    """Get Groq API token from .env"""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip().startswith('GROQ_API_KEY='):
                    return line.split('=', 1)[1].strip()
    
    token = input("Enter Groq API key: ").strip()
    with open(env_path, 'w') as f:
        f.write(f"GROQ_API_KEY={token}\n")
    return token

# ============================================
# IMAGE HANDLING
# ============================================

def image_to_base64(image_path):
    """Convert image to base64."""
    with Image.open(image_path) as img:
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Keep good resolution for OMR detection
        max_size = 1500
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=90)
        img_bytes = buffer.getvalue()
        
        return f"data:image/jpeg;base64,{base64.b64encode(img_bytes).decode('utf-8')}"

# ============================================
# OMR DETECTION
# ============================================

def detect_answers(image_path, api_key):
    """
    Detect filled bubbles from OMR sheet.
    Optimized prompt for IAPT-PRMO style sheets.
    """
    print(f"\n📷 Analyzing: {image_path}")
    print("="*60)
    
    image_data = image_to_base64(image_path)
    
    # Highly specific prompt for this OMR format
    prompt = """This is an OMR (Optical Mark Recognition) answer sheet from an exam.

TASK: Identify which bubble (A, B, C, or D) is FILLED/DARKENED for each question.

The sheet has questions numbered 1-30 arranged in 3 columns:
- Column 1: Questions 1-10
- Column 2: Questions 11-20  
- Column 3: Questions 21-30

Each question has 4 bubble options: A, B, C, D (shown as circles)
A FILLED bubble appears DARK/BLACK compared to empty bubbles.

IMPORTANT:
- Look at each row carefully
- The DARKENED/FILLED circle is the student's answer
- Empty circles are light/unfilled
- If no bubble is filled, mark as "X"

Return ONLY a JSON object in this exact format:
{
  "answers": {
    "1": "A",
    "2": "B",
    "3": "C",
    ...
    "30": "D"
  },
  "confidence": 0.95
}

Analyze the image carefully and return ONLY the JSON."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_data}},
                    {"type": "text", "text": prompt}
                ]
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.1
    }
    
    print("🤖 Sending to Llama 4 Scout...")
    
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=120
    )
    
    if response.status_code != 200:
        print(f"❌ API Error: {response.text[:200]}")
        return None
    
    data = response.json()
    text = data['choices'][0]['message']['content']
    
    print(f"📥 Response received ({len(text)} chars)")
    
    # Clean JSON from markdown
    if '```json' in text:
        text = text.split('```json')[1].split('```')[0]
    elif '```' in text:
        text = text.split('```')[1].split('```')[0]
    
    text = text.strip()
    
    # Find JSON object
    if not text.startswith('{'):
        start = text.find('{')
        if start != -1:
            brace_count = 0
            for i, c in enumerate(text[start:], start):
                if c == '{': brace_count += 1
                elif c == '}': brace_count -= 1
                if brace_count == 0:
                    text = text[start:i+1]
                    break
    
    try:
        result = json.loads(text)
        return result
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parse error: {e}")
        print(f"Raw: {text[:500]}")
        return None

# ============================================
# MAIN
# ============================================

def main():
    print("\n" + "="*60)
    print("🔍 OMR ANSWER DETECTION")
    print("="*60)
    
    # Get image path
    if len(sys.argv) >= 2:
        image_path = sys.argv[1]
    else:
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            image_path = filedialog.askopenfilename(
                title="Select OMR Sheet Image",
                filetypes=[("Image files", "*.jpg *.jpeg *.png"), ("All", "*.*")]
            )
            root.destroy()
        except:
            image_path = input("Enter image path: ").strip()
    
    if not image_path or not Path(image_path).exists():
        print("❌ No valid image")
        return
    
    # Get API key
    api_key = get_groq_token()
    
    # Detect answers
    result = detect_answers(image_path, api_key)
    
    if not result:
        print("❌ Detection failed")
        return
    
    answers = result.get('answers', {})
    confidence = result.get('confidence', 0)
    
    # Display results
    print("\n" + "="*60)
    print("📝 DETECTED ANSWERS")
    print("="*60)
    
    # Show in columns like the OMR sheet
    print("\n   Q1-10        Q11-20       Q21-30")
    print("   " + "-"*40)
    
    for i in range(1, 11):
        q1 = str(i)
        q2 = str(i + 10)
        q3 = str(i + 20)
        
        a1 = answers.get(q1, '?')
        a2 = answers.get(q2, '?')
        a3 = answers.get(q3, '?')
        
        print(f"   Q{q1:>2}: {a1}       Q{q2:>2}: {a2}       Q{q3:>2}: {a3}")
    
    print("\n" + "="*60)
    print(f"✅ Confidence: {confidence*100:.0f}%")
    print(f"📊 Total questions detected: {len(answers)}")
    
    # Save to file
    output = {
        "image": str(image_path),
        "answers": answers,
        "confidence": confidence
    }
    
    with open("detected_answers.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"💾 Saved to: detected_answers.json")
    print("="*60 + "\n")
    
    return answers

if __name__ == "__main__":
    main()

