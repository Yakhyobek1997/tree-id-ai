# MongoDB Integration - Complete Guide

Bu qo'llanma Tree Recognition System da MongoDB integratsiyasi haqida to'liq ma'lumot beradi.

## 📋 Mundarija

1. [O'rnatish](#ornatish)
2. [Konfiguratsiya](#konfiguratsiya)
3. [Ishlatish](#ishlatish)
4. [Migratsiya](#migratsiya)
5. [Test qilish](#test-qilish)
6. [API Reference](#api-reference)

---

## 🚀 O'rnatish

### 1. MongoDB Driver

```bash
cd backend
pip install pymongo dnspython
```

Yoki:

```bash
pip install -r requirements.txt
```

### 2. MongoDB Server

#### Windows:
```bash
# MongoDB Community Server ni yuklab oling
# https://www.mongodb.com/try/download/community

# Service ni ishga tushirish
net start MongoDB
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod  # Auto-start
```

#### macOS:
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

#### Docker:
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 3. Schema yaratish

```bash
# MongoDB shell (mongosh) orqali
mongosh tree_recognition < backend/database/schema_mongodb.js

# Yoki Python orqali (automatic)
python -c "from backend.database.db_manager import DatabaseManager; db = DatabaseManager('mongodb'); print('Schema created')"
```

---

## ⚙️ Konfiguratsiya

### Option 1: Kod orqali

```python
from backend.database.db_manager import DatabaseManager

# Local MongoDB
db = DatabaseManager(
    db_type='mongodb',
    connection_string='mongodb://localhost:27017/',
    database_name='tree_recognition'
)
```

### Option 2: MongoConfig yordamida

```python
from backend.utils.mongo_config import MongoConfig

# Local
config = MongoConfig.for_local()
db = config.get_database_manager()

# MongoDB Atlas (Cloud)
config = MongoConfig.for_atlas(
    cluster_url='cluster0.xxxxx.mongodb.net',
    username='your_username',
    password='your_password'
)
db = config.get_database_manager()
```

### Option 3: Environment Variables

`.env` faylini yarating:

```env
DB_TYPE=mongodb
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DATABASE=tree_recognition

# Yoki MongoDB Atlas uchun:
# MONGO_CONNECTION_STRING=mongodb+srv://user:pass@cluster.mongodb.net/tree_recognition
```

Kodda:

```python
import os
from dotenv import load_dotenv
from backend.database.db_manager import DatabaseManager

load_dotenv()
db = DatabaseManager(
    db_type=os.getenv('DB_TYPE', 'mongodb'),
    connection_string=os.getenv('MONGO_CONNECTION_STRING', 'mongodb://localhost:27017/'),
    database_name=os.getenv('MONGO_DATABASE', 'tree_recognition')
)
```

---

## 💻 Ishlatish

### Asosiy Operatsiyalar

```python
from backend.database.db_manager import DatabaseManager
import numpy as np

# Database yaratish
db = DatabaseManager(db_type='mongodb')

# 1. Daraxt qo'shish
tree_id = 'tree-001'
features = np.random.rand(256)

db.add_tree(
    tree_id=tree_id,
    tree_type='Terak',
    location_lat=41.311151,
    location_lng=69.279737,
    location_address='Toshkent, O\'zbekiston',
    features=features,
    image_path='images/tree-001.jpg',
    metadata={'age': 10, 'height': 15.5}
)

# 2. Daraxtni olish
tree = db.get_tree(tree_id)
print(f"Tree: {tree['tree_type']}, Location: {tree['location_address']}")

# 3. Features olish
features = db.get_tree_features(tree_id)
print(f"Features shape: {features.shape}")

# 4. Barcha daraxtlar
trees = db.get_all_trees(limit=100)
print(f"Total trees: {len(trees)}")

# 5. Daraxtlar + Features (matching uchun)
trees_with_features = db.get_all_trees_with_features()
for tree in trees_with_features:
    print(f"{tree['tree_id']}: {tree['features'].shape}")

# 6. Observation qo'shish
db.add_observation(
    tree_id=tree_id,
    features=np.random.rand(256),
    health_status='healthy',
    growth_stage='mature',
    notes='Seasonal observation'
)

# 7. Observations olish
observations = db.get_observations(tree_id)
print(f"Total observations: {len(observations)}")

# 8. Daraxtni o'chirish
db.delete_tree(tree_id)

# Database ni yopish
db.close()
```

### Context Manager bilan

```python
with DatabaseManager(db_type='mongodb') as db:
    trees = db.get_all_trees()
    print(f"Found {len(trees)} trees")
# Automatic close
```

---

## 🔄 Migratsiya (SQLite → MongoDB)

### CLI orqali

```bash
# Asosiy migratsiya
python backend/database/migrate_to_mongodb.py

# Custom parametrlar bilan
python backend/database/migrate_to_mongodb.py \
    --sqlite-path data/database/trees.db \
    --mongo-host localhost \
    --mongo-port 27017 \
    --mongo-database tree_recognition \
    --verify

# MongoDB Atlas ga migratsiya
python backend/database/migrate_to_mongodb.py \
    --mongo-connection "mongodb+srv://user:pass@cluster.mongodb.net/" \
    --verify

# Test uchun (faqat 10 ta daraxt)
python backend/database/migrate_to_mongodb.py --limit 10 --verify
```

### Python orqali

```python
from backend.database.migrate_to_mongodb import DatabaseMigration

# Migratsiya
migration = DatabaseMigration(
    sqlite_path='data/database/trees.db',
    mongo_connection='mongodb://localhost:27017/',
    mongo_database='tree_recognition'
)

# Migrate
migration.migrate_trees()
migration.migrate_observations()
migration.verify_migration()
migration.print_summary()
migration.close()
```

---

## ✅ Test qilish

### Barcha testlarni ishga tushirish

```bash
python backend/database/test_mongodb.py
```

### Test natijalari:

```
=======================================================
                  MONGODB TEST SUITE
=======================================================

Test 1: MongoDB Connection
✅ MongoDB connection successful!

Test 2: Add Tree
✅ Tree added successfully: test-tree-20241126120530

Test 3: Get Tree
✅ Tree retrieved successfully!
   Tree ID: test-tree-20241126120530
   Type: Terak
   Location: (41.311151, 69.279737)
   Metadata: {'age': 10, 'height': 15.5, 'test': True}

... (more tests)

=======================================================
                    TEST SUMMARY
=======================================================
Total Tests:  9
Passed:       9 ✅
Failed:       0 
Success Rate: 100.0%
=======================================================
```

---

## 📚 API Reference

### DatabaseManager

```python
class DatabaseManager:
    def __init__(
        self,
        db_type: str = 'sqlite',
        connection_string: str = None,
        database_name: str = 'tree_recognition'
    )
```

#### Methods:

**add_tree(tree_id, tree_type, location_lat, location_lng, location_address, features, image_path, metadata) → bool**
- Daraxt qo'shish

**get_tree(tree_id) → Dict**
- Daraxt ma'lumotlarini olish

**get_tree_features(tree_id) → np.ndarray**
- Daraxt features ini olish

**get_all_trees(limit, offset) → List[Dict]**
- Barcha daraxtlarni olish (pagination)

**get_all_trees_with_features() → List[Dict]**
- Daraxtlar + features (matching uchun optimallashtirilgan)

**add_observation(tree_id, features, image_path, health_status, growth_stage, notes) → bool**
- Observation qo'shish

**get_observations(tree_id, limit) → List[Dict]**
- Observations olish

**delete_tree(tree_id) → bool**
- Daraxtni o'chirish

**close()**
- Connection ni yopish

### MongoConfig

```python
class MongoConfig:
    @classmethod
    def for_local(cls, database=None) → MongoConfig
    
    @classmethod
    def for_atlas(cls, cluster_url, username, password, database=None) → MongoConfig
    
    @classmethod
    def from_env(cls) → MongoConfig
    
    def get_database_manager(self) → DatabaseManager
```

---

## 🔧 Troubleshooting

### MongoDB server ishlamayapti

```bash
# Status tekshirish
# Linux:
sudo systemctl status mongod

# Windows:
net start MongoDB

# macOS:
brew services list
```

### Connection error

```python
# Timeout ni oshirish
from pymongo import MongoClient
client = MongoClient(
    'mongodb://localhost:27017/',
    serverSelectionTimeoutMS=5000
)
```

### Performance

```python
# Indexlar yaratilganligini tekshirish
db = DatabaseManager(db_type='mongodb')
indexes = db.db.trees.index_information()
print(indexes)
```

---

## 📊 Collections Structure

### trees
```javascript
{
  _id: ObjectId,
  tree_id: String (unique),
  tree_type: String,
  tree_species: String,
  location_lat: Double,
  location_lng: Double,
  location_address: String,
  metadata: Object,
  registered_date: Date,
  last_updated: Date,
  status: String (enum: active, inactive, removed)
}
```

### tree_features
```javascript
{
  _id: ObjectId,
  tree_id: String,
  features: Array[Number],
  image_path: String,
  extraction_date: Date
}
```

### tree_images
```javascript
{
  _id: ObjectId,
  tree_id: String,
  image_path: String,
  image_type: String (enum: registration, observation, analysis),
  uploaded_date: Date
}
```

### tree_observations
```javascript
{
  _id: ObjectId,
  tree_id: String,
  features: Array[Number],
  image_path: String,
  health_status: String,
  growth_stage: String,
  notes: String,
  observation_date: Date
}
```

---

## 🎯 Best Practices

1. **Connection Management**
   ```python
   # Context manager ishlatish
   with DatabaseManager(db_type='mongodb') as db:
       # operations
       pass
   ```

2. **Batch Operations**
   ```python
   # Ko'p daraxtlarni birga olish
   trees = db.get_all_trees_with_features()  # Optimized aggregation
   ```

3. **Error Handling**
   ```python
   try:
       db.add_tree(...)
   except Exception as e:
       print(f"Error: {e}")
       # Handle error
   ```

4. **Environment Variables**
   - Parollarni kodga yozmaslik
   - `.env` fayl ishlatish
   - Production da secret management

---

## 🌟 Afzalliklari

### MongoDB vs SQLite

| Feature | MongoDB | SQLite |
|---------|---------|--------|
| Scalability | ✅ Horizontal | ❌ Single file |
| Performance (large data) | ✅ Excellent | ⚠️ Good |
| Replication | ✅ Yes | ❌ No |
| Aggregation | ✅ Powerful | ⚠️ Limited |
| Schema | ✅ Flexible | ❌ Fixed |
| Cloud hosting | ✅ Atlas | ❌ No |
| Setup complexity | ⚠️ Medium | ✅ Easy |
| Development | ⚠️ Good | ✅ Excellent |

**Qachon MongoDB?**
- Production environment
- Katta hajm (10,000+ daraxtlar)
- Multiple servers
- Cloud deployment
- Replication kerak

**Qachon SQLite?**
- Development
- Prototip
- Kichik hajm
- Single server
- Simple deployment

---

## 📞 Support

Savollar uchun:
- GitHub Issues
- Documentation: `backend/database/MONGODB_CONFIG.md`
- Test examples: `backend/database/test_mongodb.py`

---

## ✨ Yangi Features

MongoDB integratsiyasi qo'shildi:
- ✅ Full CRUD operations
- ✅ Optimized aggregation queries
- ✅ Geospatial indexing ready
- ✅ Migration tools
- ✅ Comprehensive tests
- ✅ Multiple configuration options

**Barcha 3 database (SQLite, PostgreSQL, MongoDB) bir xil API bilan ishlaydi!**


