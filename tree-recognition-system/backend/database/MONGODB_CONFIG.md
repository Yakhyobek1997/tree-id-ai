# MongoDB Configuration Guide

## O'rnatish (Installation)

### 1. MongoDB Driver ni o'rnatish

```bash
cd backend
pip install pymongo dnspython
```

Yoki requirements.txt orqali:

```bash
pip install -r requirements.txt
```

### 2. MongoDB ni o'rnatish

#### Windows uchun:
1. MongoDB Community Server ni yuklab oling: https://www.mongodb.com/try/download/community
2. O'rnatib, MongoDB ni ishga tushiring:
```bash
# MongoDB service ni ishga tushirish
net start MongoDB
```

#### Linux uchun:
```bash
# Ubuntu/Debian
sudo apt-get install mongodb-org

# MongoDB ni ishga tushirish
sudo systemctl start mongod
```

#### macOS uchun:
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

### 3. MongoDB Atlas (Cloud) - Ixtiyoriy

Agar lokal MongoDB o'rniga cloud MongoDB ishlatmoqchi bo'lsangiz:
1. https://www.mongodb.com/cloud/atlas ga kiring
2. Bepul cluster yarating
3. Connection string ni oling

---

## Konfiguratsiya

### Variant 1: Python kodda

```python
from backend.database.db_manager import DatabaseManager

# Local MongoDB
db_manager = DatabaseManager(
    db_type='mongodb',
    connection_string='mongodb://localhost:27017/',
    database_name='tree_recognition'
)

# MongoDB Atlas
db_manager = DatabaseManager(
    db_type='mongodb',
    connection_string='mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/',
    database_name='tree_recognition'
)
```

### Variant 2: MongoConfig yordamida

```python
from backend.utils.mongo_config import MongoConfig

# Local MongoDB
config = MongoConfig.for_local()
db_manager = config.get_database_manager()

# MongoDB Atlas
config = MongoConfig.for_atlas(
    cluster_url='cluster0.xxxxx.mongodb.net',
    username='your_username',
    password='your_password'
)
db_manager = config.get_database_manager()
```

### Variant 3: Environment Variables

`.env` faylini yarating va quyidagilarni qo'shing:

```env
# Database type
DB_TYPE=mongodb

# Local MongoDB
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DATABASE=tree_recognition
MONGO_USERNAME=
MONGO_PASSWORD=

# Yoki MongoDB Atlas uchun:
# MONGO_CONNECTION_STRING=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/tree_recognition
```

Keyin kodda:

```python
import os
from dotenv import load_dotenv
from backend.database.db_manager import DatabaseManager

load_dotenv()

db_manager = DatabaseManager(
    db_type=os.getenv('DB_TYPE', 'mongodb'),
    connection_string=os.getenv('MONGO_CONNECTION_STRING'),
    database_name=os.getenv('MONGO_DATABASE', 'tree_recognition')
)
```

---

## Schema va Indexes ni yaratish

MongoDB shell (mongosh) orqali:

```bash
# MongoDB shell ni oching
mongosh

# Database ni tanlang
use tree_recognition

# Schema faylini bajarib chiqish
load('backend/database/schema_mongodb.js')

# Yoki to'g'ridan-to'g'ri:
mongosh tree_recognition < backend/database/schema_mongodb.js
```

---

## Test qilish

Python yordamida:

```python
from backend.database.db_manager import DatabaseManager
import numpy as np

# Database manager ni yaratish
db = DatabaseManager(
    db_type='mongodb',
    connection_string='mongodb://localhost:27017/',
    database_name='tree_recognition'
)

# Test daraxt qo'shish
tree_id = 'test-tree-001'
features = np.random.rand(256)  # Test features

success = db.add_tree(
    tree_id=tree_id,
    tree_type='Terak',
    location_lat=41.311151,
    location_lng=69.279737,
    location_address='Toshkent, O\'zbekiston',
    features=features,
    image_path='test/image.jpg',
    metadata={'age': 10, 'height': 15.5}
)

print(f"Tree qo'shildi: {success}")

# Daraxtni olish
tree = db.get_tree(tree_id)
print(f"Tree ma'lumotlari: {tree}")

# Features olish
tree_features = db.get_tree_features(tree_id)
print(f"Features: {tree_features.shape}")

# Barcha daraxtlar
trees = db.get_all_trees()
print(f"Jami daraxtlar: {len(trees)}")

# Database ni yopish
db.close()
```

---

## SQLite dan MongoDB ga migratsiya

Agar sizda mavjud SQLite database bo'lsa, quyidagi skript yordamida MongoDB ga ko'chirishingiz mumkin:

```python
from backend.database.db_manager import DatabaseManager
import numpy as np

# SQLite database
sqlite_db = DatabaseManager(db_type='sqlite', connection_string='data/database/trees.db')

# MongoDB database
mongo_db = DatabaseManager(
    db_type='mongodb',
    connection_string='mongodb://localhost:27017/',
    database_name='tree_recognition'
)

# Barcha daraxtlarni ko'chirish
trees = sqlite_db.get_all_trees(limit=10000)
print(f"Ko'chirilayotgan daraxtlar: {len(trees)}")

for tree in trees:
    tree_id = tree.get('tree_id')
    if not tree_id:
        continue
    
    # Features olish
    features = sqlite_db.get_tree_features(tree_id)
    
    # MongoDB ga qo'shish
    mongo_db.add_tree(
        tree_id=tree_id,
        tree_type=tree.get('tree_type'),
        location_lat=tree.get('location_lat'),
        location_lng=tree.get('location_lng'),
        location_address=tree.get('location_address'),
        features=features,
        metadata={}
    )
    
    print(f"Ko'chirildi: {tree_id}")

print("Migratsiya tugadi!")

# Database larni yopish
sqlite_db.close()
mongo_db.close()
```

---

## Afzalliklari

### MongoDB vs SQLite

**MongoDB afzalliklari:**
- ✅ Katta hajmdagi ma'lumotlar uchun yaxshi
- ✅ Horizontal scaling (ko'p serverlar)
- ✅ Moslashuvchan schema (JSON-like documents)
- ✅ Tez query'lar va indexlar
- ✅ Replication va high availability
- ✅ Aggregation pipeline (murakkab query'lar)

**SQLite afzalliklari:**
- ✅ O'rnatish kerak emas (embedded)
- ✅ Oddiy va yengil
- ✅ Development uchun yaxshi
- ✅ Single file database

---

## Xulosa

MongoDB integratsiyasi muvaffaqiyatli qo'shildi! 

Endi siz uchta database variantidan birini tanlashingiz mumkin:
1. **SQLite** - development uchun (default)
2. **PostgreSQL** - production uchun (SQL kerak bo'lsa)
3. **MongoDB** - production uchun (NoSQL, yuqori hajm)

Barcha 3 variant `DatabaseManager` class orqali bir xil API bilan ishlaydi.


