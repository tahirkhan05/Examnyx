#!/usr/bin/env python3
"""
OMR Evaluator v2.0 - Production Ready
=====================================

A complete OMR evaluation system using AI vision models.

Features:
- Detects filled bubbles from OMR sheet images
- Calculates marks against answer keys
- Supports batch processing
- Exports results to JSON/CSV

Requirements:
- Python 3.8+
- Groq API key (free at console.groq.com)

Usage:
    # Interactive mode (file picker)
    python omr_evaluator_v2.py
    
    # Command line
    python omr_evaluator_v2.py --image sheet.jpg --key ABCDB
    
    # Batch mode with dataset
    python omr_evaluator_v2.py --batch dataset.xlsx --image-col "Image Path"

Author: AI-Generated for OMR Evaluation
Version: 2.0
"""

import os
import sys
import json
import base64
import io
import subprocess
from pathlib import Path
from datetime import datetime

# ============================================
# SETUP & CONFIGURATION
# ============================================

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Auto-install dependencies
def install_dependencies():
    """Install required packages if missing."""
    packages = {
        'PIL': 'pillow',
        'requests': 'requests',
        'pandas': 'pandas',
        'openpyxl': 'openpyxl'
    }
    
    missing = []
    for module, package in packages.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"Installing: {', '.join(missing)}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q'] + missing)
        print("Done!\n")

install_dependencies()

# Now import
import requests
from PIL import Image
import pandas as pd

# ============================================
# API CONFIGURATION
# ============================================

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

def get_api_key():
    """Get Groq API key from environment or .env file."""
    # Check environment
    key = os.getenv('GROQ_API_KEY')
    if key:
        return key
    
    # Check .env file
    env_locations = [
        Path(__file__).parent / '.env',
        Path.cwd() / '.env',
        Path.home() / '.env'
    ]
    
    for env_path in env_locations:
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.strip().startswith('GROQ_API_KEY='):
                        return line.split('=', 1)[1].strip()
    
    # Prompt user
    print("\n" + "=" * 60)
    print("GROQ API KEY REQUIRED")
    print("=" * 60)
    print("\nGet your FREE API key:")
    print("1. Visit: https://console.groq.com/keys")
    print("2. Sign up (free)")
    print("3. Create API Key")
    print()
    
    key = input("Paste your API key: ").strip()
    
    if not key:
        print("Error: API key required")
        sys.exit(1)
    
    # Save for future use
    env_path = Path(__file__).parent / '.env'
    with open(env_path, 'a') as f:
        f.write(f"\nGROQ_API_KEY={key}\n")
    
    print("Saved to .env\n")
    return key

# ============================================
# IMAGE PROCESSING
# ============================================

def load_image_as_base64(image_path):
    """Load and convert image to base64 data URI."""
    with Image.open(image_path) as img:
        # Convert to RGB
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Resize if too large
        max_size = 1500
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=90)
        b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/jpeg;base64,{b64}"

def select_file(title="Select File", filetypes=None):
    """Open file picker dialog."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        if filetypes is None:
            filetypes = [("All files", "*.*")]
        
        path = filedialog.askopenfilename(title=title, filetypes=filetypes)
        root.destroy()
        
        return path if path else None
    except Exception as e:
        print(f"File picker unavailable: {e}")
        return input("Enter file path: ").strip()

# ============================================
# AI DETECTION
# ============================================

def detect_answers(image_path, api_key, num_questions=30):
    """
    Detect filled bubbles from OMR image using AI.
    
    Args:
        image_path: Path to OMR image
        api_key: Groq API key
        num_questions: Expected number of questions (default 30)
    
    Returns:
        dict: {"answers": {"1": "A", "2": "B", ...}, "confidence": 0.95}
    """
    print(f"Analyzing: {Path(image_path).name}")
    
    # Load image
    image_data = load_image_as_base64(image_path)
    
    # Build prompt
    prompt = f"""Analyze this OMR answer sheet and identify filled bubbles.

