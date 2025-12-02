#!/usr/bin/env python3
"""
OMR Evaluator - Final Version
=============================

Single provider (Groq) with 3-pass validation using different prompts.
Majority voting for final answers.

Usage:
    python omr_final.py image.jpg
    python omr_final.py image.jpg --key ABCDB
"""

import sys
import json
import base64
import io
import os
import requests
from pathlib import Path
from collections import Counter

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except: pass

from PIL import Image

# ============================================
# CONFIG
# ============================================

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# Three different prompts for varied detection
PROMPTS = [
    # Prompt 1: Standard
    """Analyze this OMR answer sheet. For each question (1-{n}), identify which bubble (A, B, C, or D) is FILLED/DARKENED.

Return ONLY JSON: {{"answers": {{"1": "A", "2": "B", ...}}, "confidence": 0.95}}
If no bubble is filled, use "X". Return ONLY the JSON.""",

    # Prompt 2: Detailed instructions
    """You are an OMR scanner. Look at this answer sheet carefully.

TASK: Find the DARKENED/FILLED bubble for each question 1-{n}.
- A filled bubble is BLACK/DARK
- An empty bubble is WHITE/LIGHT
- Check each row systematically

Return ONLY this format: {{"answers": {{"1": "A", "2": "B"}}, "confidence": 0.9}}
No explanation. Just JSON.""",

    # Prompt 3: Column-aware
    """This OMR sheet has questions arranged in columns. Scan each column and identify marked answers.

For questions 1-{n}, which option (A/B/C/D) is marked?
A marked answer appears as a FILLED/DARK circle.

Output format: {{"answers": {{"1": "A"}}, "confidence": 0.9}}
Return ONLY valid JSON, nothing else."""
]

# ============================================
# SETUP
# ============================================

def get_api_key():
    """Get Groq API key."""
    key = os.getenv('GROQ_API_KEY')
    if key:
        return key
    
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if 'GROQ_API_KEY=' in line:
                    return line.split('=', 1)[1].strip()
    
    print("\nGet free API key at: https://console.groq.com/keys")
    key = input("Enter GROQ_API_KEY: ").strip()
    
    if key:
        with open(env_path, 'a') as f:
            f.write(f"\nGROQ_API_KEY={key}\n")
    
    return key

def image_to_base64(image_path):
    """Convert image to base64."""
    with Image.open(image_path) as img:
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        max_size = 1024
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        return f"data:image/jpeg;base64,{base64.b64encode(buffer.getvalue()).decode()}"

# ============================================
# DETECTION
# ============================================

def detect_single_pass(image_data, api_key, prompt, pass_num):
    """Run single detection pass."""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_data}},
                {"type": "text", "text": prompt}
            ]
        }],
        "max_tokens": 1000,
        "temperature": 0.2 + (pass_num * 0.1)  # Slightly vary temperature
    }
    
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            return None
        
        text = response.json()['choices'][0]['message']['content']
        
        # Clean JSON
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        elif '```' in text:
            text = text.split('```')[1].split('```')[0]
        
        text = text.strip()
        if not text.startswith('{'):
            start = text.find('{')
            if start >= 0:
                brace_count = 0
                for i, c in enumerate(text[start:], start):
                    if c == '{': brace_count += 1
                    elif c == '}': brace_count -= 1
                    if brace_count == 0:
                        text = text[start:i+1]
                        break
        
        # Try parsing JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError as je:
            # Try to fix common JSON issues
            import re
            
            # Fix single quotes to double quotes
            fixed_text = text.replace("'", '"')
            
            # Remove trailing commas
            fixed_text = re.sub(r',\s*}', '}', fixed_text)
            fixed_text = re.sub(r',\s*]', ']', fixed_text)
            
            # Try to extract answers using regex as fallback
            try:
                return json.loads(fixed_text)
            except:
                # Last resort: try to extract answers with regex
                answer_pattern = r'"(\d+)":\s*"([A-DX])"'
                matches = re.findall(answer_pattern, text, re.IGNORECASE)
                
                if matches:
                    answers = {q: a.upper() for q, a in matches}
                    return {"answers": answers, "confidence": 0.7}
                
                print(f"   JSON parse error: {str(je)[:50]}")
                return None
        
    except Exception as e:
        print(f"   Error: {e}")
        return None

