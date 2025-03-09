import sqlite3

# Data to be inserted into the database
data = [
    {"id": 1, "number": "01.02.04", "name": "Deformatsiyalanuvchan qattiq jism mexanikasi"},
    {"id": 2, "number": "05.01.03", "name": "Informatikaning nazariy asoslari"},
    {"id": 3, "number": "05.01.11", "name": "Raqamli texnologiyalar va sun'iy intelekt"},
    {"id": 4, "number": "05.09.06", "name": "Gidrotexnika va melioratsiya qurilishi"},
    {"id": 5, "number": "05.09.07", "name": "Gidravlika va muhandislik gidrologiyasi"},
    {"id": 6, "number": "05.10.01", "name": "Mehnatni muxofaza qilish va inson faoliyati xavfsizligi"},
    {"id": 7, "number": "06.01.02", "name": "Melioratsiya va sug‘orma dehkonchilik"},
    {"id": 8, "number": "06.01.10", "name": "Yer tuzish, kadastr va yer monitoringi (iqtisodiyot fanlari)"},
    {"id": 9, "number": "07.00.01", "name": "O‘zbekiston tarixi"},
    {"id": 10, "number": "08.00.04", "name": "Qishloq xoʻjaligi iqtisodiyoti"},
    {"id": 11, "number": "08.00.08", "name": "Buxgalteriya hisobi, audit va iqtisodiy tahlil"},
    {"id": 12, "number": "09.00.04", "name": "Ijtimoiy falsafa"},
    {"id": 13, "number": "11.00.07", "name": "Geoinformatika"},
    {"id": 14, "number": "11.00.05", "name": "Atrof muhitni muhofaza qilish va tabiiy resurslardan oqilona foydalanish"},
    {"id": 15, "number": "13.00.02", "name": "Ta’lim va tarbiya nazariyasi va metodikasi"},
    {"id": 16, "number": "05.01.04", "name": "Hisoblash mashinalari, majmualari va kompyuter tarmoqlarining matematik va dasturiy ta'minoti"},
    {"id": 17, "number": "05.01.08", "name": "Texnologik jarayonlar va ishlab chiqarishni avtomatlashtirish va boshqarish"},
    {"id": 18, "number": "05.07.01", "name": "Qishloq xo‘jaligi va melioratsiya mashinalari. Qishloq xo’jaligi va melioratsiya ishlarini mexanizatsiyalash"},
    {"id": 19, "number": "05.05.07", "name": "Qishloq xo‘jaligida elektr texnologiyalar va elektr uskunalar"},
    {"id": 20, "number": "05.05.06", "name": "Qayta tiklanadigan energiya turlari asosidagi energiya qurilmalari"},
    {"id": 21, "number": "05.01.01", "name": "Muhandislik geometriyasi va kompyuter grafikasi. Audio va video texnologiyalari"}
]

# Connect to SQLite database (creates the file if it doesn't exist)
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Create table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS web_nexteducationmajor (
        id INTEGER PRIMARY KEY,
        number TEXT NOT NULL,
        name TEXT NOT NULL
    )
''')

# Insert data into the table; using INSERT OR REPLACE to avoid duplicate primary key errors
for item in data:
    cursor.execute('''
        INSERT OR REPLACE INTO web_nexteducationmajor (id, number, name)
        VALUES (?, ?, ?)
    ''', (item['id'], item['number'], item['name']))

conn.commit()
conn.close()

print("Data inserted successfully!")
