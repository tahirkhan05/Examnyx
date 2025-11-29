#!/usr/bin/env python3
"""Quick calibration test with actual OMR image."""

import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except: pass

import pandas as pd
import json
from omr_evaluator import OMREvaluator

# Paths
DATASET = r'C:\Users\DrRay\Downloads\PS1E.xlsx'
OMR_IMAGE = r'C:\Users\DrRay\Downloads\omr sheet.jpeg'

print("="*60)
print("🔬 QUICK CALIBRATION TEST")
print("="*60)

# Load dataset
df = pd.read_excel(DATASET)
print(f"\n📊 Loaded {len(df)} test cases from dataset")

# Detect answers
print(f"\n📷 Analyzing: {OMR_IMAGE}")
evaluator = OMREvaluator()
result = evaluator.evaluate(OMR_IMAGE)

# Extract detected answers
detected = {}
for q, data in result.get('answers', {}).items():
    detected[q] = data.get('answer', '?') if isinstance(data, dict) else data

print("\n" + "="*60)
print("📝 DETECTED STUDENT ANSWERS")
print("="*60)
for q in sorted(detected.keys(), key=lambda x: int(x) if x.isdigit() else 0):
    print(f"   Q{q}: {detected[q]}")

print("\n" + "="*60)
print("📊 COMPARING WITH EACH ANSWER KEY")
print("="*60 + "\n")

matches = 0
total = len(df)

for idx, row in df.iterrows():
    roll = row['Student Roll Number']
    answer_key = json.loads(row['Correct Answers Key'])
    manual = row['Extracted Marks']
    original_auto = row['Auto Calculated Marks']
    
    # Calculate our marks
    our_marks = 0
    for qk, qd in answer_key.items():
        qnum = qk.replace('Q', '')
        if detected.get(qnum) == qd['answer']:
            our_marks += qd['marks']
    
    # Check match
    if our_marks == manual:
        matches += 1
        icon = "✅"
    else:
        icon = "❌"
    
    print(f"Roll {roll}: Manual={manual:3d}, Our AI={our_marks:3d}, Orig Auto={original_auto:3d}  {icon}")

# Summary
print("\n" + "="*60)
print("📈 SUMMARY")
print("="*60)
accuracy = (matches / total) * 100
print(f"\n✅ AI matches manual: {matches}/{total} ({accuracy:.1f}%)")

# Original system accuracy
orig_matches = sum(1 for _, r in df.iterrows() if r['Marks Matched'] == 'Yes')
orig_accuracy = (orig_matches / total) * 100
print(f"📊 Original auto matches: {orig_matches}/{total} ({orig_accuracy:.1f}%)")

diff = accuracy - orig_accuracy
if diff > 0:
    print(f"\n🎉 Our AI is {diff:.1f}% BETTER!")
elif diff < 0:
    print(f"\n⚠️  Our AI is {abs(diff):.1f}% worse - needs tuning")
else:
    print(f"\n📊 Same accuracy as original")

print("\n" + "="*60 + "\n")

