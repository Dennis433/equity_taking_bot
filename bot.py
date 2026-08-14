import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DEPOSIT_ADDRESS = "67ZMMrmdR7S2shWpLmfrHZd2dF68JZZyNGDWjfHWcQSV"

# Conversation state
WAITING_FOR_WALLET = 1

# In-memory storage (per user)
user_wallets = {}
user_stakes = {}


# ─── /start ───────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    first_name = update.effective_user.first_name
    keyboard = [
        [InlineKeyboardButton("💰 Stake", callback_data="stake")],
        [InlineKeyboardButton("📊 My Balance", callback_data="balance")],
        [InlineKeyboardButton("🔗 Connect Wallet", callback_data="connect_wallet")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 Welcome, {first_name}!\n\n"
        f"This is the Staking Bot. Stake your tokens and earn rewards!\n\n"
        f"Choose an option below 👇",
        reply_markup=reply_markup
    )


# ─── Button Handler ───────────────────────────────────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # ── Stake ──
    if query.data == "stake":
        if user_id not in user_wallets:
            await query.message.reply_text(
                "⚠️ You haven't connected a wallet yet!\n\n"
                "Please tap *🔗 Connect Wallet* first before staking.",
                parse_mode="Markdown"
            )
            return ConversationHandler.END

        await query.message.reply_text(
            f"📥 *To Stake, Send Your Deposit Here:*\n\n"
            f"`{DEPOSIT_ADDRESS}`\n\n"
            f"➡️ Send the amount you wish to stake to the address above.\n"
            f"✅ Your stake will be confirmed once the transaction is verified.\n\n"
            f"⚠️ _Only send supported tokens. Double-check the address before sending._",
            parse_mode="Markdown"
        )

    # ── Connect Wallet ──
    elif query.data == "connect_wallet":
        await query.message.reply_text(
            "🔗 *Connect Your Wallet*\n\n"
            "Please send your wallet address below 👇",
            parse_mode="Markdown"
        )
        return WAITING_FOR_WALLET

    # ── Balance ──
    elif query.data == "balance":
        wallet = user_wallets.get(user_id)
        stake = user_stakes.get(user_id, 0)

        if not wallet:
            await query.message.reply_text(
                "⚠️ No wallet connected yet.\n\nTap *🔗 Connect Wallet* to get started.",
                parse_mode="Markdown"
            )
        else:
            await query.message.reply_text(
                f"📊 *Your Staking Dashboard*\n\n"
                f"🔗 Wallet: `{wallet}`\n"
                f"💰 Total Staked: `{stake} tokens`\n\n"
                f"_Stake more to earn higher rewards!_",
                parse_mode="Markdown"
            )


# ─── Receive Wallet Address ───────────────────────────────
async def receive_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet_address = update.message.text.strip()

    # Basic validation — adjust length rules per your chain
    if len(wallet_address) < 20:
        await update.message.reply_text(
            "❌ That doesn't look like a valid wallet address. Please try again."
        )
        return WAITING_FOR_WALLET

    user_wallets[user_id] = wallet_address

    keyboard = [
        [InlineKeyboardButton("💰 Stake", callback_data="stake")],
        [InlineKeyboardButton("📊 My Balance", callback_data="balance")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ *Wallet Connected Successfully!*\n\n"
        f"🔗 Address: `{wallet_address}`\n\n"
        f"You can now stake your tokens or check your balance below 👇",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    return ConversationHandler.END


# ─── Cancel ───────────────────────────────────────────────
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Action cancelled.")
    return ConversationHandler.END


# ─── Main ─────────────────────────────────────────────────
def main():
    app = (
        Application.builder()
        .token(TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .build()
    )

    # Conversation handler for wallet connection
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler)],
        states={
            WAITING_FOR_WALLET: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_wallet)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()