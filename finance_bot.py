from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from storage import load_data, save_data
from emoji import emojize

CONFIG_INCOME, CONFIG_BUDGET, CONFIRM_RESET = range(3)


# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to Finance Bot! Use /help to see available commands.")

# /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
Available commands:
/config - Set income & budgets
/log - Log income or expense
/summary - Show budget summary
/reset - Delete all your data
/notifyon - Enable reminders
/notifyoff - Disable reminders
""")

# /config command
async def config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💵 Please enter your monthly income:")
    return CONFIG_INCOME

async def set_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        income = float(update.message.text)
        context.user_data["income"] = income
        context.user_data["budgets"] = {}
        await update.message.reply_text("✅ Income saved. Now enter budgets (e.g., food 200). Type 'done' to finish.")
        return CONFIG_BUDGET
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number for income.")
        return CONFIG_INCOME

async def set_budgets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if "done" in update.message.text.lower():
        data = {
            "income": context.user_data["income"],
            "budgets": context.user_data["budgets"],
            "expenses": []
        }
        save_data(user_id, data)
        await update.message.reply_text("✅ Budget configuration saved.")
        return ConversationHandler.END

    try:
        category, amount = update.message.text.split()
        context.user_data["budgets"][category] = float(amount)
        await update.message.reply_text(f"Added budget: {category} - {amount}. Type 'done' when finished.")
    except:
        await update.message.reply_text("❌ Use format: category amount (e.g., food 200)")
    return CONFIG_BUDGET


# /log command
async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 Please enter your income or expense (e.g., income 500 or expense 200 food).")

async def handle_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = load_data(user_id)

    if context.user_data.get("awaiting_reset"):
        if update.message.text.strip().upper() == "YES":
            save_data(user_id, {"income": 0, "budgets": {}, "expenses": []})
            context.user_data["awaiting_reset"] = False
            await update.message.reply_text("✅ All your data has been reset.")
        else:
            context.user_data["awaiting_reset"] = False
            await update.message.reply_text("❌ Reset cancelled.")
        return

    try:
        parts = update.message.text.strip().split()
        entry_type = parts[0].lower()
        amount = float(parts[1])
        category = parts[2] if len(parts) > 2 else "unspecified"

        if entry_type == "income":
            data["income"] += amount
        elif entry_type == "expense":
            data["expenses"].append({"category": category, "amount": amount})
        else:
            raise ValueError("Invalid type")

        save_data(user_id, data)
        await update.message.reply_text(f"✅ {entry_type.capitalize()} of {amount} logged under {category}.")
    except:
        await update.message.reply_text("❌ Please use the format: 'income/expense amount category' (e.g., income 500 or expense 200 food).")


# /summary command
def progress_bar(current, total):
    ratio = min(current / total, 1.0) if total else 0
    filled = int(ratio * 10)
    bar = "█" * filled + "░" * (10 - filled)
    return bar

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = load_data(user_id)

    income = data.get("income", 0)
    budgets = data.get("budgets", {})
    expenses = data.get("expenses", [])

    total_expenses = sum(entry["amount"] for entry in expenses)
    expense_summary = {}
    for entry in expenses:
        expense_summary[entry["category"]] = expense_summary.get(entry["category"], 0) + entry["amount"]

    budget_lines = []
    for category, limit in budgets.items():
        spent = expense_summary.get(category, 0)
        bar = progress_bar(spent, limit)
        budget_lines.append(f"{category}: {spent}/{limit} [{bar}]")

    if not budget_lines:
        budget_lines.append("No budgets set.")

    uncategorized = [f"{k}: {v}" for k, v in expense_summary.items() if k not in budgets]
    if not uncategorized:
        uncategorized.append("None.")

    await update.message.reply_text(f"""
📊 *Budget Summary*
Total Income: {income}
Total Expenses: {total_expenses}

💼 *Budgets:*
{chr(10).join(budget_lines)}

🧾 *Other Expenses:*
{chr(10).join(uncategorized)}
""", parse_mode="Markdown")


# /reset command
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_reset"] = True
    await update.message.reply_text("⚠️ Are you sure you want to reset all your data? Type 'YES' to confirm.")


# Dummy reminder commands
async def notify_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔔 Reminders enabled!")

async def notify_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔕 Reminders disabled!")


# Handlers
def setup_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("log", log))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("notifyon", notify_on))
    app.add_handler(CommandHandler("notifyoff", notify_off))

    # Conversation handler for /config
    config_conv = ConversationHandler(
        entry_points=[CommandHandler("config", config)],
        states={
            CONFIG_INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_income)],
            CONFIG_BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_budgets)],
        },
        fallbacks=[],
    )
    app.add_handler(config_conv)
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_log))


# Entry point
def main():
    import os
    from telegram.ext import Application

    token = os.getenv("TELEGRAM_TOKEN")
    app = Application.builder().token(token).build()
    setup_handlers(app)
    app.run_polling()

if __name__ == "__main__":
    main()