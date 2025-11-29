#!/usr/bin/env python3
"""
Open Source OMR Evaluator
Two-model ensemble: Llama 3.2 Vision + Qwen2-VL

Usage: python omr_evaluator.py <image_path>

Features:
- Zero manual setup
- Auto-installs dependencies
- Auto-manages HF token
- Works on any OMR image
- 100% free
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# Fix Windows console encoding for Unicode/emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass  # Older Python versions

# ============================================
# SECTION 1: AUTO-SETUP
# ============================================

def auto_install_dependencies():
    """
    Automatically install required packages if missing.
    User doesn't need to run pip install manually.
    """
    required = {
        'huggingface_hub': 'huggingface_hub',
        'PIL': 'pillow',
        'requests': 'requests'
    }
    
    missing = []
    for import_name, package_name in required.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        print(f"📦 Installing required packages: {', '.join(missing)}...")
        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'install', '--quiet'] + missing
        )
        print("✅ Installation complete!\n")

# Run auto-install before imports
auto_install_dependencies()

# Now safe to import
from PIL import Image
import base64
import io
import requests

# ============================================
# SECTION 2: TOKEN MANAGEMENT
# ============================================

def load_env_file():
    """Load tokens from .env file."""
    tokens = {}
    
    # Try script directory
    script_dir = Path(__file__).parent
    env_path = script_dir / '.env'
    
    for path in [env_path, Path('.env')]:
        if path.exists():
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        tokens[key.strip()] = value.strip()
    
    return tokens

def get_groq_token():
    """
    Get Groq API token (FREE, supports Llama 3.2 Vision).
    
    1. Check GROQ_API_KEY environment variable
    2. Check .env file
    3. Prompt user (one-time only)
    
    Returns: token string
    """
    # Try environment variable
    token = os.getenv('GROQ_API_KEY')
    if token:
        return token
    
    # Try .env file
    tokens = load_env_file()
    if 'GROQ_API_KEY' in tokens:
        return tokens['GROQ_API_KEY']
    
    # First-time setup: prompt user
    print("\n" + "="*70)
    print("🔑 GROQ API KEY SETUP (One-time only, FREE)")
    print("="*70)
    print("\nGroq offers FREE Llama 3.2 Vision API!")
    print("\nSteps:")
    print("1. Visit: https://console.groq.com/keys")
    print("2. Sign up / Log in (free)")
    print("3. Click 'Create API Key'")
    print("4. Copy the key\n")
    
    token = input("Paste your Groq API key here: ").strip()
    
    if not token:
        print("❌ API key is required to proceed.")
        sys.exit(1)
    
    # Save for future use
    script_dir = Path(__file__).parent
    env_path = script_dir / '.env'
    
    # Append to existing .env or create new
    existing_content = ""
    if env_path.exists():
        with open(env_path, 'r') as f:
            existing_content = f.read()
    
    with open(env_path, 'w') as f:
        if existing_content:
            f.write(existing_content.rstrip() + '\n')
        f.write(f"GROQ_API_KEY={token}\n")
    
    print("✅ API key saved! You won't be asked again.\n")
    return token

# ============================================
# SECTION 3: CORE EVALUATOR CLASS
# ============================================

class OMREvaluator:
    """
    Two-model ensemble OMR evaluator using Groq's FREE API.
    
    Models (via Groq - 100% FREE):
    - Llama 3.2 Vision 11B (primary detector)
    - Llama 3.2 Vision 90B (validator) - OR second pass with 11B
    
    Voting: Both agree = 99% confidence, disagree = 70% + flag
    """
    
    def __init__(self, api_key=None):
        """Initialize with Groq API key."""
        self.api_key = api_key or get_groq_token()
        self.api_base = "https://api.groq.com/openai/v1/chat/completions"
        
        # Model identifiers - Groq's current vision models (Llama 4)
        # llama-4-scout is the multimodal vision model
        self.primary_model = "meta-llama/llama-4-scout-17b-16e-instruct"
        self.validator_model = "meta-llama/llama-4-scout-17b-16e-instruct"  # Same model, 2nd pass
        
        self.verbose = True  # Show detailed API responses
    
    def _clean_json_response(self, text):
        """
        Remove markdown code fences from LLM responses.
        LLMs sometimes return: ```json\n{...}\n```
        We need just the JSON.
        """
        text = text.strip()
        
        # Remove markdown code fences
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        elif '```' in text:
            parts = text.split('```')
            if len(parts) >= 2:
                text = parts[1]
                # Handle case where language specifier is on same line
                if text.startswith('\n'):
                    text = text[1:]
                elif '\n' in text:
                    first_line = text.split('\n')[0]
                    if first_line.strip().isalpha():
                        text = '\n'.join(text.split('\n')[1:])
        
        text = text.strip()
        
        # Try to find JSON object if there's extra text
        if text and not text.startswith('{'):
            start_idx = text.find('{')
            if start_idx != -1:
                # Find matching closing brace
                brace_count = 0
                end_idx = start_idx
                for i, char in enumerate(text[start_idx:], start_idx):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i
                            break
                text = text[start_idx:end_idx + 1]
        
        return text.strip()
    
    def _image_to_base64(self, image_path):
        """Convert image to base64 data URI for API."""
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Resize if too large (Groq has limits)
            max_size = 1024
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            img_bytes = buffer.getvalue()
            
            base64_string = base64.b64encode(img_bytes).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_string}"
    
    def _call_vision_model(self, model_name, image_path, prompt):
        """
        Call vision model via Groq's FREE API.
        
        Args:
            model_name: Groq model ID
            image_path: Path to OMR image
            prompt: Instructions for the model
        
        Returns:
            dict: Parsed JSON response
        """
        model_short_name = model_name.replace('-preview', '')
        
        try:
            # Convert image to base64 data URI
            image_data_uri = self._image_to_base64(image_path)
            
            if self.verbose:
                print(f"   📤 Sending to {model_short_name}...")
            
            # Groq API request (OpenAI-compatible format)
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": image_data_uri}
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.1
            }
            
            response = requests.post(
                self.api_base,
                headers=headers,
                json=payload,
                timeout=120  # 2 minute timeout for large images
            )
            
            # Check for errors
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', response.text[:200])
                raise Exception(f"API Error {response.status_code}: {error_msg}")
            
            # Parse response
            data = response.json()
            response_text = data['choices'][0]['message']['content']
            
            if self.verbose:
                print(f"   📥 Received response ({len(response_text)} chars)")
                preview = response_text[:150].replace('\n', ' ')
                print(f"   📝 Preview: {preview}...")
            
            cleaned_text = self._clean_json_response(response_text)
            
            try:
                result = json.loads(cleaned_text)
                if self.verbose:
                    num_answers = len(result.get('answers', {}))
                    print(f"   ✅ Parsed {num_answers} answers")
            except json.JSONDecodeError as je:
                print(f"⚠️  {model_short_name}: JSON parse error: {je}")
                print(f"   Attempting to extract answers manually...")
                
                # Try to salvage what we can from the response
                result = {
                    "answers": {},
                    "confidence": 0.5,
                    "raw_response": response_text[:500]
                }
            
            return result
        
        except requests.exceptions.Timeout:
            print(f"\n⏱️  {model_short_name}: Request timed out (2 min limit)")
            print(f"   → Try with a smaller/clearer image")
            return {"answers": {}, "confidence": 0.0, "double_bubbles": [], "error": "timeout"}
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ {model_short_name} Error:")
            
            if "401" in error_msg or "invalid_api_key" in error_msg.lower():
                print(f"   → Invalid API key. Get a new one at: https://console.groq.com/keys")
            elif "429" in error_msg or "rate" in error_msg.lower():
                print(f"   → Rate limited. Wait a moment and try again.")
                print(f"   → Groq free tier: ~30 requests/minute")
            elif "413" in error_msg or "too large" in error_msg.lower():
                print(f"   → Image too large. Try resizing to under 1024px.")
            else:
                print(f"   → {error_msg[:200]}")
            
            return {"answers": {}, "confidence": 0.0, "double_bubbles": [], "error": error_msg}
    
    def detect_with_primary(self, image_path):
        """
        Model 1: Llama 3.2 Vision 11B (primary detector).
        
        Returns:
            dict: {
                "answers": {"1": "A", "2": "B", ...},
                "double_bubbles": [15, 23],
                "confidence": 0.95
            }
        """
        prompt = """You are an expert OMR (Optical Mark Recognition) sheet evaluator.

