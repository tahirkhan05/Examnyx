# AWS Bedrock Prompt Templates
# Collection of prompts used for OMR reconstruction

## 1. Sheet Reconstruction Prompt

**Purpose:** Analyze damaged OMR sheet and reconstruct missing/damaged regions

**Prompt:**
```
You are an expert in OMR (Optical Mark Recognition) sheet analysis and reconstruction.

You are analyzing a damaged OMR answer sheet that may have:
- Torn edges or missing corners
- Coffee stains or water damage
- Crumpled or folded areas
- Smudged bubble regions
- Missing or partially obscured bubbles

Your task:
1. Identify the OMR grid structure (rows and columns of bubbles)
2. Detect which bubble positions are damaged, obscured, or missing
3. Infer the expected grid pattern based on visible intact bubbles
4. Reconstruct missing bubble outlines based on geometric pattern
5. Predict bubble positions even in damaged regions

Provide a JSON response with:
{
  "grid_structure": {
    "rows": <number>,
    "cols": <number>,
    "bubble_diameter": <pixels>
  },
  "damaged_regions": [
    {
      "area": "top-left|top-right|center|bottom",
      "damage_type": "torn|stained|crumpled|smudged|missing",
      "severity": 0.0-1.0,
      "bbox": [x, y, width, height]
    }
  ],
  "reconstructed_bubbles": [
    {
      "row": <number>,
      "col": <number>,
      "inferred": true|false,
      "confidence": 0.0-1.0,
      "center": [x, y]
    }
  ],
  "reconstruction_notes": "<explanation of inference logic>"
}

Be precise with coordinates and conservative with confidence scores for inferred bubbles.
```

---

## 2. Grid Prediction Prompt

**Purpose:** Predict complete grid structure from partial visible bubbles

**Prompt:**
```
Analyze this damaged OMR sheet and predict the complete grid structure.

Even if parts are missing or damaged:
1. Identify visible bubble patterns
2. Calculate average bubble spacing
3. Detect grid alignment (horizontal/vertical lines)
4. Extrapolate missing bubble positions based on pattern
5. Provide geometric reconstruction of the full grid

Return JSON:
{
  "detected_bubbles": <count>,
  "grid_pattern": {
    "rows": <number>,
    "cols": <number>,
    "bubble_spacing_x": <pixels>,
    "bubble_spacing_y": <pixels>,
    "grid_offset_x": <pixels>,
    "grid_offset_y": <pixels>
  },
  "confidence": 0.0-1.0,
  "missing_bubble_positions": [
    {"row": <number>, "col": <number>, "predicted_center": [x, y]}
  ]
}
```

---

## 3. Damage Detection & Classification Prompt

**Purpose:** Identify and classify all damage types

**Prompt:**
```
Analyze this OMR sheet for ALL types of damage and quality issues.

Identify and classify:
1. **Torn edges** - Missing paper, ripped corners
2. **Stains** - Coffee, ink, water marks, discoloration
3. **Fold marks** - Creases, bent areas
4. **Smudges** - Blurred regions, rubbed areas
5. **Shadows** - Lighting artifacts, dark areas
6. **Missing corners** - Cut or torn corner regions
7. **Crumpled areas** - Wrinkled, distorted paper
8. **Water damage** - Wet spots, paper warping

For EACH damage instance, provide:
- Exact type
- Severity (minor/moderate/severe)
- Precise bounding box [x, y, width, height]
- Whether it affects bubble regions
- Estimated number of affected bubbles

Return JSON:
{
  "damages": [
    {
      "type": "torn|stain|fold|smudge|shadow|missing_corner|crumpled|water_damage",
      "severity": "minor|moderate|severe",
      "location_description": "top-left corner|center area|etc",
      "bbox": [x, y, width, height],
      "affects_bubbles": true|false,
      "affected_bubble_count": <number>,
      "confidence": 0.0-1.0
    }
  ],
  "overall_quality_score": 0.0-1.0,
  "is_recoverable": true|false,
  "recovery_difficulty": "easy|medium|hard|impossible"
}
```

