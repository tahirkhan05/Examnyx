# Frontend-Backend Integration Guide

## Overview
This guide covers the integration between the ExamNyx frontend (React + Vite) and backend (FastAPI + Blockchain).

## Architecture

```
Frontend (React)          Backend (FastAPI)
Port: 8080               Port: 8000
     │                        │
     ├─► API Service ────────►├─► Blockchain Engine
     │                        │
     └─► State Management    └─► Database (SQLite)
```

## Setup Instructions

### 1. Backend Setup

Navigate to the blockchain_part directory and start the server:

```powershell
cd blockchain_part
python main.py
```

The backend will be available at: http://localhost:8000
API Documentation: http://localhost:8000/docs

### 2. Frontend Setup

Navigate to the frontend directory and install dependencies:

```powershell
cd frontend
npm install
npm run dev
```

The frontend will be available at: http://localhost:8080

### 3. Environment Variables

Frontend `.env` file:
```
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_ENV=development
VITE_ENABLE_BLOCKCHAIN=true
VITE_ENABLE_AI_FEATURES=true
```

## API Integration

### API Configuration (`src/lib/api.ts`)

The axios instance is configured with:
- Base URL from environment variable
- Request interceptor for auth tokens
- Response interceptor for error handling
- 30-second timeout

### API Service (`src/services/api.service.ts`)

Provides methods for all backend endpoints:

**Blockchain APIs:**
- `getBlockchainStatus()` - Get blockchain status
- `getBlockchainBlocks()` - Get all blocks
- `getBlockByHash(hash)` - Get specific block
- `validateBlockchain()` - Validate chain integrity

**OMR Operations:**
- `uploadOMRSheet(file, metadata)` - Upload OMR sheet
- `processBubbleDetection(sheetId)` - Detect bubbles
- `scoreOMRSheet(sheetId, answerKey)` - Calculate scores
- `finalizeResult(sheetId)` - Finalize results

**Student APIs:**
- `getStudentResults(studentId)` - Get all results
- `submitRecheckRequest(sheetId, reason)` - Request recheck
- `getResultByHash(blockchainHash)` - Verify result

## Component Integration Example

### Results Page with API Integration

```tsx
import { useState, useEffect } from 'react';
import apiService from '@/services/api.service';

const Results = () => {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchResults();
  }, []);

  const fetchResults = async () => {
    try {
      const response = await apiService.getStudentResults('STUDENT_001');
      if (response.success) {
        setResults(response.data);
      }
    } catch (error) {
      console.error('Error:', error);
      // Fallback to mock data
    } finally {
      setLoading(false);
    }
  };

  // ... component render
};
```

## Testing Integration

### 1. Test Backend Health

```powershell
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "blockchain": {
    "is_valid": true,
    "total_blocks": 1
  }
}
```

### 2. Test Blockchain Status

```powershell
curl http://localhost:8000/api/blockchain/status
```

### 3. Run Integration Test Script

```powershell
.\test_integration.ps1
```

## CORS Configuration

The backend is configured to allow all origins in development:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**For production**, update to specific origins:
```python
allow_origins=["https://examnyx.com"],
```

## Proxy Configuration

Vite is configured with a proxy for API requests:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

## Error Handling

### Frontend Error Handling

API errors are caught and displayed using toast notifications:

```tsx
try {
  const response = await apiService.someAPI();
} catch (error) {
  toast({
    title: 'Error',
    description: error.message,
    variant: 'destructive',
  });
}
```

### Backend Error Responses

All errors return structured JSON:

```json
{
  "success": false,
  "error": "Error message",
  "detail": "Detailed error information"
}
```

## Available Endpoints

### Blockchain
- `GET /api/blockchain/status` - Get blockchain status
- `GET /api/blockchain/blocks` - List all blocks
- `GET /api/blockchain/block/{hash}` - Get block by hash
- `GET /api/blockchain/validate` - Validate blockchain

### OMR Scanning
- `POST /api/scan/upload` - Upload OMR sheet
- `GET /api/scan/{sheet_id}` - Get sheet details

### Evaluation
- `POST /api/bubble/process/{sheet_id}` - Process bubbles
- `POST /api/score/calculate/{sheet_id}` - Calculate scores
- `POST /api/verify/submit/{sheet_id}` - Submit verification

### Results
- `GET /api/result/student/{student_id}` - Get student results
- `POST /api/result/finalize/{sheet_id}` - Finalize result
- `GET /api/result/hash/{blockchain_hash}` - Get result by hash

### Recheck
- `POST /api/recheck/request/{sheet_id}` - Request recheck
- `GET /api/recheck/requests` - List recheck requests
- `POST /api/recheck/process/{recheck_id}` - Process recheck

## Production Deployment

### Frontend Build

```powershell
npm run build
```

Output in `dist/` folder.

### Environment Variables for Production

Update `.env.production`:
```
VITE_API_BASE_URL=https://api.examnyx.com
VITE_APP_ENV=production
```

### Backend Configuration

Update `blockchain_part/app/config.py`:
- Set `ENVIRONMENT=production`
- Update CORS origins
- Configure production database
- Set secure secret keys

## Troubleshooting

### Frontend can't connect to backend

1. Check backend is running: `curl http://localhost:8000/health`
2. Check CORS configuration
3. Verify `.env` has correct `VITE_API_BASE_URL`
4. Check browser console for errors

### API returns 404

1. Verify endpoint path in `api.service.ts`
2. Check backend route definitions
3. Review FastAPI docs at `/docs`

### CORS errors

1. Ensure backend CORS middleware is configured
2. Check `allow_origins` setting
3. Verify request headers

## Next Steps

1. Implement authentication (JWT tokens)
2. Add file upload for OMR sheets
3. Integrate real-time blockchain verification
4. Add WebSocket for live updates
5. Implement comprehensive error boundaries

## Support

For issues or questions, refer to:
- Backend API Docs: http://localhost:8000/docs
- Frontend README: `frontend/README.md`
- Integration Status: `INTEGRATION_STATUS.md`
