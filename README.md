# Beta Testing Bot

A Telegram bot for collecting and organizing beta tester feedback on projects.

## How It Works

1. Admin registers a project to test
2. Testers submit feedback using hashtags in the group chat
3. Bot collects feedback and generates AI-summarized reports

## Commands

**For testers:**
- `/start` — How to use the bot
- `/projects` — See active projects
- `#ProjectName your feedback` — Submit feedback

**For admins:**
- `/register ProjectName` — Start testing a new project
- `/close ProjectName` — End testing period
- `/feedback ProjectName` — Export AI-summarized report

## Feedback Report

The `/feedback` command generates a structured report with:
- Summary
- UX & Usability
- Bugs & Issues
- Feature Requests
- What Works Well
- Comparisons to Competitors

## Setup

### Environment Variables

```
TELEGRAM_BOT_TOKEN=your_bot_token
CLAUDE_API_KEY=your_anthropic_api_key
ADMIN_USER_IDS=comma_separated_telegram_user_ids
```

Get your Telegram user ID from [@userinfobot](https://t.me/userinfobot).

### Run Locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

### Deploy to Railway

```bash
railway login
railway init
railway up
railway variables set TELEGRAM_BOT_TOKEN=xxx
railway variables set CLAUDE_API_KEY=xxx
railway variables set ADMIN_USER_IDS=xxx
```
