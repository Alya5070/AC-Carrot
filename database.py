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
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS reaction_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                emoji TEXT NOT NULL,
                role_id INTEGER NOT NULL
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS dropdown_menus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                placeholder TEXT NOT NULL,
                row_index INTEGER NOT NULL
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS dropdown_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                menu_id INTEGER NOT NULL,
                label TEXT NOT NULL,
                emoji TEXT,
                role_id INTEGER NOT NULL
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS verbal_reasons (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                text TEXT NOT NULL
            )
        ''')
        
        cursor = await db.execute("SELECT COUNT(*) FROM verbal_reasons")
        count = (await cursor.fetchone())[0]
        if count == 0:
            default_reasons = [
                ("underpricing", "Underpricing", "pricing below our server minimum of 15USD __per__ character, *or* below the server minimum of 5USD per 100 words for writing. Please refer to [Rule 2.4](https://discord.com/channels/369798142289510401/492328409175687179/1481767967103389727), and visit our [Commission Guide](https://discord.com/channels/369798142289510401/1393288825987665990/1476704977958469663) for more information.\n-# Note: Extra characters must also meet the server minimum of 15USD. Additionally, your post will be taken down if it has no specified currency, or uses one that is under the server minimum when converted."),
                ("no_visible_pricing", "Lack of visible pricing and examples", "a lack of visible pricing and/or offer examples in your post. Be it through written text or images; offer examples, TOS, and pricing per service offered __must__ be visible in your post according to [Rule 2.1](https://discord.com/channels/369798142289510401/492328409175687179/1481767967103389727).\n-# Note: Refer to our [Local Rules](https://discord.com/channels/369798142289510401/1393271200729268294/1476738956396597290) per channel for more information."),
                ("no_tos_mention", "Lack of/No mentions of ToS", "not having your Terms of Service linked or displayed properly, or indicated as to where they can be found. Refer to [Rule 2.1](https://discord.com/channels/369798142289510401/492328409175687179/1481767967103389727), read through the <#492328409175687179> before posting, and visit our [TOS Guide](https://discord.com/channels/369798142289510401/1191922480961552424/1191922480961552424) for examples on how your terms should be written.\n-# Note: If not directly displayed in your post; you __must__ state where your terms can be found, such as in a specific link or website. Buyers should not have to message you for additional information."),
                ("incomplete_tos", "Incomplete ToS", "insufficient information in your Terms of Service. Please keep in mind that __ALL__ of the following sections must be included __and__ elaborated on, based on [Rule 2.1](https://discord.com/channels/369798142289510401/492328409175687179/1324496338985029662): \n> Offers, Specified commission rights for seller and buyer, Payment method, Refund policy, and Contact.\nPlease read through the <#492328409175687179> before posting, and visit our [TOS Guide](https://discord.com/channels/369798142289510401/1191922480961552424/1191922480961552424) for examples on how to elaborate.\n-# Note: Please explicitly mention \"Terms of Service\" in your post rather than just generally listing your terms."),
                ("wrong_channel", "Advertising in wrong channel", "advertising services outside of its designated [server category](https://discord.com/channels/369798142289510401/1393271200729268294/1476738956396597290). Please ensure your post does not contain any form of advertising if it isn't allowed by its local channel ruling. Refer to this [list](https://discord.com/channels/369798142289510401/1393288825987665990/1476704979598442662) to find what designated channel your services would fall under."),
                ("wrong_channel_no_role", "Advertising in wrong channel + no role", "advertising services outside of its designated [server category](https://discord.com/channels/369798142289510401/1393271200729268294/1476738956396597290), and without the Art Seller role. Please refer [here](https://discord.com/channels/369798142289510401/635030026911481856/1490007480955179180) for information on how to the obtain the Art Seller role."),
                ("chatting_daily_wins", "Chatting in daily w", "as the <#873116269640036362> channel is meant only for __posting__ positive achievements, and cannot be used for chatting. To respond to someone's daily win, please only use reaction emotes."),
                ("critique_format", "Critique format", "not following the format found in the channel's pins. Please follow the rules per channel. If unsure on how to formulate your critique request, or if you have any questions, please message staff at <@501746915218554881>."),
                ("art_in_chats", "Art in chats", "posting art/writing work unrelated to current conversation topic. Please refer to channel pins for local ruling, as all art and writing should be shared to <#369833248240566282> or <#616268995246424097> instead.")
            ]
            await db.executemany("INSERT INTO verbal_reasons (id, label, text) VALUES (?, ?, ?)", default_reasons)

        await db.commit()

# --- Verbal Reasons Methods ---

async def get_all_verbal_reasons() -> list:
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM verbal_reasons")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_verbal_reason(reason_id: str) -> dict:
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM verbal_reasons WHERE id = ?", (reason_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def add_verbal_reason(reason_id: str, label: str, text: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR REPLACE INTO verbal_reasons (id, label, text) VALUES (?, ?, ?)", (reason_id, label, text))
        await db.commit()

async def delete_verbal_reason(reason_id: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM verbal_reasons WHERE id = ?", (reason_id,))
        await db.commit()


# --- Warning Tracker Methods ---

async def add_warning(user_id: int, channel_id: int, message_id: int, message_content: str, staff_id: int = None, reason: str = None, warned_at: str = None):
    async with aiosqlite.connect(DB_NAME) as db:
        if warned_at:
            cursor = await db.execute('''
                INSERT INTO warnings (user_id, channel_id, message_id, message_content, staff_id, reason, warned_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, channel_id, message_id, message_content, staff_id, reason, warned_at))
        else:
            cursor = await db.execute('''
                INSERT INTO warnings (user_id, channel_id, message_id, message_content, staff_id, reason)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, channel_id, message_id, message_content, staff_id, reason))
        await db.commit()
        return cursor.lastrowid

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

# --- Reaction Roles Methods ---

async def add_reaction_role(message_id: int, guild_id: int, emoji: str, role_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO reaction_roles (message_id, guild_id, emoji, role_id)
            VALUES (?, ?, ?, ?)
        ''', (message_id, guild_id, emoji, role_id))
        await db.commit()

