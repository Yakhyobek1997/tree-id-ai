# 🌳 Daraxt Taniqlash Tizimi / Tree Recognition System

AI yordamida daraxtlarni tanib olish va kuzatish tizimi. Deep learning texnologiyasi yordamida daraxtlarni rasm orqali tanish va vaqt bo'yicha o'zgarishlarini kuzatish.

Tree recognition and monitoring system using AI. Identify trees from images using deep learning and track changes over time.

## 📁 Loyiha Strukturasi / Project Structure

```
tree-recognition-system/
├── backend/                 # Python Flask backend
│   ├── models/             # ML modellar
│   ├── database/           # Ma'lumotlar bazasi
│   ├── api/                # REST API endpoints
│   ├── utils/              # Utility funksiyalar
│   ├── main.py             # Asosiy kirish nuqtasi
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # React komponentlar
│   │   ├── pages/         # Sahifalar
│   │   └── services/      # API xizmatlari
│   └── package.json       # Node dependencies
├── data/                   # Ma'lumotlar
│   ├── models/            # Pre-trained modellar
│   ├── uploads/           # Yuklangan rasmlar
│   └── database/          # SQLite/PostgreSQL
└── notebooks/             # Training uchun notebooklar
```

## 🚀 O'rnatish / Installation

### Backend O'rnatish

1. Virtual environment yaratish:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# yoki
venv\Scripts\activate     # Windows
```

2. Dependencies o'rnatish:
```bash
pip install -r requirements.txt
```

3. Environment variables sozlash (ixtiyoriy):
```bash
# .env fayl yaratish
DB_TYPE=sqlite
DB_CONNECTION_STRING=data/database/trees.db
API_HOST=0.0.0.0
API_PORT=5000
DEBUG=True
```

4. Backendni ishga tushirish:
```bash
python main.py
```

Backend `http://localhost:5000` da ishga tushadi.

### Frontend O'rnatish

1. Dependencies o'rnatish:
```bash
cd frontend
npm install
```

2. Environment variables (ixtiyoriy):
```bash
# .env fayl yaratish
VITE_API_URL=http://localhost:5000/api
```

3. Development serverni ishga tushirish:
```bash
npm run dev
```

Frontend `http://localhost:3000` da ochiladi.

4. Production build:
```bash
npm run build
```

## 📖 Foydalanish / Usage

### API Endpoints

#### Tree Registration
```
POST /api/register-tree
Body: multipart/form-data
  - image: (required) Tree image
  - tree_type: (optional) Type of tree
  - location_lat: (optional) Latitude
  - location_lng: (optional) Longitude
  - location_address: (optional) Address
```

#### Tree Identification
```
POST /api/identify-tree
Body: multipart/form-data
  - image: (required) Tree image to identify
```

#### Get All Trees
```
GET /api/trees?limit=100&offset=0
```

#### Get Tree Details
```
GET /api/trees/<tree_id>?include_observations=true
```

#### Add Observation
```
POST /api/trees/<tree_id>/observations
Body: multipart/form-data
  - image: (required) Observation image
  - health_status: (optional)
  - growth_stage: (optional)
  - notes: (optional)
```

#### Get Observations
```
GET /api/trees/<tree_id>/observations?limit=100
```

### Frontend Pages

- `/` - Bosh sahifa / Home page
- `/register` - Yangi daraxt qo'shish / Register new tree
- `/identify` - Daraxtni tanish / Identify tree
- `/trees` - Daraxtlar ro'yxati / Tree list
- `/trees/:treeId` - Daraxt tafsilotlari / Tree details

## 🔧 Konfiguratsiya / Configuration

### Backend Settings

`backend/utils/config.py` faylida quyidagi sozlamalarni o'zgartirish mumkin:

- `DB_TYPE`: `sqlite` yoki `postgresql`
- `SIMILARITY_THRESHOLD`: Tanishish uchun minimal o'xshashlik (0.75)
- `DUPLICATE_THRESHOLD`: Duplikat aniqlash uchun threshold (0.85)
- `MAX_UPLOAD_SIZE`: Maksimal rasm hajmi (10MB)

### Database

SQLite (default) yoki PostgreSQL ishlatish mumkin.

PostgreSQL uchun:
```bash
DB_TYPE=postgresql
DB_CONNECTION_STRING=postgresql://user:password@localhost:5432/trees
```

Schema avtomatik yaratiladi.

## 🤖 Machine Learning

Sistema ResNet50 modelidan foydalanadi feature extraction uchun.

### Training

Training uchun `notebooks/` papkasida Jupyter notebooklar yaratish mumkin.

### Model Paths

- Feature Extractor: `data/models/feature_extractor.h5`
- Tree Classifier: `data/models/tree_classifier.h5`

## 📊 Xususiyatlar / Features

- ✅ AI yordamida daraxt taniqlash
- ✅ Rasm orqali tez tanish
- ✅ Vaqt bo'yicha kuzatish
- ✅ Duplikat aniqlash
- ✅ Ma'lumotlar bazasida saqlash
- ✅ REST API
- ✅ Modern React frontend
- ✅ Responsive dizayn

## 🛠️ Texnologiyalar / Technologies

### Backend
- Python 3.8+
- Flask
- TensorFlow/Keras
- SQLite/PostgreSQL
- OpenCV
- NumPy, SciPy

### Frontend
- React 18
- Vite
- Axios
- React Router

## 📝 License

MIT License

## 👥 Muallif / Author

Tree Recognition System

## 🤝 Yordam / Support

Muammo bo'lsa issue oching yoki pull request yuboring.
