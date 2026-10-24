# SmartRoute UZ — Navigation

Foydalanuvchi jo‘nash va yetib borish manzillarini qidiradi, yo‘l variantlarini solishtiradi, xarita va batafsil ko‘rsatmalarni ko‘radi, yoqilg‘i sarfi/xarajatini hisoblaydi.

## Windows / PowerShell
```powershell
cd D:\SmartRoute_UZ_Pro
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Data providers
- Geocoding: OpenStreetMap Nominatim
- Road routes: OSRM public demo server

Internet talab qilinadi. Ochiq demo xizmatlarida foydalanish limiti va uzilishlar bo‘lishi mumkin. Hozirgi OSRM demo avtomobil profili truck-specific restrictions (balandlik, vazn, o‘q yuki, taqiqlar)ni kafolatli hisobga olmaydi. Truck tijoriy foydalanishi uchun truck-aware routing provayderi bilan integratsiya zarur. Masofa/vaqt real vaqt tirbandligini hisobga olmaydi.
