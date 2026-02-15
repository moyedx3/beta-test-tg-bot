# CryptoAppReview Beta Testing Bot

A Telegram bot for collecting beta tester feedback and feeding it into the CryptoAppReview article workflow.

**Site:** https://cryptoappreview-production.up.railway.app/

## How It Works

1. **Admin registers an app** to review
2. **Testers use the app** and submit feedback via hashtags
3. **Bot aggregates feedback** and generates AI-summarized reports
4. **Summary sent to Char** (AI assistant) for research & article writing
5. **Review published** on CryptoAppReview

## Commands

**For testers:**
- `/start` — How to use the bot
- `/projects` — See active apps to test
- `#AppName your feedback` — Submit feedback

**For admins:**
- `/register AppName` — Start testing a new app
- `/close AppName` — End testing period
- `/feedback AppName` — Generate AI summary & send to Char

## Example Workflow

```
# Admin registers app
/register MetaMask

# Testers submit feedback
#MetaMask The new portfolio view is confusing
#MetaMask Love the multi-chain support
#MetaMask Gas estimation seems off

# Admin generates report
/feedback MetaMask

# Bot sends summary to cryptoappreview group
# Char receives it and starts research
```

## Feedback Report

The `/feedback` command generates:
- AI-generated summary with themes
- Full raw feedback for context
- Auto-sends to CryptoAppReview group for article writing

## Setup

### Environment Variables

```
TELEGRAM_BOT_TOKEN=your_bot_token
CLAUDE_API_KEY=your_anthropic_api_key
ADMIN_USER_IDS=comma_separated_telegram_user_ids
CRYPTOAPPREVIEW_GROUP_ID=-5237557865  # Group where Char receives summaries
```

Get your Telegram user ID from [@userinfobot](https://t.me/userinfobot).

Get your group ID by adding [@userinfobot](https://t.me/userinfobot) to the group.

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
railway variables set CRYPTOAPPREVIEW_GROUP_ID=-5237557865
```

## Integration with CryptoAppReview

When `/feedback` is run, the bot automatically sends:
1. AI summary to the configured group
2. Full raw feedback
3. Trigger message for Char to begin research

Char then:
- Reads workflow docs from obsidian vault
- Researches the app
- Writes review article
- Publishes to site

## Credits

Built for CryptoAppReview — opinionated crypto app reviews in the style of theneedledrop.com.
