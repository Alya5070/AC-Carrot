import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

# Original IDs from .env
CORRECT_IDS = {
    'staff_notice_channel_id': os.getenv('STAFF_NOTICE_CHANNEL_ID'),
    'staff_commands_channel_id': os.getenv('STAFF_COMMANDS_CHANNEL_ID'),
    'staff_log_channel_id': os.getenv('STAFF_LOG_CHANNEL_ID'),
    'team_leader_role_id': os.getenv('TEAM_LEADER_ROLE_ID'),
    'moderator_role_id': os.getenv('MODERATOR_ID'),
    'trial_moderator_role_id': os.getenv('TRIAL_MODERATOR_ID'),
    'submit_channel_id': os.getenv('SUBMIT_PAID_REQUEST_CHANNEL_ID'),
    'review_channel_id': os.getenv('PAID_REQUEST_REVIEW_CHANNEL_ID'),
    'approved_channel_id': os.getenv('PAID_REQUEST_APPROVED_CHANNEL_ID'),
    'approval_log_channel_id': os.getenv('APPROVAL_LOG_CHANNEL_ID')
}

db = sqlite3.connect('database.sqlite')
db.row_factory = sqlite3.Row

configs = db.execute("SELECT * FROM guild_configs").fetchall()

for config in configs:
    guild_id = config['guild_id']
    print(f"Fixing config for guild {guild_id}...")
    
    updates = []
    values = []
    
    for key, correct_val in CORRECT_IDS.items():
        if correct_val:
            updates.append(f"{key} = ?")
            values.append(int(correct_val))
            
    if updates:
        values.append(guild_id)
        db.execute(f"UPDATE guild_configs SET {', '.join(updates)} WHERE guild_id = ?", values)

db.commit()
print("Fixed corrupted IDs in database!")