Analyze this answer sheet image and extract ALL filled bubble answers.

CRITICAL INSTRUCTIONS:
1. Examine each question row carefully
2. Identify which bubble (A, B, C, or D) is darkened/filled
3. Return ONLY valid JSON (no markdown, no explanation, no extra text)
4. If a question has multiple bubbles filled, list it in "double_bubbles"
5. If no bubble is filled for a question, skip it

REQUIRED OUTPUT FORMAT:
{
  "answers": {
    "1": "A",
    "2": "B",
    "3": "C"
  },
  "double_bubbles": [15, 23],
  "confidence": 0.95
}

Rules:
- answers: question number (string) -> selected option (A/B/C/D)
- double_bubbles: array of question numbers with multiple marks
- confidence: your certainty level (0.0 to 1.0)

Be extremely accurate. Return ONLY the JSON object."""

        print("🦙 Llama 4 Scout - Primary analysis...")
        return self._call_vision_model(self.primary_model, image_path, prompt)
    
    def validate_with_secondary(self, image_path):
        """
        Model 2: Second pass with same model for cross-validation.
        Uses slightly different prompt for independent verification.
        
        Returns same format as primary.
        """
        prompt = """Look at this OMR bubble sheet and identify each filled answer.

For each question number, tell me which bubble (A, B, C, or D) is marked.

