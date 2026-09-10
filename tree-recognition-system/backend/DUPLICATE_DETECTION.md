# Duplicate Detection (Takroriy Daraxtlarni Aniqlash)

## 📌 Muammo

Daraxt bazaga qo'shilganda, agar u allaqachon mavjud bo'lsa, qayta qo'shilmasligi kerak. Duplicate detection bu muammoni hal qiladi.

## ✅ Yechim

### 1. **Avtomatik Tekshirish**

Daraxt ro'yxatga olinganda:
1. Rasmdan feature'lar chiqariladi
2. Bazadagi barcha daraxtlar bilan taqqoslanadi
3. Agar 80%+ o'xshashlik topilsa → **OGOHLIK**
4. Agar o'xshashlik past → yangi daraxt sifatida qo'shiladi

### 2. **Threshold Sozlamalari**

`.env` faylida:

```env
# Duplicate detection threshold
DUPLICATE_THRESHOLD=0.80  # 80% similarity = duplicate

# Identification threshold  
SIMILARITY_THRESHOLD=0.75  # 75% similarity = match

# High confidence threshold
HIGH_CONFIDENCE_THRESHOLD=0.85  # 85%+ = high confidence
```

**Threshold tushunchasi:**
- `0.80` = 80% o'xshashlik
- Agar ikkita rasm 80%+ o'xshash bo'lsa → bu bir xil daraxt
- Past qiymat (masalan, 0.70) → ko'proq duplicate topadi
- Yuqori qiymat (masalan, 0.90) → kamroq duplicate topadi

### 3. **Response Format**

#### A. Duplicate Topilsa:

```json
{
  "status": "exists",
  "tree_id": "abc-123-def",
  "similarity": 0.85,
  "message": "⚠️ Bu daraxt allaqachon bazada mavjud! (O'xshashlik: 85%)",
  "warning": "Bu daraxt avval ro'yxatdan o'tgan",
  "tree_data": {
    "tree_id": "abc-123-def",
    "tree_type": "Terak",
    "location_address": "Toshkent",
    "registered_date": "2024-11-26T10:00:00"
  }
}
```

#### B. Yangi Daraxt (Duplicate Yo'q):

```json
{
  "success": true,
  "status": "registered",
  "tree_id": "new-456-xyz",
  "tree_type": "Terak",
  "message": "Daraxt muvaffaqiyatli ro'yxatga olindi!",
  "similarity": 1.0
}
```

---

## 🔧 Debug Mode

Backend ishga tushganda terminalda ko'rinadi:

```
🔍 Checking for duplicates...
📊 Found 3 trees in database
  🔎 Checking 3 trees for duplicates (threshold: 80%)
    Tree 1 (abc-123-d...): similarity = 45%
    Tree 2 (def-456-a...): similarity = 87%
    ✅ DUPLICATE FOUND! Similarity: 87%
⚠️  DUPLICATE FOUND: def-456-a... (similarity: 87%)
```

---

## 🎯 Threshold Sozlash

### Scenario 1: Ko'p False Positive (xato duplicate)

**Muammo:** Har xil daraxtlar "duplicate" deb topilmoqda

**Yechim:** Threshold ni oshiring

```env
DUPLICATE_THRESHOLD=0.85  # 80 → 85
```

### Scenario 2: Duplicate Aniqlanmayapti

**Muammo:** Bir xil daraxt qayta qo'shilmoqda

**Yechim:** Threshold ni pasaytiring

```env
DUPLICATE_THRESHOLD=0.75  # 80 → 75
```

### Scenario 3: Optimal (Tavsiya etiladi)

```env
DUPLICATE_THRESHOLD=0.80  # ✅ Yaxshi balans
SIMILARITY_THRESHOLD=0.75  # ✅ Identification uchun
HIGH_CONFIDENCE_THRESHOLD=0.85  # ✅ Yuqori ishonch
```

---

## 🧪 Test Qilish

### 1. Bir xil rasmni ikki marta yuklash

```bash
curl -X POST http://localhost:5000/api/register-tree \
  -F "image=@tree1.jpg" \
  -F "tree_type=Terak"
```

**1-marta:** ✅ Registered
**2-marta:** ⚠️ Duplicate detected

### 2. Bir xil daraxtni har xil burchakdan

```bash
# Oldingi burchak
curl -X POST http://localhost:5000/api/register-tree \
  -F "image=@tree_front.jpg"

# Orqa tomoni
curl -X POST http://localhost:5000/api/register-tree \
  -F "image=@tree_back.jpg"
```

**Natija:** Agar 80%+ o'xshash → duplicate

---

## 📊 Feature Extraction

Duplicate detection feature extraction ga bog'liq:

### Simple Mode (Default):
- Color histogram
- Texture features  
- Shape features
- **Yaxshi:** Tez, yengil
- **Yomon:** Kam aniq

### Advanced Mode:
- Deep learning features
- Rotation invariant
- Multi-scale
- **Yaxshi:** Juda aniq
- **Yomon:** Sekin, ko'p resurs kerak

`.env` da:

```env
FEATURE_EXTRACTION_METHOD=simple  # yoki advanced
```

---

## 🚨 Xato Bartaraf Qilish

### 1. Duplicate aniqlanmayapti

**Tekshirish:**

```python
from backend.database.db_manager import DatabaseManager

db = DatabaseManager(db_type='mongodb')
trees = db.get_all_trees_with_features()
print(f"Trees with features: {len(trees)}")

for tree in trees:
    print(f"  {tree['tree_id']}: features shape = {tree.get('features').shape if tree.get('features') is not None else 'None'}")
```

**Sabab:** Features saqlanmagan

### 2. Barcha daraxtlar duplicate

**Tekshirish:** Threshold juda past

```env
DUPLICATE_THRESHOLD=0.85  # Oshiring
```

### 3. Feature shape mismatch

**Xato:** `Shape mismatch (256,) vs (512,)`

**Yechim:** Feature extractor method bir xil bo'lishi kerak

---

## 💡 Best Practices

1. **Threshold Tuning:**
   - Development: `0.80` (balansli)
   - Production: `0.82-0.85` (kam false positive)

2. **Feature Quality:**
   - Yaxshi yorug'lik
   - Aniq rasm (blur bo'lmasin)
   - To'liq daraxt ko'rinsin

3. **Database Maintenance:**
   - Vaqti-vaqti bilan duplicate tekshirish
   - Eski/noto'g'ri yozuvlarni tozalash

4. **User Experience:**
   - Duplicate topilganda aniq xabar ko'rsatish
   - Qaysi daraxt bilan match bo'lganini ko'rsatish
   - Override option (admin uchun)

---

## 🎓 Qo'shimcha Ma'lumot

### O'xshashlik Hisoblash

```python
similarity = 1 - cosine_distance(features1, features2)
```

- `1.0` = 100% o'xshash (bir xil)
- `0.8` = 80% o'xshash
- `0.5` = 50% o'xshash
- `0.0` = 0% o'xshash (mutlaqo boshqa)

### Recommended Thresholds

| Use Case | Threshold | Izoh |
|----------|-----------|------|
| Duplicate Detection | 0.80 | Bir xil daraxt |
| Same Tree (different time) | 0.75 | Temporal tracking |
| Same Species | 0.60 | Bir xil tur |
| Similar Features | 0.50 | O'xshash |

---

Savol bo'lsa:
- Terminalda debug log'larni kuzating
- Threshold'larni sozlang
- Feature extraction method'ni tekshiring

Muvaffaqiyatli duplicate detection! 🎯