---

## 4. Bubble Extraction Prompt

**Purpose:** Extract marked bubble answers with confidence

**Prompt:**
```
Analyze this OMR answer sheet and extract all bubble markings.

For each question row:
1. Identify which bubble (A, B, C, D, E) is marked/filled
2. Provide confidence score for each detection
3. Flag ambiguous or unclear markings
4. Handle partially obscured bubbles

The sheet may have:
- Incomplete bubble fills
- Smudged markings
- Multiple marks (erasures)
- Faint or light markings

Return JSON format:
{
  "answers": [
    {
      "question_number": <number>,
      "selected_option": "A|B|C|D|E|NONE|MULTIPLE",
      "confidence": 0.0-1.0,
      "is_ambiguous": true|false,
      "fill_intensity": 0.0-1.0,
      "notes": "<any issues>"
    }
  ],
  "total_questions": <number>,
  "confident_answers": <number>,
  "ambiguous_answers": <number>
}

Be conservative - mark low confidence when uncertain.
```

---

## 5. Bubble Validation Prompt

**Purpose:** Cross-validate detected bubbles

**Prompt:**
```
Validate these bubble detections from a reconstructed OMR sheet.

Detected bubbles: {bubbles}

Cross-check:
1. Are bubbles correctly positioned in grid?
2. Are fill intensities reasonable?
3. Are there any detection errors?
4. Should any ambiguous marks be resolved?

Return JSON with validated results and corrections.
```

---

## 6. Missing Bubble Inference Prompt

**Purpose:** Infer bubble positions in damaged regions

**Prompt:**
```
Given these damaged regions: {damaged_regions}

Infer the most likely bubble positions in these damaged areas based on:
1. Visible bubble pattern in intact regions
2. Grid spacing and alignment
3. Geometric extrapolation

Provide inferred bubble centers with confidence scores.
```

---

## Prompt Engineering Tips

### For Best Results with Claude 3.5 Sonnet:

1. **Be Specific:** Provide exact JSON schema expected
2. **Use Examples:** Show format in prompt
3. **Request Reasoning:** Ask for "notes" or "explanation" fields
4. **Conservative Confidence:** Instruct model to be conservative with scores
5. **Low Temperature:** Use 0.1-0.3 for consistent structured output
6. **Context:** Explain the OMR domain and constraints

### Temperature Settings:

- **Reconstruction:** 0.2 (balanced between creativity and precision)
- **Grid Prediction:** 0.1 (very precise geometric calculations)
- **Damage Detection:** 0.2 (slight flexibility for edge cases)
- **Bubble Extraction:** 0.1 (maximum consistency)
- **Validation:** 0.15 (slight flexibility for corrections)

### Model-Specific Notes:

**Claude 3.5 Sonnet:**
- Excellent at spatial reasoning
- Handles complex JSON schemas well
- Good at explaining inference logic
- Best for grid reconstruction

**Amazon Nova Pro:**
- Faster inference
- Good for simple damage detection
- May need simpler prompts

**Llama 3.1 Vision:**
- Requires more explicit instructions
- Better with shorter prompts
- May need examples in prompt

---

## Example API Call with Prompt

```python
from bedrock_client import get_bedrock_client

client = get_bedrock_client()

# Load your custom prompt
custom_prompt = """
Analyze this OMR sheet and identify all marked bubbles.
Return a JSON array of {question: number, answer: "A|B|C|D|E"}
"""

# Send to Bedrock
result = client.run_bedrock_vision(
    prompt=custom_prompt,
    image_bytes=image_data,
    temperature=0.1
)

print(result['text'])
```

---

## Prompt Versioning

**Version 1.0** - Initial release
- Basic reconstruction
- Simple damage detection

**Version 1.1** - Enhanced (Current)
- Detailed damage classification
- Confidence scoring
- Multi-type damage support
- Recovery difficulty estimation

---

## Contributing New Prompts

When adding new prompts:
1. Document the purpose clearly
2. Specify expected input/output format
3. Include temperature recommendations
4. Test with multiple models
5. Add examples of good responses
