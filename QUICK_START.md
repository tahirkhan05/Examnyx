# ExamNyx - Quick Start Guide

## 🚀 Starting the Application

### Option 1: Use the Startup Script (Recommended)
```powershell
.\start_all.ps1
```
This will start both backend and frontend automatically in separate windows.

### Option 2: Manual Start

**Terminal 1 - Backend:**
```powershell
cd blockchain_part
python main.py
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm run dev
```

## 🌐 Access Points

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

## 🧪 Testing Integration

Run the integration test script:
```powershell
.\test_integration.ps1
```

Or test manually:
```powershell
# Test backend
curl http://localhost:8000/health

# Test blockchain
curl http://localhost:8000/api/blockchain/status
```

## 📁 Key Files

### Frontend
- `src/lib/api.ts` - Axios configuration
- `src/services/api.service.ts` - API service functions
- `.env` - Environment variables
- `vite.config.ts` - Vite configuration with proxy

### Backend
- `main.py` - FastAPI application
- `app/config.py` - Configuration settings
- `app/api/` - API route handlers
- `app/blockchain/` - Blockchain engine

## 🔑 Environment Variables

### Frontend (.env)
```
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_ENV=development
VITE_ENABLE_BLOCKCHAIN=true
VITE_ENABLE_AI_FEATURES=true
```

### Backend (config.py)
- Database: SQLite (omr_blockchain.db)
- Port: 8000
- CORS: Enabled for all origins (development)

## 📚 Documentation

- **Integration Complete**: `INTEGRATION_COMPLETE.md`
- **Integration Guide**: `FRONTEND_BACKEND_INTEGRATION.md`
- **Architecture**: `ARCHITECTURE_VISUAL.md`
- **Executive Summary**: `EXECUTIVE_SUMMARY.md`

## ⚙️ Common Tasks

### Install Dependencies

**Frontend:**
```powershell
cd frontend
npm install
```

**Backend:**
```powershell
cd blockchain_part
pip install -r requirements.txt
```

### Build for Production

**Frontend:**
```powershell
cd frontend
npm run build
```

### Stop All Services
Close the terminal windows or press `Ctrl+C` in each terminal.

## 🔧 Troubleshooting

### Port Already in Use
```powershell
# Find process using port 8000
Get-NetTCPConnection -LocalPort 8000

# Stop Python processes
Get-Process python | Stop-Process -Force
```

### Frontend Can't Connect to Backend
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check `.env` file has correct API URL
3. Clear browser cache and reload

### API Errors
1. Check backend logs in the terminal
2. Visit API docs: http://localhost:8000/docs
3. Test endpoints with curl or Postman

## 🎯 Next Steps

1. **Login** - Navigate to http://localhost:8080
2. **Test Student Portal** - Use student login
3. **Test Admin Portal** - Use admin login
4. **View Results** - Check the results page with blockchain verification
5. **Explore API** - Visit http://localhost:8000/docs

## 💡 Features

✓ Blockchain-based result storage
✓ OMR sheet evaluation
✓ Student result verification
✓ Recheck request workflow
✓ Real-time blockchain validation
✓ Multi-signature approval system
✓ Complete audit trail

## 📞 Support

For issues or questions:
- Check the documentation files
- Review API docs at /docs endpoint
- Check browser console for errors
- Review backend terminal logs

---

**Happy Coding! 🎉**
