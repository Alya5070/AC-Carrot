import aiosqlite
import os

# Use persistent /data directory if on Railway, otherwise fallback to local file
if os.path.exists("/data") and os.access("/data", os.W_OK):
    DB_NAME = "/data/database.sqlite"
else:
    DB_NAME = "database.sqlite"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                warned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                channel_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                message_content TEXT,
                staff_id INTEGER,
                reason TEXT
            )
        ''')
        
        # Safe migration if database already exists without message_content
        try:
            await db.execute('ALTER TABLE warnings ADD COLUMN message_content TEXT')
            await db.commit()
        except aiosqlite.OperationalError:
            pass # Column already exists

        # Safe migration if database already exists without staff_id
        try:
            await db.execute('ALTER TABLE warnings ADD COLUMN staff_id INTEGER')
            await db.commit()
        except aiosqlite.OperationalError:
            pass # Column already exists

        # Safe migration if database already exists without reason
        try:
            await db.execute('ALTER TABLE warnings ADD COLUMN reason TEXT')
            await db.commit()
        except aiosqlite.OperationalError:
            pass # Column already exists
            
        await db.execute('''
            CREATE TABLE IF NOT EXISTS paid_requests (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                budget TEXT NOT NULL,
                sfw_nsfw TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                use_case TEXT NOT NULL,
                content TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                staff_review_msg_id INTEGER,
                approved_msg_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

# --- Warning Tracker Methods ---

async def add_warning(user_id: int, channel_id: int, message_id: int, message_content: str, staff_id: int = None, reason: str = None, warned_at: str = None):
    async with aiosqlite.connect(DB_NAME) as db:
        if warned_at:
            await db.execute('''
                INSERT INTO warnings (user_id, channel_id, message_id, message_content, staff_id, reason, warned_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, channel_id, message_id, message_content, staff_id, reason, warned_at))
        else:
            await db.execute('''
                INSERT INTO warnings (user_id, channel_id, message_id, message_content, staff_id, reason)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, channel_id, message_id, message_content, staff_id, reason))
        await db.commit()

async def warning_exists(message_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('''
            SELECT 1 FROM warnings WHERE message_id = ? AND user_id = ?
        ''', (message_id, user_id))
        row = await cursor.fetchone()
        return row is not None

async def get_warnings_count_last_3_months(user_id: int) -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        # Check warnings in the last 3 months
        cursor = await db.execute('''
            SELECT COUNT(*) FROM warnings 
            WHERE user_id = ? AND warned_at >= datetime('now', '-3 months')
        ''', (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else 0

async def get_warnings_count_last_30_days(user_id: int) -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        # Check warnings in the last 30 days
        cursor = await db.execute('''
            SELECT COUNT(*) FROM warnings 
            WHERE user_id = ? AND warned_at >= datetime('now', '-30 days')
        ''', (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else 0

async def get_last_warning_staff_id_last_30_days(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('''
            SELECT staff_id FROM warnings
            WHERE user_id = ? AND staff_id IS NOT NULL AND warned_at >= datetime('now', '-30 days')
            ORDER BY warned_at DESC
            LIMIT 1
        ''', (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else None

async def get_last_warning_staff_id_last_3_months(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('''
            SELECT staff_id FROM warnings
            WHERE user_id = ? AND staff_id IS NOT NULL AND warned_at >= datetime('now', '-3 months')
            ORDER BY warned_at DESC
            LIMIT 1
        ''', (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else None

async def get_last_3_warnings(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        # Fetch the last 3 warnings within 3 months
        cursor = await db.execute('''
            SELECT message_content, warned_at FROM warnings
            WHERE user_id = ? AND warned_at >= datetime('now', '-3 months')
            ORDER BY warned_at DESC
            LIMIT 3
        ''', (user_id,))
        rows = await cursor.fetchall()
        return [(row['message_content'], row['warned_at']) for row in rows if row['message_content']]

async def get_warnings_paginated(user_id: int, limit: int, offset: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('''
            SELECT id, warned_at, channel_id, message_id, message_content, staff_id, reason FROM warnings
            WHERE user_id = ?
            ORDER BY warned_at DESC
            LIMIT ? OFFSET ?
        ''', (user_id, limit, offset))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_warnings_count(user_id: int) -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('SELECT COUNT(*) FROM warnings WHERE user_id = ?', (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else 0

async def get_warning_by_id(warning_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT * FROM warnings WHERE id = ?', (warning_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def delete_warning_by_id(warning_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('SELECT 1 FROM warnings WHERE id = ?', (warning_id,))
        exists = await cursor.fetchone()
        if not exists:
            return False
        await db.execute('DELETE FROM warnings WHERE id = ?', (warning_id,))
        await db.commit()
        return True

async def get_warnings_by_staff_paginated(staff_id: int, limit: int, offset: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('''
            SELECT id, user_id, warned_at, channel_id, message_id, message_content, reason FROM warnings
            WHERE staff_id = ?
            ORDER BY warned_at DESC
            LIMIT ? OFFSET ?
        ''', (staff_id, limit, offset))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_warnings_by_staff_count(staff_id: int) -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('SELECT COUNT(*) FROM warnings WHERE staff_id = ?', (staff_id,))
        row = await cursor.fetchone()
        return row[0] if row else 0

# --- Paid Request Methods ---

async def create_paid_request(user_id: int, budget: str, sfw_nsfw: str, payment_method: str, use_case: str, content: str) -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('''
            INSERT INTO paid_requests (user_id, budget, sfw_nsfw, payment_method, use_case, content)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, budget, sfw_nsfw, payment_method, use_case, content))
        await db.commit()
        return cursor.lastrowid

async def get_paid_request(request_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT * FROM paid_requests WHERE request_id = ?', (request_id,))
        return await cursor.fetchone()

async def update_paid_request_review_msg(request_id: int, msg_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE paid_requests SET staff_review_msg_id = ? WHERE request_id = ?', (msg_id, request_id))
        await db.commit()

async def update_paid_request_status(request_id: int, status: str, approved_msg_id: int = None):
    async with aiosqlite.connect(DB_NAME) as db:
        if approved_msg_id:
            await db.execute('UPDATE paid_requests SET status = ?, approved_msg_id = ? WHERE request_id = ?', (status, approved_msg_id, request_id))
        else:
            await db.execute('UPDATE paid_requests SET status = ? WHERE request_id = ?', (status, request_id))
        await db.commit()

async def update_paid_request_details(request_id: int, budget: str, sfw_nsfw: str, payment_method: str, use_case: str, content: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            UPDATE paid_requests 
            SET budget = ?, sfw_nsfw = ?, payment_method = ?, use_case = ?, content = ? 
            WHERE request_id = ?
        ''', (budget, sfw_nsfw, payment_method, use_case, content, request_id))
        await db.commit()

async def get_last_submitted_request(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('''
            SELECT * FROM paid_requests
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user_id,))
        return await cursor.fetchone()
