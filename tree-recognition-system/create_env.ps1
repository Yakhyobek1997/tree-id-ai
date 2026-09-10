# .env faylini yaratish uchun PowerShell skript

Write-Host "================================" -ForegroundColor Green
Write-Host ".env Faylini Yaratish" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

# Check if .env already exists
if (Test-Path ".env") {
    Write-Host "⚠️  .env fayl allaqachon mavjud!" -ForegroundColor Yellow
    $overwrite = Read-Host "Qayta yozishni xohlaysizmi? (y/n)"
    if ($overwrite -ne "y") {
        Write-Host "❌ Bekor qilindi" -ForegroundColor Red
        exit
    }
}

# Create .env file
$envContent = @"
# ===== DATABASE CONFIGURATION =====

# Database type: sqlite | postgresql | mongodb
DB_TYPE=mongodb

# ===== MongoDB Configuration =====
# Local MongoDB
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DATABASE=tree_recognition
MONGO_USERNAME=
MONGO_PASSWORD=

# MongoDB Atlas (Cloud) uchun pastdagi qatorni uncomment qiling:
# MONGO_CONNECTION_STRING=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/tree_recognition?retryWrites=true&w=majority

# ===== Flask Configuration =====
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
SECRET_KEY=tree-recognition-secret-key-2024-$(Get-Random)

# ===== File Upload Configuration =====
UPLOAD_FOLDER=data/uploads
MAX_CONTENT_LENGTH=16777216
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif

# ===== Model Configuration =====
MODEL_PATH=data/models
FEATURE_EXTRACTION_METHOD=simple

# ===== CORS Configuration =====
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# ===== Logging =====
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
"@

# Write to .env file
$envContent | Out-File -FilePath ".env" -Encoding UTF8

Write-Host "✅ .env fayl yaratildi!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Kerakli sozlamalar:" -ForegroundColor Cyan
Write-Host "  - DB_TYPE=mongodb" -ForegroundColor White
Write-Host "  - MONGO_HOST=localhost" -ForegroundColor White
Write-Host "  - MONGO_DATABASE=tree_recognition" -ForegroundColor White
Write-Host ""
Write-Host "📂 .env faylini ko'rish:" -ForegroundColor Cyan
Write-Host "  notepad .env" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Backend ni ishga tushirish:" -ForegroundColor Cyan
Write-Host "  cd backend" -ForegroundColor White
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  python main.py" -ForegroundColor White
Write-Host ""
Write-Host "================================" -ForegroundColor Green