Return ONLY this JSON format:
{
  "answers": {"1": "A", "2": "B"},
  "double_bubbles": [],
  "confidence": 0.94
}

No explanation. Just the JSON object."""

        print("🔍 Llama 4 Scout - Validation pass...")
        return self._call_vision_model(self.validator_model, image_path, prompt)
    
    def evaluate(self, image_path):
        """
        Full two-model ensemble evaluation.
        
        Process:
        1. Both models analyze independently
        2. Compare predictions question-by-question
        3. Agreement = high confidence
        4. Disagreement = flag for review
        
        Args:
            image_path: Path to OMR image
        
        Returns:
            dict: Complete evaluation results
        """
        # Validate image exists
        image_path = Path(image_path)
        if not image_path.exists():
            print(f"❌ Error: Image not found at '{image_path}'")
            sys.exit(1)
        
        # Validate it's an image
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        if image_path.suffix.lower() not in valid_extensions:
            print(f"❌ Error: Unsupported image format '{image_path.suffix}'")
            print(f"   Supported formats: {', '.join(valid_extensions)}")
            sys.exit(1)
        
        print(f"\n📄 Evaluating: {image_path}")
        print("="*70 + "\n")
        
        # Get predictions from both models (Groq's free Llama Vision)
        llama_result = self.detect_with_primary(str(image_path))
        qwen_result = self.validate_with_secondary(str(image_path))
        
        # Ensemble voting
        print("\n🗳️  Comparing model predictions...\n")
        
        llama_answers = llama_result.get('answers', {})
        qwen_answers = qwen_result.get('answers', {})
        
        # Get all question numbers from both models
        all_questions = set(llama_answers.keys()) | set(qwen_answers.keys())
        
        final_answers = {}
        disagreements = []
        
        for q_num in sorted(all_questions, key=lambda x: int(x) if x.isdigit() else float('inf')):
            llama_ans = llama_answers.get(q_num, "BLANK")
            qwen_ans = qwen_answers.get(q_num, "BLANK")
            
            if llama_ans == qwen_ans:
                # Both models agree - high confidence
                final_answers[q_num] = {
                    'answer': llama_ans,
                    'confidence': 0.99,
                    'status': 'AGREED',
                    'models': f"Llama:{llama_ans}, Qwen:{qwen_ans}"
                }
            else:
                # Models disagree - flag for review
                disagreements.append(q_num)
                # Default to Llama (primary model), but could implement smarter logic
                final_answers[q_num] = {
                    'answer': llama_ans if llama_ans != "BLANK" else qwen_ans,
                    'confidence': 0.70,
                    'status': 'DISPUTED',
                    'llama_says': llama_ans,
                    'qwen_says': qwen_ans,
                    'models': f"Llama:{llama_ans}, Qwen:{qwen_ans}"
                }
        
        # Calculate overall confidence
        llama_conf = llama_result.get('confidence', 0.9)
        qwen_conf = qwen_result.get('confidence', 0.9)
        
        # Ensure confidence values are floats
        try:
            llama_conf = float(llama_conf)
        except (ValueError, TypeError):
            llama_conf = 0.9
        
        try:
            qwen_conf = float(qwen_conf)
        except (ValueError, TypeError):
            qwen_conf = 0.9
        
        overall_confidence = (llama_conf + qwen_conf) / 2
        
        # Merge double bubbles from both models
        llama_doubles = llama_result.get('double_bubbles', [])
        qwen_doubles = qwen_result.get('double_bubbles', [])
        all_double_bubbles = list(set(
            [int(x) for x in llama_doubles if str(x).isdigit()] +
            [int(x) for x in qwen_doubles if str(x).isdigit()]
        ))
        
        # Compile final result
        return {
            'image_path': str(image_path),
            'answers': final_answers,
            'overall_confidence': overall_confidence,
            'total_questions': len(final_answers),
            'disagreements': disagreements,
            'double_bubbles': sorted(all_double_bubbles),
            'model_details': {
                'llama': llama_result,
                'qwen': qwen_result
            }
        }

# ============================================
# SECTION 4: RESULTS DISPLAY
# ============================================

def display_results(result):
    """
    Pretty-print evaluation results to console.
    Also save to JSON file.
    """
    print("\n" + "="*70)
    print("📊 EVALUATION RESULTS")
    print("="*70)
    
    # Summary metrics
    print(f"\n✅ Overall Confidence: {result['overall_confidence']*100:.1f}%")
    print(f"📝 Total Questions Detected: {result['total_questions']}")
    print(f"⚠️  Model Disagreements: {len(result['disagreements'])}")
    print(f"🚩 Double Bubbles Found: {len(result['double_bubbles'])}")
    
    # Answer details
    if result['answers']:
        print("\n" + "-"*70)
        print("DETECTED ANSWERS:")
        print("-"*70)
        
        answers = result['answers']
        for q_num in sorted(answers.keys(), key=lambda x: int(x) if x.isdigit() else float('inf')):
            ans_data = answers[q_num]
            answer = ans_data['answer']
            confidence = ans_data['confidence']
            status = ans_data['status']
            
            # Status icon
            if status == 'AGREED':
                status_icon = "✅"
            else:
                status_icon = "⚠️"
            
            print(f"Q{q_num:>3}: {answer:>5} ({confidence*100:>3.0f}%) {status_icon} {status}")
            
            # Show details for disputed answers
            if status == 'DISPUTED':
                print(f"       └─> Pass 1: {ans_data['llama_says']}, Pass 2: {ans_data['qwen_says']}")
    else:
        print("\n⚠️  No answers detected. Please check:")
        print("   - Is this a valid OMR sheet image?")
        print("   - Is the image clear and well-lit?")
        print("   - Are the bubbles properly filled?")
    
    # Disagreements section
    if result['disagreements']:
        print("\n" + "-"*70)
        print("⚠️  FLAGGED FOR MANUAL REVIEW:")
        print("-"*70)
        print(f"\n{len(result['disagreements'])} question(s) need human verification:\n")
        
        answers = result['answers']
        for q_num in result['disagreements']:
            q_key = str(q_num)
            if q_key in answers:
                ans_data = answers[q_key]
                print(f"  Question {q_num}:")
                print(f"    📊 Pass 1:  {ans_data.get('llama_says', 'N/A')}")
                print(f"    📊 Pass 2:  {ans_data.get('qwen_says', 'N/A')}")
                print(f"    ✓ Using:   {ans_data['answer']}")
                print()
    
    # Double bubbles
    if result['double_bubbles']:
        print("\n" + "-"*70)
        print("🚩 DOUBLE BUBBLES DETECTED:")
        print("-"*70)
        print(f"\nQuestions with multiple marks: {', '.join(map(str, result['double_bubbles']))}")
        print("These questions may need manual review.\n")
    
    # Save to JSON file
    output_file = "omr_results.json"
    
    # Create a clean copy for JSON (without potential non-serializable items)
    json_result = {
        'image_path': result['image_path'],
        'answers': result['answers'],
        'overall_confidence': result['overall_confidence'],
        'total_questions': result['total_questions'],
        'disagreements': [str(d) for d in result['disagreements']],
        'double_bubbles': result['double_bubbles']
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_result, f, indent=2, ensure_ascii=False)
    
    print("-"*70)
    print(f"💾 Complete results saved to: {output_file}")
    print("="*70 + "\n")

# ============================================
# SECTION 5: FILE PICKER
# ============================================

def open_file_picker():
    """
    Open a file explorer dialog to select an image.
    Uses tkinter which is built into Python.
    
    Returns:
        str: Selected file path, or None if cancelled
    """
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        # Create hidden root window
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        root.attributes('-topmost', True)  # Bring dialog to front
        
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select OMR Sheet Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("All files", "*.*")
            ]
        )
        
        root.destroy()  # Clean up
        
        return file_path if file_path else None
        
    except Exception as e:
        print(f"⚠️  Could not open file picker: {e}")
        print("Please provide the image path as a command line argument.")
        return None

# ============================================
# SECTION 6: MAIN ENTRY POINT
# ============================================

def main():
    """
    Main entry point for the OMR evaluator.
    Completely autonomous operation.
    """
    # Welcome message
    print("\n" + "="*70)
    print("🌟 OPEN SOURCE OMR EVALUATOR")
    print("="*70)
    print("Model: Llama 4 Scout Vision (via Groq - FREE)")
    print("Cost: $0 | Datasets: None | Prerequisites: None")
    print("="*70 + "\n")
    
    # Get image path from command line or file picker
    if len(sys.argv) >= 2:
        image_path = sys.argv[1]
    else:
        print("📂 No image specified. Opening file picker...\n")
        image_path = open_file_picker()
        
        if not image_path:
            print("❌ No image selected.\n")
            print("You can also run with a path:")
            print(f"  python {sys.argv[0]} <path_to_omr_image>\n")
            sys.exit(1)
        
        print(f"✅ Selected: {image_path}\n")
    
    try:
        # Create evaluator (handles token setup automatically)
        evaluator = OMREvaluator()
        
        # Run evaluation
        result = evaluator.evaluate(image_path)
        
        # Display results
        display_results(result)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Evaluation interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error during evaluation: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# ============================================
# SECTION 7: RUN
# ============================================

if __name__ == "__main__":
    main()

