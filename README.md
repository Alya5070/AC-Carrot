# Carrot

Carrot is a Discord bot and web dashboard for community moderation, commissions handling, and support. It includes warning tracking, paid request submissions, automated user reminders, interactive support DMs, and a dashboard for logging and analytics.

---

## Features

### 1. Moderation & Warning Tracker
- **Remove Post (Context Menu):** Right click a message, select **Apps > Remove Post**, and select a reason to delete the post, issue a verbal warning to the user, log the action, and DM the user.
- **Verbal Warning Logs:** Track all warnings issued to users.
- **History Synchronization:** Import up to three months of past warnings from public channels directly into the database.
- **Dynamic Warning Reasons:** Administrators can add, edit, or remove pre-configured warning templates.

### 2. Paid Requests (Commissions Portal)
- **Persistent Form Button:** Post a persistent embed containing a submission button. Users can click this button to open a modal form.
- **Commission Review Queue:** Submitted requests go to a staff review channel with interactive approval and rejection buttons.
- **User DMs & Reminders:** The bot automatically DMs the user with active commission status changes and sends reminders for unfulfilled or outdated requests.

### 3. Interactive Support Chatbot
- **Initiate Support button:** Post a support banner in a channel. Users click a button to start a private DM conversation.
- **ModMail Redirection:** The bot handles direct messages and guides users to open support tickets or answer options before sending reports to staff.

### 4. Personal Reminders
- Set timed reminders with flexible durations (such as `5m`, `2h`, or `1d`).

---

## Discord Bot Commands

All commands are restricted to the configured staff commands channel, except for the superuser/developer bypass.

### Slash Commands
* `/verbal [action] [reason]`
  * Description: Manage dynamic verbal warning reasons in the database.
  * Permission: Team Leaders only.
* `/remindme [about] [in] [where]`
  * Description: Set a personal reminder.
  * Parameters:
    * `about`: What you want to be reminded of.
    * `in`: Time duration (such as `5m`, `2h`, or `1d`).
    * `where`: Channel to ping you in (type `here`, mention a channel, or omit for DM).
* `/purge [target]`
  * Description: Purge database tables.
  * Choices: `Paid Requests` or `Verbals`.
  * Permission: Developer only.

### Text Prefix Commands
* `!carrothelp`
  * View the interactive help menu pages.
* `!verbals [user]`
  * Check verbal warning logs for yourself or a specified user.
* `!verbalby [staff]`
  * Check all verbal warnings issued by a specific staff member.
* `!delverbal [warning_id] [reason]`
  * Revoke a warning by ID, notify the user, and log the action.
  * Permission: Staff roles only.
* `!sync_warnings`
  * Synchronize warning history from the staff notice channel from the past 90 days.
  * Permission: Administrators only.
* `!setup_paid_requests`
  * Send the persistent paid request form button embed to the current channel.
  * Permission: Administrators only.
* `!chatbot_setup_channel`
  * Send the persistent support contact banner to the current channel.
  * Permission: Administrators only.
* `!trigger_paid_reminders [duration]`
  * Force check and send warnings for old unpaid requests.
  * Permission: Administrators only.
* `!resend_pendings`
  * Resend pending requests from the database to the staff review channel.
  * Permission: Administrators only.
* `!purge [target]`
  * Purge the target table (`paid requests` or `verbals`).
  * Permission: Developer only.

---

## Technical Stack
* **Bot:** Python 3.10+, `discord.py`
* **API:** FastAPI, Uvicorn
* **Database:** SQLite with `aiosqlite`
* **Dashboard:** Next.js (App Router), React, Tailwind CSS

---

## Local Setup

### Prerequisite Environment Variables
Create a file named `.env` in the root folder with the following variables:

```env
DISCORD_TOKEN=your_discord_bot_token
PORT=8000
```

### 1. Bot & API Setup
1. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the bot and FastAPI server:
   ```bash
   python bot.py
   ```

### 2. Next.js Dashboard Setup
1. Navigate to the dashboard directory:
   ```bash
   cd dashboard
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
4. Access the dashboard UI in your browser at `http://localhost:3000`.

---

## Deployment (Railway)
This project is configured to run on Railway using the `Procfile` at the root.

1. Create a new service on Railway.
2. Bind your GitHub repository.
3. Configure the environment variables (`DISCORD_TOKEN` and `PORT`).
4. Ensure the bot's application settings in the Discord Developer Portal have **Server Members Intent** and **Message Content Intent** enabled.
