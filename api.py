from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import database

app = FastAPI()

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Reference to the Discord bot client for dynamic username resolution
bot_client = None

# Simple in-memory cache to prevent Discord API rate limiting
user_cache = {}

def set_bot_client(client):
    global bot_client
    bot_client = client

async def get_cached_user(user_id):
    if not user_id or not bot_client:
        return None
    
    # Return from cache if we have it
    if user_id in user_cache:
        return user_cache[user_id]
        
    # Try getting from bot's internal cache
    user = bot_client.get_user(user_id)
    
    # Fetch from API if not cached internally
    if not user:
        try:
            user = await bot_client.fetch_user(user_id)
        except Exception:
            return None
            
    if user:
        user_data = {
            "name": str(user),
            "avatar": user.display_avatar.url
        }
        user_cache[user_id] = user_data
        return user_data
        
    return None

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/guilds/{guild_id}/warnings")
async def get_warnings(guild_id: int, limit: int = 50, offset: int = 0):
    async with database.aiosqlite.connect(database.DB_NAME) as db:
        db.row_factory = database.aiosqlite.Row
        
        if guild_id == 0:
            cursor = await db.execute('''
                SELECT id, user_id, warned_at, channel_id, message_id, message_content, staff_id, reason, post_created_at 
                FROM warnings
                ORDER BY warned_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            rows = await cursor.fetchall()
            warnings = [dict(row) for row in rows]
            
            count_cursor = await db.execute('SELECT COUNT(*) FROM warnings')
            total = (await count_cursor.fetchone())[0]
        else:
            cursor = await db.execute('''
                SELECT id, user_id, warned_at, channel_id, message_id, message_content, staff_id, reason, post_created_at 
                FROM warnings
                WHERE guild_id = ? OR guild_id IS NULL
                ORDER BY warned_at DESC
                LIMIT ? OFFSET ?
            ''', (guild_id, limit, offset))
            rows = await cursor.fetchall()
            warnings = [dict(row) for row in rows]
            
            count_cursor = await db.execute('''
                SELECT COUNT(*) FROM warnings WHERE guild_id = ? OR guild_id IS NULL
            ''', (guild_id,))
            total = (await count_cursor.fetchone())[0]

    # Dynamically resolve Discord usernames
    if bot_client:
        for w in warnings:
            # Target User
            user_id = w.get('user_id')
            user_data = await get_cached_user(user_id)
            if user_data:
                w['user_name'] = user_data['name']
                w['user_avatar'] = user_data['avatar']
            else:
                w['user_name'] = f"Unknown ({user_id})" if user_id else "Unknown"
                w['user_avatar'] = None

            # Staff User
            staff_id = w.get('staff_id')
            if staff_id:
                staff_data = await get_cached_user(staff_id)
                if staff_data:
                    w['staff_name'] = staff_data['name']
                    w['staff_avatar'] = staff_data['avatar']
                else:
                    w['staff_name'] = f"Unknown ({staff_id})"
                    w['staff_avatar'] = None
            else:
                w['staff_name'] = "System"
                w['staff_avatar'] = None

    return {"warnings": warnings, "total": total}

@app.get("/api/guilds/{guild_id}/warning-reasons")
async def get_warning_reasons(guild_id: int):
    # For now, verbal reasons are global across the bot
    async with database.aiosqlite.connect(database.DB_NAME) as db:
        db.row_factory = database.aiosqlite.Row
        cursor = await db.execute('''
            SELECT id, label, text FROM verbal_reasons
        ''')
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

@app.get("/api/guilds/{guild_id}/paid-requests")
async def get_paid_requests(guild_id: int, limit: int = 50, offset: int = 0):
    async with database.aiosqlite.connect(database.DB_NAME) as db:
        db.row_factory = database.aiosqlite.Row
        
        cursor = await db.execute('''
            SELECT request_id, user_id, budget, sfw_nsfw, payment_method, use_case, content, status, created_at 
            FROM paid_requests
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        rows = await cursor.fetchall()
        requests = [dict(row) for row in rows]
        
        count_cursor = await db.execute('SELECT COUNT(*) FROM paid_requests')
        total = (await count_cursor.fetchone())[0]

    if bot_client:
        for r in requests:
            user_id = r.get('user_id')
            user_data = await get_cached_user(user_id)
            if user_data:
                r['user_name'] = user_data['name']
                r['user_avatar'] = user_data['avatar']
            else:
                r['user_name'] = f"Unknown ({user_id})" if user_id else "Unknown"
                r['user_avatar'] = None

    return {"requests": requests, "total": total}

@app.get("/api/guilds/{guild_id}/stats")
async def get_stats(guild_id: int):
    async with database.aiosqlite.connect(database.DB_NAME) as db:
        # Pending requests
        cursor = await db.execute("SELECT COUNT(*) FROM paid_requests WHERE status = 'pending'")
        pending_requests = (await cursor.fetchone())[0]

        if guild_id == 0:
            # Verbals this week
            cursor = await db.execute("SELECT COUNT(*) FROM warnings WHERE warned_at >= datetime('now', '-7 days')")
            verbals_this_week = (await cursor.fetchone())[0]
            
            # Verbals last week for trend
            cursor = await db.execute("SELECT COUNT(*) FROM warnings WHERE warned_at >= datetime('now', '-14 days') AND warned_at < datetime('now', '-7 days')")
            verbals_last_week = (await cursor.fetchone())[0]
        else:
            # Verbals this week
            cursor = await db.execute("SELECT COUNT(*) FROM warnings WHERE warned_at >= datetime('now', '-7 days') AND (guild_id = ? OR guild_id IS NULL)", (guild_id,))
            verbals_this_week = (await cursor.fetchone())[0]
            
            # Verbals last week for trend
            cursor = await db.execute("SELECT COUNT(*) FROM warnings WHERE warned_at >= datetime('now', '-14 days') AND warned_at < datetime('now', '-7 days') AND (guild_id = ? OR guild_id IS NULL)", (guild_id,))
            verbals_last_week = (await cursor.fetchone())[0]

        # Active reminders
        cursor = await db.execute("SELECT COUNT(*) FROM reminders")
        active_reminders = (await cursor.fetchone())[0]

    # Calculate trend
    if verbals_last_week == 0:
        trend = "+100%" if verbals_this_week > 0 else "0%"
    else:
        diff = ((verbals_this_week - verbals_last_week) / verbals_last_week) * 100
        trend = f"{'+' if diff > 0 else ''}{diff:.1f}%"

    ping = f"{round(bot_client.latency * 1000)}ms" if bot_client else "N/A"
    status = "Online" if bot_client and bot_client.is_ready() else "Offline"

    return {
        "bot_status": status,
        "ping": ping,
        "pending_requests": pending_requests,
        "verbals_this_week": verbals_this_week,
        "verbals_trend": f"{trend} vs last week",
        "active_reminders": active_reminders
    }

class GuildConfig(BaseModel):
    staff_notice_channel_id: Optional[str] = None
    staff_commands_channel_id: Optional[str] = None
    staff_log_channel_id: Optional[str] = None
    team_leader_role_id: Optional[str] = None
    moderator_role_id: Optional[str] = None
    trial_moderator_role_id: Optional[str] = None
    submit_channel_id: Optional[str] = None
    review_channel_id: Optional[str] = None
    approved_channel_id: Optional[str] = None
    approval_log_channel_id: Optional[str] = None
    active_limit: int = 2
    reminder_threshold: int = 14
    accepted_currencies: str = "USD, EUR, GBP, CAD, AUD, \\$|£|€"
    accepted_payments: str = "PayPal, Stripe, CashApp, Venmo, Ko-Fi"
    banned_terms_regex: str = "robux|robuck|robucks|crypto|btc|eth|sol|ltc|usdt|usdc"

@app.get("/api/guilds/{guild_id}/analytics")
async def get_analytics(guild_id: int, period: str = "month"):
    # period can be "week", "month", "year"
    days = 30
    if period == "week":
        days = 7
    elif period == "year":
        days = 365
        
    async with database.aiosqlite.connect(database.DB_NAME) as db:
        db.row_factory = database.aiosqlite.Row
        
        # Get warnings grouped by date
        if guild_id == 0:
            w_cursor = await db.execute(f"""
                SELECT date(warned_at) as day, COUNT(*) as count 
                FROM warnings 
                WHERE date(warned_at) >= date('now', '-{days} days')
                GROUP BY date(warned_at)
                ORDER BY day ASC
            """)
        else:
            w_cursor = await db.execute(f"""
                SELECT date(warned_at) as day, COUNT(*) as count 
                FROM warnings 
                WHERE guild_id = ? AND date(warned_at) >= date('now', '-{days} days')
                GROUP BY date(warned_at)
                ORDER BY day ASC
            """, (guild_id,))
        warn_rows = await w_cursor.fetchall()
        
        # Get paid requests grouped by date (paid_requests doesn't have guild_id, so we ignore it here)
        p_cursor = await db.execute(f"""
            SELECT date(created_at) as day, COUNT(*) as count 
            FROM paid_requests 
            WHERE date(created_at) >= date('now', '-{days} days')
            GROUP BY date(created_at)
            ORDER BY day ASC
        """)
        paid_rows = await p_cursor.fetchall()
        
        # Merge them into a single timeline array for Recharts
        timeline = {}
        from datetime import datetime, timedelta
        
        # Prefill timeline with 0s to ensure the chart doesn't skip days
        today = datetime.utcnow().date()
        for i in range(days):
            d = (today - timedelta(days=days - 1 - i)).isoformat()
            timeline[d] = {"date": d, "warnings": 0, "requests": 0}
            
        for r in warn_rows:
            if r["day"] in timeline:
                timeline[r["day"]]["warnings"] = r["count"]
                
        for r in paid_rows:
            if r["day"] in timeline:
                timeline[r["day"]]["requests"] = r["count"]
                
        return {"data": list(timeline.values())}

@app.get("/api/guilds")
async def get_guilds():
    if bot_client:
        return {"guilds": [{"id": str(g.id), "name": g.name, "icon": g.icon.url if g.icon else None} for g in bot_client.guilds]}
    else:
        async with database.aiosqlite.connect(database.DB_NAME) as db:
            cursor = await db.execute("SELECT DISTINCT guild_id FROM guild_configs WHERE guild_id != 0")
            rows = await cursor.fetchall()
            return {"guilds": [{"id": str(row[0]), "name": f"Server {row[0]}", "icon": None} for row in rows]}

@app.get("/api/guilds/{guild_id}/config")
async def get_config(guild_id: int):
    async with database.aiosqlite.connect(database.DB_NAME) as db:
        db.row_factory = database.aiosqlite.Row
        
        if guild_id == 0:
            cursor = await db.execute("SELECT * FROM guild_configs LIMIT 1")
        else:
            cursor = await db.execute("SELECT * FROM guild_configs WHERE guild_id = ?", (guild_id,))
        row = await cursor.fetchone()
        
        if row:
            config_dict = dict(row)
            for k, v in config_dict.items():
                if k.endswith('_id') and v is not None:
                    config_dict[k] = str(v)
            return config_dict
        
        # Return defaults if no config exists
        return GuildConfig().model_dump()

@app.post("/api/guilds/{guild_id}/config")
async def save_config(guild_id: int, config: GuildConfig):
    async with database.aiosqlite.connect(database.DB_NAME) as db:
        # Resolve guild_id 0 to actual guild_id if it exists
        if guild_id == 0:
            cursor = await db.execute("SELECT guild_id FROM guild_configs LIMIT 1")
            row = await cursor.fetchone()
            actual_guild_id = row[0] if row else 0
        else:
            actual_guild_id = guild_id

        # Check if exists
        cursor = await db.execute("SELECT 1 FROM guild_configs WHERE guild_id = ?", (actual_guild_id,))
        exists = await cursor.fetchone()
        
        if exists:
            await db.execute('''
                UPDATE guild_configs SET 
                    staff_notice_channel_id = ?, staff_commands_channel_id = ?, staff_log_channel_id = ?,
                    team_leader_role_id = ?, moderator_role_id = ?, trial_moderator_role_id = ?,
                    submit_channel_id = ?, review_channel_id = ?, approved_channel_id = ?, approval_log_channel_id = ?,
                    active_limit = ?, reminder_threshold = ?, accepted_currencies = ?, accepted_payments = ?, banned_terms_regex = ?
                WHERE guild_id = ?
            ''', (
                config.staff_notice_channel_id, config.staff_commands_channel_id, config.staff_log_channel_id,
                config.team_leader_role_id, config.moderator_role_id, config.trial_moderator_role_id,
                config.submit_channel_id, config.review_channel_id, config.approved_channel_id, config.approval_log_channel_id,
                config.active_limit, config.reminder_threshold, config.accepted_currencies, config.accepted_payments, config.banned_terms_regex,
                actual_guild_id
            ))
        else:
            await db.execute('''
                INSERT INTO guild_configs (
                    guild_id, staff_notice_channel_id, staff_commands_channel_id, staff_log_channel_id,
                    team_leader_role_id, moderator_role_id, trial_moderator_role_id,
                    submit_channel_id, review_channel_id, approved_channel_id, approval_log_channel_id,
                    active_limit, reminder_threshold, accepted_currencies, accepted_payments, banned_terms_regex
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                actual_guild_id, config.staff_notice_channel_id, config.staff_commands_channel_id, config.staff_log_channel_id,
                config.team_leader_role_id, config.moderator_role_id, config.trial_moderator_role_id,
                config.submit_channel_id, config.review_channel_id, config.approved_channel_id, config.approval_log_channel_id,
                config.active_limit, config.reminder_threshold, config.accepted_currencies, config.accepted_payments, config.banned_terms_regex
            ))
        await db.commit()
    return {"status": "success"}

class VerbalReason(BaseModel):
    id: str
    label: str
    text: str

class VerbalReasonsUpdate(BaseModel):
    reasons: List[VerbalReason]

@app.post("/api/guilds/{guild_id}/warning-reasons")
async def save_warning_reasons(guild_id: int, data: VerbalReasonsUpdate):
    async with database.aiosqlite.connect(database.DB_NAME) as db:
        # Delete existing reasons
        await db.execute("DELETE FROM verbal_reasons")
        
        # Insert new reasons
        for r in data.reasons:
            await db.execute('''
                INSERT INTO verbal_reasons (id, label, text) VALUES (?, ?, ?)
            ''', (r.id, r.label, r.text))
            
        await db.commit()
    return {"status": "success"}

@app.post("/api/paid-requests/purge")
async def purge_paid_requests():
    async with database.aiosqlite.connect(database.DB_NAME) as db:
        await db.execute("DELETE FROM paid_requests")
        await db.commit()
    return {"status": "success"}

@app.post("/api/guilds/{guild_id}/warnings/purge")
async def purge_warnings(guild_id: int):
    async with database.aiosqlite.connect(database.DB_NAME) as db:
        if guild_id == 0:
            await db.execute("DELETE FROM warnings")
        else:
            await db.execute("DELETE FROM warnings WHERE guild_id = ?", (guild_id,))
        await db.commit()
    return {"status": "success"}

@app.get("/api/guilds/{guild_id}/reminders")
async def get_reminders(guild_id: int):
    async with database.aiosqlite.connect(database.DB_NAME) as db:
        db.row_factory = database.aiosqlite.Row
        
        cursor = await db.execute('''
            SELECT id, user_id, about, remind_at, channel_id, created_at 
            FROM reminders
            ORDER BY remind_at ASC
        ''')
        rows = await cursor.fetchall()
        reminders = [dict(row) for row in rows]
        
    if bot_client:
        for r in reminders:
            user_id = r.get('user_id')
            user_data = await get_cached_user(user_id)
            if user_data:
                r['user_name'] = user_data['name']
                r['user_avatar'] = user_data['avatar']
            else:
                r['user_name'] = f"Unknown ({user_id})" if user_id else "Unknown"
                r['user_avatar'] = None

    return {"reminders": reminders}

@app.delete("/api/reminders/{reminder_id}")
async def delete_reminder(reminder_id: int):
    async with database.aiosqlite.connect(database.DB_NAME) as db:
        await db.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        await db.commit()
    return {"status": "success"}
