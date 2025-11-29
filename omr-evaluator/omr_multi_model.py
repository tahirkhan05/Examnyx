#!/usr/bin/env python3
"""
OMR Multi-Model Evaluator
=========================

Uses MULTIPLE AI providers for true cross-validation:
1. Groq (Llama 4 Scout) - Primary
2. OpenRouter (Free models) - Validator
3. Together AI (Free tier) - Third opinion

This gives REAL cross-validation instead of same-model comparison.

Usage:
    python omr_multi_model.py image.jpg
"""

import sys
import json
import base64
import io
import os
import requests
from pathlib import Path

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except: pass

from PIL import Image

# ============================================
# API CONFIGURATIONS
# ============================================

PROVIDERS = {
    "groq": {
        "name": "Groq (Llama 4 Scout)",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "env_key": "GROQ_API_KEY",
        "signup": "https://console.groq.com/keys"
    },
    "openrouter": {
        "name": "OpenRouter (Qwen Vision)",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "qwen/qwen2.5-vl-72b-instruct:free",  # Free Qwen vision model
        "env_key": "OPENROUTER_API_KEY",
        "signup": "https://openrouter.ai/keys"
    }
}

# ============================================
# SETUP
# ============================================

def load_env():
    """Load API keys from .env file."""
    env_path = Path(__file__).parent / '.env'
    keys = {}
    
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    keys[k.strip()] = v.strip()
                    os.environ[k.strip()] = v.strip()
    
    return keys

def get_api_key(provider_id):
    """Get API key for a provider."""
    provider = PROVIDERS[provider_id]
    env_key = provider['env_key']
    
    # Check environment
    key = os.getenv(env_key)
    if key:
        return key
    
    # Prompt user
    print(f"\n{provider['name']} API key not found.")
    print(f"Get one free at: {provider['signup']}")
    key = input(f"Enter {env_key}: ").strip()
    
    if key:
        # Save to .env
        env_path = Path(__file__).parent / '.env'
        with open(env_path, 'a') as f:
            f.write(f"\n{env_key}={key}\n")
        os.environ[env_key] = key
    
    return key

# ============================================
# IMAGE PROCESSING
# ============================================

def image_to_base64(image_path):
    """Convert image to base64 data URI."""
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
        b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/jpeg;base64,{b64}"

# ============================================
# AI DETECTION
# ============================================

