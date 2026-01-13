import os
import re
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import anthropic

import db

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
ADMIN_USER_IDS = [int(x.strip()) for x in os.getenv("ADMIN_USER_IDS", "").split(",") if x.strip()]

HASHTAG_PATTERN = re.compile(r"#(\w+)\s+(.+)", re.DOTALL)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_USER_IDS


# /start - Onboarding
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
Welcome to Nutype!

We're a community of beta testers for early-stage crypto and onchain projects.

How it works:
1. Admins will register new projects to test
2. You try out the project and share feedback
3. Use #ProjectName to tag your feedback
4. We aggregate and send it to the project team

Commands:
/projects - See active projects to test
/start - See this message again

To give feedback, just type:
#ProjectName your feedback here

Happy testing!
    """.strip()
    await update.message.reply_text(welcome_text)


# /projects - List active projects
async def projects_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    projects = db.get_active_projects()

    if not projects:
        await update.message.reply_text("No active projects right now. Stay tuned!")
        return

    lines = ["Active projects to test:\n"]
    for p in projects:
        lines.append(f"  #{p['name']}")

    lines.append("\nTo give feedback, type:\n#ProjectName your feedback here")
    await update.message.reply_text("\n".join(lines))


# /register ProjectName - Admin only
async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("Only admins can register projects.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /register ProjectName")
        return

    project_name = context.args[0]

    if db.create_project(project_name):
        await update.message.reply_text(
            f"Project #{project_name} registered!\n\n"
            f"Testers can now submit feedback with:\n#ProjectName their feedback"
        )
    else:
        await update.message.reply_text(f"Project '{project_name}' already exists.")


# /close ProjectName - Admin only
async def close_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("Only admins can close projects.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /close ProjectName")
        return

    project_name = context.args[0]

    if db.close_project(project_name):
        await update.message.reply_text(f"Project #{project_name} closed.")
    else:
        await update.message.reply_text(f"Project '{project_name}' not found or already closed.")


# /feedback ProjectName - Admin only, AI summarized
async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("Only admins can export feedback.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /feedback ProjectName")
        return

    project_name = context.args[0]
    project = db.get_project_by_name(project_name)

    if not project:
        await update.message.reply_text(f"Project '{project_name}' not found.")
        return

    feedback_list = db.get_feedback_for_project(project_name)

    if not feedback_list:
        await update.message.reply_text(f"No feedback collected for #{project_name} yet.")
        return

    await update.message.reply_text("Generating AI summary... this may take a moment.")

    # Format raw feedback
    raw_feedback = "\n\n".join([
        f"@{f['username'] or 'anonymous'} ({f['created_at']}):\n{f['message']}"
        for f in feedback_list
    ])

    # Generate AI summary
    try:
        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": f"""You are helping a beta testing community summarize user feedback for a crypto project called "{project_name}".

Below is raw feedback from testers. Please create a structured summary that can be shared with the project team.

Format your response as:

## Summary
(2-3 sentence overview)

## UX & Usability
(bullet points)

## Bugs & Issues
(bullet points)

## Feature Requests
(bullet points)

## What Works Well
(bullet points)

## Comparisons to Competitors
(bullet points, if any)

If a category has no relevant feedback, write "No feedback in this category."

---
RAW FEEDBACK:

{raw_feedback}"""
            }]
        )
        summary = response.content[0].text
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        summary = "(AI summary failed - showing raw feedback only)"

    # Build export
    status = "Active" if project["is_active"] else "Closed"
    export_text = f"""# {project_name} - Beta Testing Feedback

**Status:** {status}
**Feedback count:** {len(feedback_list)}

---

{summary}

---

## Raw Feedback

{raw_feedback}
"""

    # Telegram has a 4096 char limit, so split if needed
    if len(export_text) <= 4096:
        await update.message.reply_text(export_text)
    else:
        # Send summary first
        await update.message.reply_text(f"# {project_name} - Beta Testing Feedback\n\n{summary}")
        # Then raw feedback in chunks
        for i in range(0, len(raw_feedback), 4000):
            chunk = raw_feedback[i:i+4000]
            await update.message.reply_text(f"Raw feedback (continued):\n\n{chunk}")


# Hashtag feedback capture
async def capture_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    match = HASHTAG_PATTERN.match(text)

    if not match:
        return

    project_name = match.group(1)
    feedback_text = match.group(2).strip()

    if not feedback_text:
        return

    user = update.effective_user
    username = user.username or user.first_name or str(user.id)

    if db.add_feedback(project_name, user.id, username, feedback_text):
        await update.message.reply_text(
            f"Feedback recorded for #{project_name}. Thanks!",
            quote=True
        )
    else:
        # Project doesn't exist or not active - silently ignore
        # (don't spam the chat for unrelated hashtags)
        pass


def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set")

    if not ADMIN_USER_IDS:
        logger.warning("ADMIN_USER_IDS not set - no one can use admin commands")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("projects", projects_command))
    app.add_handler(CommandHandler("register", register_command))
    app.add_handler(CommandHandler("close", close_command))
    app.add_handler(CommandHandler("feedback", feedback_command))

    # Hashtag capture (must be after commands)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, capture_feedback))

    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
