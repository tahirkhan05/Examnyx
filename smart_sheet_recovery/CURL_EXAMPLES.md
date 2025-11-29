# Smart Sheet Recovery - cURL Test Examples

## 1. Health Check

```bash
curl http://localhost:8000/health
```

---

## 2. List Available Models

```bash
curl http://localhost:8000/models
```

---

## 3. Reconstruct Sheet (Base64)

```bash
# Encode image to base64
IMAGE_BASE64=$(base64 -w 0 damaged_sheet.png)

# Send reconstruction request
curl -X POST http://localhost:8000/reconstruct \
  -H "Content-Type: application/json" \
  -d "{
    \"image_base64\": \"$IMAGE_BASE64\",
    \"expected_rows\": 50,
    \"expected_cols\": 5
  }" | jq '.'
```

---

## 4. Reconstruct Sheet (File Upload)

```bash
curl -X POST http://localhost:8000/reconstruct/upload \
  -F "file=@damaged_sheet.png" \
  -F "expected_rows=50" \
  -F "expected_cols=5" | jq '.'
```

---

## 5. Extract Bubbles (Base64)

```bash
# Using reconstructed image from previous step
RECONSTRUCTED_IMAGE="<base64_from_reconstruction_result>"

curl -X POST http://localhost:8000/extract-bubbles \
  -H "Content-Type: application/json" \
  -d "{
    \"image_base64\": \"$RECONSTRUCTED_IMAGE\",
    \"config\": \"default\",
    \"use_ai\": true
  }" | jq '.'
```

---

## 6. Extract Bubbles (File Upload)

```bash
curl -X POST http://localhost:8000/extract-bubbles/upload \
  -F "file=@omr_sheet.png" \
  -F "config=default" \
  -F "use_ai=true" | jq '.'
```

---

## 7. Detect Damage

```bash
curl -X POST http://localhost:8000/detect-damage \
  -F "file=@damaged_sheet.png" | jq '.'
```

---

## 8. Demo Reconstruction (🎯 HACKATHON DEMO)

```bash
IMAGE_BASE64=$(base64 -w 0 heavily_damaged_sheet.png)

curl -X POST http://localhost:8000/demo/reconstruct \
  -H "Content-Type: application/json" \
  -d "{
    \"image_base64\": \"$IMAGE_BASE64\",
    \"damage_description\": \"Coffee-stained sheet with torn corner and crumples\"
  }" | jq '.' > demo_result.json

# View results
cat demo_result.json | jq '.comparison'
```

---

## 9. Demo Reconstruction (File Upload)

```bash
curl -X POST "http://localhost:8000/demo/reconstruct/upload?damage_description=Coffee+stained+with+fold+marks" \
  -F "file=@damaged_sheet.png" | jq '.'
```

---

## 10. Save Reconstructed Images

```bash
# Get reconstruction result
curl -X POST http://localhost:8000/reconstruct/upload \
  -F "file=@damaged_sheet.png" \
  -o reconstruction_result.json

# Extract and save reconstructed image
cat reconstruction_result.json | jq -r '.reconstructed_image' | base64 -d > reconstructed.png

# Extract and save confidence map
cat reconstruction_result.json | jq -r '.confidence_map' | base64 -d > confidence_map.png
```

---

## 11. Test with Different Models

### Using Amazon Nova Pro

```bash
curl -X POST http://localhost:8000/reconstruct/upload \
  -F "file=@damaged_sheet.png" \
  -F "model_id=amazon.nova-pro-v1:0" | jq '.'
```

### Using Llama 3.1 Vision

```bash
curl -X POST http://localhost:8000/reconstruct/upload \
  -F "file=@damaged_sheet.png" \
  -F "model_id=meta.llama3-2-90b-instruct-v1:0" | jq '.'
```

---

## 12. Complete Pipeline Test

```bash
#!/bin/bash

echo "🎯 Smart Sheet Recovery - Complete Pipeline Test"
echo "================================================"

# Step 1: Detect damage
echo -e "\n1️⃣ Detecting damage..."
curl -s -X POST http://localhost:8000/detect-damage \
  -F "file=@damaged_sheet.png" \
  | jq '.merged_damages | {total: .total_count, severe: .severe_count, recoverable: .is_recoverable}'

# Step 2: Reconstruct sheet
echo -e "\n2️⃣ Reconstructing sheet..."
RECON_RESULT=$(curl -s -X POST http://localhost:8000/reconstruct/upload \
  -F "file=@damaged_sheet.png")

echo $RECON_RESULT | jq '.success'

# Step 3: Extract bubbles
echo -e "\n3️⃣ Extracting bubbles..."
RECONSTRUCTED_IMAGE=$(echo $RECON_RESULT | jq -r '.reconstructed_image')
echo "{\"image_base64\": \"$RECONSTRUCTED_IMAGE\", \"use_ai\": true}" > temp_request.json

curl -s -X POST http://localhost:8000/extract-bubbles \
  -H "Content-Type: application/json" \
  -d @temp_request.json \
  | jq '.results | {total: .total_questions, confident: .confident_answers, ambiguous: .ambiguous_answers}'

rm temp_request.json

echo -e "\n✅ Pipeline complete!"
```

---

## Windows PowerShell Versions

### Reconstruct Sheet (PowerShell)

```powershell
# Load image and convert to base64
$imageBytes = [System.IO.File]::ReadAllBytes("damaged_sheet.png")
$imageBase64 = [Convert]::ToBase64String($imageBytes)

# Create request body
$body = @{
    image_base64 = $imageBase64
    expected_rows = 50
    expected_cols = 5
} | ConvertTo-Json

# Send request
$response = Invoke-RestMethod -Uri "http://localhost:8000/reconstruct" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

# View result
$response | ConvertTo-Json -Depth 10
```

### Extract Bubbles (PowerShell)

```powershell
$imageBytes = [System.IO.File]::ReadAllBytes("omr_sheet.png")
$imageBase64 = [Convert]::ToBase64String($imageBytes)

$body = @{
    image_base64 = $imageBase64
    config = "default"
    use_ai = $true
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/extract-bubbles" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

# Show first 10 answers
$response.results.answers | Select-Object -First 10 | Format-Table
```

### Demo Mode (PowerShell)

```powershell
$imageBytes = [System.IO.File]::ReadAllBytes("damaged_sheet.png")
$imageBase64 = [Convert]::ToBase64String($imageBytes)

$body = @{
    image_base64 = $imageBase64
    damage_description = "Coffee-stained with torn corner"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/demo/reconstruct" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

# Show comparison
$response.comparison | Format-List

# Save reconstructed image
$reconstructedBytes = [Convert]::FromBase64String($response.after.reconstructed_image)
[System.IO.File]::WriteAllBytes("reconstructed.png", $reconstructedBytes)

Write-Host "✅ Reconstructed image saved to reconstructed.png"
```

---

## Notes

- Replace `damaged_sheet.png` with your actual image path
- Install `jq` for JSON parsing: `sudo apt install jq` (Linux) or `brew install jq` (Mac)
- For Windows PowerShell, use the PowerShell versions above
- All endpoints return JSON responses
- Check API docs at `http://localhost:8000/docs` for interactive testing
