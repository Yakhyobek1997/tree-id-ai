# MongoDB Atlas bilan .env faylini sozlash

Write-Host "================================" -ForegroundColor Green
Write-Host "MongoDB Atlas Configuration" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

# .env content with MongoDB Atlas
$envContent = @"
# ===== DATABASE CONFIGURATION =====
DB_TYPE=mongodb

# ===== MongoDB Atlas (Cloud) =====
MONGO_CONNECTION_STRING=mongodb+srv://yahyobek19979797_db_user:IDPNxZhTlPnzNEke@cluster0.pfypwjz.mongodb.net/
MONGO_DATABASE=tree_recognition

# ===== Flask Configuration =====
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
SECRET_KEY=tree-recognition-secret-key-2024

# ===== File Upload Configuration =====
UPLOAD_FOLDER=data/uploads
MAX_CONTENT_LENGTH=16777216
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif

# ===== Model Configuration =====
MODEL_PATH=data/models
FEATURE_EXTRACTION_METHOD=simple

# ===== Similarity Thresholds =====
# Duplicate detection: 0.80 = 80% similarity triggers duplicate warning
DUPLICATE_THRESHOLD=0.80
# Tree identification: 0.75 = 75% similarity for matching
SIMILARITY_THRESHOLD=0.75
# High confidence: 0.85 = 85%+ similarity is high confidence match
HIGH_CONFIDENCE_THRESHOLD=0.85

# ===== CORS Configuration =====
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# ===== Logging =====
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
"@

# Write to .env file
$envContent | Out-File -FilePath ".env" -Encoding UTF8

Write-Host "✅ .env fayl MongoDB Atlas bilan yaratildi!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Sozlamalar:" -ForegroundColor Cyan
Write-Host "  ✓ DB_TYPE=mongodb" -ForegroundColor White
Write-Host "  ✓ MongoDB Atlas ulanish" -ForegroundColor White
Write-Host "  ✓ Database: tree_recognition" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Backend ni ishga tushirish:" -ForegroundColor Cyan
Write-Host "  cd backend" -ForegroundColor White
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  python main.py" -ForegroundColor White
Write-Host ""
Write-Host "================================" -ForegroundColor Green