def detect_with_voting(image_path, num_questions=10):
    """
    Run 3 detection passes and use majority voting.
    """
    print(f"\nAnalyzing: {Path(image_path).name}")
    print("Running 3-pass validation...")
    
    api_key = get_api_key()
    if not api_key:
        print("No API key!")
        return None
    
    image_data = image_to_base64(image_path)
    
    # Run 3 passes with different prompts
    all_results = []
    
    for i, prompt_template in enumerate(PROMPTS):
        prompt = prompt_template.format(n=num_questions)
        print(f"   Pass {i+1}/3...", end=" ")
        
        result = detect_single_pass(image_data, api_key, prompt, i)
        
        if result and 'answers' in result:
            all_results.append(result['answers'])
            print(f"OK ({len(result['answers'])} answers)")
        else:
            print("Failed")
    
    if not all_results:
        print("All passes failed!")
        return None
    
    # Majority voting
    print("\nVoting on results...")
    
    all_questions = set()
    for r in all_results:
        all_questions.update(r.keys())
    
    final = {}
    details = []
    
    for q in sorted(all_questions, key=lambda x: int(x) if x.isdigit() else 0):
        votes = [r.get(q, 'X') for r in all_results]
        counter = Counter(votes)
        winner, count = counter.most_common(1)[0]
        
        unanimous = (count == len(all_results))
        confidence = count / len(all_results)
        
        final[q] = winner
        details.append({
            "q": q,
            "answer": winner,
            "votes": votes,
            "unanimous": unanimous,
            "confidence": confidence
        })
    
    return {
        "answers": final,
        "details": details,
        "passes": len(all_results)
    }

# ============================================
# MARK CALCULATION
# ============================================

def calculate_marks(detected, answer_key):
    """Calculate marks from detected answers."""
    if isinstance(answer_key, str) and not answer_key.startswith('{'):
        # Simple format: "ABCDB"
        key = {str(i+1): ans for i, ans in enumerate(answer_key)}
        marks_each = 1
    else:
        # JSON format
        if isinstance(answer_key, str):
            parsed = json.loads(answer_key)
        else:
            parsed = answer_key
        
        if 'Q1' in parsed and isinstance(parsed['Q1'], dict):
            key = {k.replace('Q',''): v['answer'] for k, v in parsed.items()}
            marks_each = list(parsed.values())[0].get('marks', 1)
        else:
            key = {k.replace('Q',''): v for k, v in parsed.items()}
            marks_each = 1
    
    total = 0
    max_total = 0
    results = []
    
    for q, correct in key.items():
        student = detected.get(q, 'X')
        earned = marks_each if student.upper() == correct.upper() else 0
        total += earned
        max_total += marks_each
        
        results.append({
            "q": f"Q{q}",
            "correct": correct,
            "student": student,
            "marks": earned,
            "status": "OK" if earned > 0 else "WRONG"
        })
    
    return total, max_total, results

# ============================================
# MAIN
# ============================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="OMR Evaluator with 3-pass voting")
    parser.add_argument('image', nargs='?', help='OMR image path')
    parser.add_argument('--key', '-k', help='Answer key (ABCDB format)')
    parser.add_argument('--questions', '-q', type=int, default=10, help='Number of questions')
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("OMR EVALUATOR (3-Pass Voting)")
    print("=" * 60)
    
    # Get image
    image_path = args.image
    if not image_path:
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            image_path = filedialog.askopenfilename(
                title="Select OMR Image",
                filetypes=[("Images", "*.jpg *.jpeg *.png")]
            )
            root.destroy()
        except:
            image_path = input("Enter image path: ").strip()
    
    if not image_path or not Path(image_path).exists():
        print("No valid image!")
        return
    
    # Detect with voting
    result = detect_with_voting(image_path, args.questions)
    
    if not result:
        return
    
    # Display detection results
    print("\n" + "=" * 60)
    print("DETECTION RESULTS")
    print("=" * 60)
    print(f"{'Q':<5} {'Answer':<8} {'Votes':<15} {'Status'}")
    print("-" * 60)
    
    for d in result['details']:
        votes_str = ','.join(d['votes'])
        status = "UNANIMOUS" if d['unanimous'] else f"{d['confidence']*100:.0f}% agree"
        icon = "[OK]" if d['unanimous'] else "[?]"
        print(f"Q{d['q']:<4} {d['answer']:<8} {votes_str:<15} {status} {icon}")
    
    # Summary
    unanimous = sum(1 for d in result['details'] if d['unanimous'])
    total_q = len(result['details'])
    print("-" * 60)
    print(f"Unanimous: {unanimous}/{total_q} questions")
    
    # Calculate marks if answer key provided
    if args.key:
        print("\n" + "=" * 60)
        print("MARK CALCULATION")
        print("=" * 60)
        
        total, max_marks, calc_results = calculate_marks(result['answers'], args.key)
        
        for r in calc_results:
            icon = "[OK]" if r['status'] == 'OK' else "[X]"
            print(f"{r['q']}: {r['student']} (correct: {r['correct']}) {icon}")
        
        print("-" * 60)
        print(f"SCORE: {total}/{max_marks} ({total/max_marks*100:.1f}%)")
    
    # Save results
    output = {
        "image": str(image_path),
        "detected_answers": result['answers'],
        "voting_details": result['details'],
        "unanimous_count": unanimous,
        "total_questions": total_q
    }
    
    output_path = Path(image_path).stem + "_results.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nSaved: {output_path}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()

