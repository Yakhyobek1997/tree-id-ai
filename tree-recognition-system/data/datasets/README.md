# Daraxt datasetlari

Bu papka haqiqiy rasmlar, manbalar va yorliqlarni saqlash uchun. Rasmlarni shu
yerga ko'chirish modelni avtomatik o'qitmaydi va 98% aniqlikni tasdiqlamaydi.

```text
data/datasets/
  images/
    bark/<tur>/          po'stloq va tana
    branch/<tur>/        shoxlar
    leaf/<tur>/          barglar
    whole_tree/<tur>/    umumiy ko'rinish
    disease/             tasdiqlangan kasallik rasmlari uchun (hozir bo'sh)
    roots/               ildiz rasmlari uchun (hozir bo'sh)
  manifests/             rasm yo'li, tur, qism, manba, litsenziya, SHA256
  sources/               asl dataset metadata, indeks va yuklash hisobotlari
  annotations/           mutaxassis tasdiqlari uchun
  splits/                daraxt ID bo'yicha train/validation/test ajratish
```

## Manbalar

- [Urban Street Tree](https://ytt917251944.github.io/dataset_jekyll/): barg, shox,
  tana va umumiy ko'rinish uchun muallif ko'rsatgan Kaggle datasetlari. Har bir
  to'plamning litsenziyasi `sources/urban_*/metadata.json`da saqlanadi. Boshlang'ich
  yuklash har bir sinfdan 3 ta rasm oladi; to'liq dataset emas. Asl yorliqdagi
  umumiy nom yoki genus nomi aniq ilmiy turga taxminan aylantirilmaydi.
- [BarkNet 1.0](https://zenodo.org/records/11508014): Zenodo metadata bo'yicha MIT.
  Boshlang'ich ERB, PEG va PID arxivlari to'liq olinadi; butun BarkNet emas.
  Asl fayl nomidan daraxt ID va tana aylanasi olinadi; diametr = aylana / pi.
  Muallif: Mathieu Carpentier, Philippe Giguere, Jonathan Gaudreault / Universite
  Laval. Asl README va metadata saqlanadi. Ilmiy manba: DOI 10.1109/IROS.2018.8593514.

## Yuklash va davom ettirish

`tree-recognition-system` ichidan:

```powershell
python -m backend.datasets.download_public --per-class 3
python -m backend.datasets.download_barknet
```

Ko'proq Urban Street rasmlari uchun:

```powershell
python -m backend.datasets.download_public --organs branch bark leaf whole_tree --per-class 20 --max-mb-per-organ 1000
```

Avval olingan rasmlar SHA256 bilan tekshiriladi va qayta yuklanmaydi. Asl rasmlar
saqlanadi; manifestlar yo'l, tur yorlig'i, daraxt qismi, litsenziya va manbani
birga saqlaydi. Tarmoq xatosi bo'lsa `sources/*/import_report.json`ni tekshiring.
BarkNet arxivlari muallifning MD5 qiymatiga solishtiriladi. `.part` fayl qolsa,
skript uni yashirincha almashtirmaydi; avval tugallanmagan yuklashni tekshiring.

## Model uchun tayyorlash

Kasallik va yosh yorlig'i manbada bo'lmasa `null` bo'lib qoladi. `taxon_verified`
mustaqil mutaxassis tekshiruvi bo'lmagani uchun `false`; bu manba yorlig'i yo'q
degan ma'noni bildirmaydi. Urban Street jismoniy daraxt IDlari tasdiqlanmagan.
Asl `source_split` saqlanadi, lekin ishchi `split` hali `unassigned`.

1. Maqsadli hudud va daraxt turlarini tanlang; tur nomlarini mutaxassis tekshirsin.
2. Bir daraxtning barcha rasmlariga bir xil ID bering. Turli fasl va rakurslar
   ham shu guruhda qoladi. O'xshash/takroriy rasmlarni tekshiring.
3. Butun daraxt guruhlarini train, validation, test qismlariga ajrating.
   Tasodifiy rasm bo'yicha bo'lish aniqlikni sun'iy oshirishi mumkin.
4. Shu ma'lumot bilan lokal modelni o'qiting; validationda parametrlarni tanlang.
5. Mutaxassis belgilagan mustaqil testda tur/kasallik aniqligini alohida o'lchang.

Bu ma'lumotlar diagnostika provideriga avtomatik yuborilmaydi va platformaning
tayyor AI modeliga avtomatik qo'shilmaydi. Hozirgi integratsiya va baholash yo'li
uchun [ANALYSIS.md](../../ANALYSIS.md)ga qarang.