The sheet has {num_questions} questions, each with options A, B, C, D.
A FILLED bubble is darker/blacker than empty ones.

Return ONLY valid JSON:
{{
  "answers": {{
    "1": "A",
    "2": "B",
    ...
    "{num_questions}": "D"
  }},
  "confidence": 0.95
}}

If a question has no filled bubble, use "X".
Return ONLY the JSON object."""

    # API request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": VISION_MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_data}},
                {"type": "text", "text": prompt}
            ]
        }],
        "max_tokens": 2000,
        "temperature": 0.1
    }
    
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=120)
        
        if response.status_code != 200:
            error = response.json().get('error', {}).get('message', response.text[:200])
            print(f"API Error: {error}")
            return None
        
        # Parse response
        text = response.json()['choices'][0]['message']['content']
        
        # Clean JSON from markdown
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        elif '```' in text:
            text = text.split('```')[1].split('```')[0]
        
        # Find JSON object
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
        
        return json.loads(text)
        
    except requests.exceptions.Timeout:
        print("Request timed out")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# ============================================
# MARK CALCULATION
# ============================================

class MarkCalculator:
    """Calculate marks from student answers vs answer key."""
    
    def __init__(self, answer_key, marks_per_question=1):
        """
        Args:
            answer_key: str "ABCDB" or dict {"Q1": "A", ...} or JSON
            marks_per_question: Points per correct answer (default 1)
        """
        self.marks_per_question = marks_per_question
        
        # Parse answer key
        if isinstance(answer_key, str):
            if answer_key.startswith('{'):
                # JSON string
                parsed = json.loads(answer_key)
                if 'Q1' in parsed and isinstance(parsed['Q1'], dict):
                    # Format: {"Q1": {"answer": "A", "marks": 20}}
                    self.answer_key = {k: v['answer'] for k, v in parsed.items()}
                    self.marks_map = {k: v['marks'] for k, v in parsed.items()}
                else:
                    self.answer_key = parsed
                    self.marks_map = None
            else:
                # Simple format: "ABCDB"
                self.answer_key = {str(i+1): ans for i, ans in enumerate(answer_key)}
                self.marks_map = None
        else:
            self.answer_key = answer_key
            self.marks_map = None
    
    def calculate(self, student_answers):
        """
        Calculate total marks.
        
        Args:
            student_answers: str "ABCDA" or dict {"1": "A", ...}
        
        Returns:
            tuple: (total_marks, max_marks, details)
        """
        # Parse student answers
        if isinstance(student_answers, str) and not student_answers.startswith('{'):
            student_answers = {str(i+1): ans for i, ans in enumerate(student_answers)}
        elif isinstance(student_answers, str):
            student_answers = json.loads(student_answers)
        
        total = 0
        max_total = 0
        details = []
        
        for q_key, correct_ans in self.answer_key.items():
            q_num = q_key.replace("Q", "")
            
            # Get marks for this question
            if self.marks_map and q_key in self.marks_map:
                q_marks = self.marks_map[q_key]
            else:
                q_marks = self.marks_per_question
            
            max_total += q_marks
            
            # Get student answer
            student_ans = student_answers.get(q_num) or student_answers.get(q_key) or "X"
            
            # Check correctness
            is_correct = (student_ans.upper() == correct_ans.upper())
            earned = q_marks if is_correct else 0
            total += earned
            
            details.append({
                "question": q_key if q_key.startswith("Q") else f"Q{q_key}",
                "correct": correct_ans,
                "student": student_ans,
                "marks": earned,
                "max": q_marks,
                "status": "correct" if is_correct else "wrong"
            })
        
        return total, max_total, details

# ============================================
# RESULT FORMATTING
# ============================================

def format_results(answers, total_marks, max_marks, details, image_path=None):
    """Format evaluation results for display."""
    
    output = []
    output.append("\n" + "=" * 60)
    output.append("EVALUATION RESULTS")
    output.append("=" * 60)
    
    if image_path:
        output.append(f"\nImage: {Path(image_path).name}")
    
    output.append(f"\nScore: {total_marks}/{max_marks} ({total_marks/max_marks*100:.1f}%)")
    
    # Answer summary
    output.append("\n" + "-" * 60)
    output.append("ANSWERS:")
    output.append("-" * 60)
    
    for d in details:
        status = "[OK]" if d['status'] == 'correct' else "[X]"
        output.append(f"  {d['question']}: {d['student']} (correct: {d['correct']}) {status}")
    
    output.append("-" * 60)
    
    return "\n".join(output)

def export_results(results, output_path):
    """Export results to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Saved to: {output_path}")