def detect_with_provider(provider_id, image_path, num_questions=10):
    """
    Detect answers using a specific provider.
    
    Returns:
        dict: {"answers": {...}, "confidence": 0.95, "provider": "..."}
    """
    provider = PROVIDERS[provider_id]
    api_key = get_api_key(provider_id)
    
    if not api_key:
        return {"answers": {}, "confidence": 0, "error": "No API key", "provider": provider['name']}
    
    print(f"\n🔍 {provider['name']}...")
    
    image_data = image_to_base64(image_path)
    
    prompt = f"""Analyze this OMR answer sheet. Identify which bubble (A/B/C/D) is filled for each question.

Return ONLY JSON:
{{
  "answers": {{"1": "A", "2": "B", ...}},
  "confidence": 0.95
}}

Questions: 1-{num_questions}. If blank, use "X". Return ONLY JSON."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Add extra headers for OpenRouter
    if provider_id == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/omr-evaluator"
        headers["X-Title"] = "OMR Evaluator"
    
    payload = {
        "model": provider['model'],
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_data}},
                {"type": "text", "text": prompt}
            ]
        }],
        "max_tokens": 1000,
        "temperature": 0.1
    }
    
    try:
        response = requests.post(provider['url'], headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            error = response.text[:200]
            print(f"   ❌ Error: {error}")
            return {"answers": {}, "confidence": 0, "error": error, "provider": provider['name']}
        
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
        
        result = json.loads(text)
        result['provider'] = provider['name']
        
        num_answers = len(result.get('answers', {}))
        print(f"   ✅ Detected {num_answers} answers")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {"answers": {}, "confidence": 0, "error": str(e), "provider": provider['name']}

# ============================================
# MULTI-MODEL EVALUATION
# ============================================

def evaluate_multi_model(image_path, num_questions=10):
    """
    Evaluate OMR using multiple AI models and compare.
    """
    print("\n" + "=" * 60)
    print("🎯 MULTI-MODEL OMR EVALUATION")
    print("=" * 60)
    print(f"Image: {Path(image_path).name}")
    print(f"Using {len(PROVIDERS)} different AI models for cross-validation")
    
    # Get results from each provider
    results = {}
    for provider_id in PROVIDERS:
        results[provider_id] = detect_with_provider(provider_id, image_path, num_questions)
    
    # Compare and vote
    print("\n" + "=" * 60)
    print("📊 CROSS-MODEL COMPARISON")
    print("=" * 60)
    
    # Get all question numbers
    all_questions = set()
    for r in results.values():
        all_questions.update(r.get('answers', {}).keys())
    
    final_answers = {}
    disagreements = []
    
    print(f"\n{'Q':<4}", end="")
    for pid in PROVIDERS:
        print(f"{PROVIDERS[pid]['name'][:15]:<17}", end="")
    print("FINAL")
    print("-" * 60)
    
    for q in sorted(all_questions, key=lambda x: int(x) if x.isdigit() else 0):
        answers_for_q = []
        row = f"Q{q:<3}"
        
        for pid in PROVIDERS:
            ans = results[pid].get('answers', {}).get(q, '?')
            answers_for_q.append(ans)
            row += f"{ans:<17}"
        
        # Vote: majority wins
        from collections import Counter
        vote = Counter(answers_for_q)
        winner, count = vote.most_common(1)[0]
        
        # Check agreement
        if count == len(PROVIDERS):
            status = "✅"
            confidence = 0.99
        elif count > len(PROVIDERS) / 2:
            status = "⚠️"
            confidence = 0.75
            disagreements.append(q)
        else:
            status = "❌"
            confidence = 0.50
            disagreements.append(q)
        
        row += f"{winner} {status}"
        print(row)
        
        final_answers[q] = {
            "answer": winner,
            "confidence": confidence,
            "votes": dict(vote),
            "unanimous": count == len(PROVIDERS)
        }
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 SUMMARY")
    print("=" * 60)
    
    unanimous = sum(1 for v in final_answers.values() if v['unanimous'])
    total = len(final_answers)
    
    print(f"\n✅ All models agree: {unanimous}/{total} questions")
    print(f"⚠️  Disagreements: {len(disagreements)} questions")
    
    if disagreements:
        print(f"\n   Questions needing review: {', '.join(map(str, disagreements))}")
    
    # Overall confidence
    avg_conf = sum(v['confidence'] for v in final_answers.values()) / total if total > 0 else 0
    print(f"\n📊 Overall confidence: {avg_conf*100:.1f}%")
    
    return {
        "final_answers": {q: v['answer'] for q, v in final_answers.items()},
        "detailed": final_answers,
        "disagreements": disagreements,
        "unanimous_count": unanimous,
        "total_questions": total,
        "overall_confidence": avg_conf,
        "provider_results": results
    }

# ============================================
# MAIN
# ============================================

def main():
    load_env()
    
    print("\n" + "=" * 60)
    print("🎯 MULTI-MODEL OMR EVALUATOR")
    print("=" * 60)
    print("True cross-validation using DIFFERENT AI models")
    print("=" * 60)
    
    # Get image
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
                title="Select OMR Image",
                filetypes=[("Images", "*.jpg *.jpeg *.png")]
            )
            root.destroy()
        except:
            image_path = input("Enter image path: ").strip()
    
    if not image_path or not Path(image_path).exists():
        print("❌ No valid image")
        return
    
    # Run evaluation
    results = evaluate_multi_model(image_path)
    
    # Save results
    output_path = Path(image_path).stem + "_multi_model_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {output_path}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()

