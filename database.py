import aiosqlite
from datetime import datetime, timedelta
from config import DB_PATH

# 1. ዳታቤዙን እና ቴብሎችን ማስጀመር
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # የ users ቴብል አወቃቀር
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                start_date TEXT,
                expiry_date TEXT,
                is_vip INTEGER DEFAULT 0
            )
        ''')
        
        # የ payments ቴብል - ለ Payment Info በተን እንዲጠቅም
        await db.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                payer_name TEXT,
                phone TEXT,
                transaction_id TEXT UNIQUE,
                amount REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.commit()

# 2. አዲስ ተጠቃሚ መመዝገብ ወይም መረጃ ማዘመን
async def add_user(user_id, username, full_name, phone=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO users (user_id, username, full_name, phone)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            full_name=excluded.full_name,
            phone=COALESCE(excluded.phone, users.phone)
        ''', (user_id, username, full_name, phone))
        await db.commit()

# 3. ተጠቃሚውን VIP ማድረግ (start_date እና expiry_date እዚህ ይመዘገባሉ)
async def activate_vip(user_id, duration_type):
    # የቆይታ ጊዜ ምርጫዎች በ config.py ካሉት ጋር መመሳሰል አለባቸው
    durations = {
        "5min": timedelta(minutes=5),
        "1month": timedelta(days=30),
        "2month": timedelta(days=60),
        "3month": timedelta(days=90),
        "6month": timedelta(days=180),
        "1year": timedelta(days=365)
    }
    
    delta = durations.get(duration_type, timedelta(days=30))
    start_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    expiry_now = (datetime.now() + delta).strftime('%Y-%m-%d %H:%M:%S')
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_vip=1, start_date=?, expiry_date=? WHERE user_id=?",
            (start_now, expiry_now, user_id)
        )
        await db.commit()

# 4. ሁሉንም የ VIP ተጠቃሚዎች መረጃ ለ Date Info ማውጣት
async def get_all_vip_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row # በስም (Key) ዳታውን ለማውጣት ይረዳል
        async with db.execute("SELECT * FROM users WHERE is_vip = 1") as cursor:
            users = await cursor.fetchall()
            return [dict(row) for row in users]

# 5. ጊዜያቸው ያለቀባቸውን ተጠቃሚዎች መፈለግ
async def get_expired_users():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE is_vip = 1 AND expiry_date <= ?", (now,)) as cursor:
            users = await cursor.fetchall()
            return [dict(row) for row in users]

# 6. ተጠቃሚውን ከ VIP ማውጣት (ጊዜው ሲያልቅ)
async def deactivate_user(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_vip=0 WHERE user_id=?", (user_id,))
        await db.commit()
async def get_expired_users():
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE is_vip=1 AND expiry_date<=?", (now,)
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def get_expiring_soon_users(days: int = 1):
    from datetime import datetime, timedelta
    now    = datetime.now()
    future = (now + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    now_s  = now.strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE is_vip=1 AND expiry_date>? AND expiry_date<=?",
            (now_s, future)
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]