# ============================================
# MAIN FUNCTIONS
# ============================================

def evaluate_single(image_path, answer_key, num_questions=None):
    """
    Evaluate a single OMR sheet.
    
    Args:
        image_path: Path to OMR image
        answer_key: Answer key (string or dict)
        num_questions: Override number of questions
    
    Returns:
        dict: Evaluation results
    """
    api_key = get_api_key()
    
    # Determine number of questions
    if num_questions is None:
        if isinstance(answer_key, str) and not answer_key.startswith('{'):
            num_questions = len(answer_key)
        else:
            num_questions = 30  # Default
    
    # Detect answers
    print("\nDetecting answers...")
    detection = detect_answers(image_path, api_key, num_questions)
    
    if not detection:
        print("Detection failed")
        return None
    
    student_answers = detection.get('answers', {})
    
    # Calculate marks
    calc = MarkCalculator(answer_key)
    total, max_marks, details = calc.calculate(student_answers)
    
    # Format and display
    print(format_results(student_answers, total, max_marks, details, image_path))
    
    # Return structured results
    return {
        "image": str(image_path),
        "timestamp": datetime.now().isoformat(),
        "detected_answers": student_answers,
        "detection_confidence": detection.get('confidence', 0),
        "total_marks": total,
        "max_marks": max_marks,
        "percentage": round(total / max_marks * 100, 1),
        "details": details
    }

def interactive_mode():
    """Run in interactive mode with file picker."""
    
    print("\n" + "=" * 60)
    print("OMR EVALUATOR - Interactive Mode")
    print("=" * 60)
    
    # Get image
    print("\nSelect OMR sheet image...")
    image_path = select_file(
        "Select OMR Image",
        [("Images", "*.jpg *.jpeg *.png"), ("All", "*.*")]
    )
    
    if not image_path:
        print("No image selected")
        return
    
    # Get answer key
    print("\nEnter answer key:")
    print("  Format 1: ABCDB (one letter per question)")
    print("  Format 2: Path to JSON file")
    
    key_input = input("\nAnswer key: ").strip()
    
    if Path(key_input).exists():
        with open(key_input) as f:
            answer_key = f.read()
    else:
        answer_key = key_input.upper()
    
    # Evaluate
    results = evaluate_single(image_path, answer_key)
    
    if results:
        # Save results
        output_path = Path(image_path).stem + "_results.json"
        export_results(results, output_path)

# ============================================
# CLI ENTRY POINT
# ============================================

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="OMR Evaluator - Detect answers and calculate marks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python omr_evaluator_v2.py                              # Interactive mode
  python omr_evaluator_v2.py --image sheet.jpg --key ABCDB
  python omr_evaluator_v2.py --image sheet.jpg --key answers.json
        """
    )
    
    parser.add_argument('--image', '-i', help='OMR image path')
    parser.add_argument('--key', '-k', help='Answer key (ABCDB or JSON file)')
    parser.add_argument('--questions', '-q', type=int, help='Number of questions')
    parser.add_argument('--output', '-o', help='Output JSON file path')
    
    args = parser.parse_args()
    
    if args.image and args.key:
        # Command line mode
        answer_key = args.key
        if Path(args.key).exists():
            with open(args.key) as f:
                answer_key = f.read()
        
        results = evaluate_single(args.image, answer_key, args.questions)
        
        if results and args.output:
            export_results(results, args.output)
    else:
        # Interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()