async def get_reaction_roles_for_message(message_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT * FROM reaction_roles WHERE message_id = ?', (message_id,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def delete_reaction_roles_for_message(message_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('DELETE FROM reaction_roles WHERE message_id = ?', (message_id,))
        await db.commit()

async def remove_reaction_role(message_id: int, emoji: str, role_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            DELETE FROM reaction_roles 
            WHERE message_id = ? AND emoji = ? AND role_id = ?
        ''', (message_id, emoji, role_id))
        await db.commit()

# --- Dropdown Roles Methods ---

async def add_dropdown_menu(message_id: int, placeholder: str, row_index: int) -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute('''
            INSERT INTO dropdown_menus (message_id, placeholder, row_index)
            VALUES (?, ?, ?)
        ''', (message_id, placeholder, row_index))
        await db.commit()
        return cursor.lastrowid

async def add_dropdown_option(menu_id: int, label: str, emoji: str, role_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO dropdown_options (menu_id, label, emoji, role_id)
            VALUES (?, ?, ?, ?)
        ''', (menu_id, label, emoji, role_id))
        await db.commit()

async def get_dropdowns_for_message(message_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        
        # Get menus
        cursor = await db.execute('SELECT * FROM dropdown_menus WHERE message_id = ? ORDER BY row_index ASC', (message_id,))
        menus = [dict(row) for row in await cursor.fetchall()]
        
        # Get options for each menu
        for menu in menus:
            cursor = await db.execute('SELECT * FROM dropdown_options WHERE menu_id = ?', (menu['id'],))
            menu['options'] = [dict(row) for row in await cursor.fetchall()]
            
        return menus

async def delete_dropdowns_for_message(message_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        # First find menus
        cursor = await db.execute('SELECT id FROM dropdown_menus WHERE message_id = ?', (message_id,))
        menus = await cursor.fetchall()
        
        for (menu_id,) in menus:
            await db.execute('DELETE FROM dropdown_options WHERE menu_id = ?', (menu_id,))
            
        await db.execute('DELETE FROM dropdown_menus WHERE message_id = ?', (message_id,))
        await db.commit()

