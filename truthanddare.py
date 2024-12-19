from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import random
import json
from typing import Dict, List
from datetime import datetime
import os

# Logging
import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

# Game states
class GameState:
    IDLE = "idle"
    PLAYING = "playing"
    WAITING_CHOICE = "waiting_choice"
    WAITING_COMPLETION = "waiting_completion"

class TruthDareGame:
    def __init__(self):
        self.games: Dict[int, dict] = {}  # Chat ID -> game data
        self.load_questions()
        self.game_adjectives = [
            "Exciting", "Mysterious", "Thrilling", "Epic", "Fantastic",
            "Amazing", "Magical", "Super", "Awesome", "Ultimate",
            "Cosmic", "Legendary", "Mighty", "Royal", "Golden"
        ]
        self.game_nouns = [
            "Challenge", "Adventure", "Quest", "Journey", "Mission",
            "Party", "Game", "Round", "Tournament", "Battle",
            "Contest", "Championship", "Match", "Session", "Series"
        ]
    
    def load_questions(self):
        # Load truth and dare questions from JSON files
        try:
            with open('data/truth.json', 'r') as f:
                self.truth_questions = json.load(f)
            with open('data/dare.json', 'r') as f:
                self.dare_questions = json.load(f)
        except FileNotFoundError:
            self.truth_questions = ["Default truth question"]
            self.dare_questions = ["Default dare question"]
    
    def generate_game_name(self) -> str:
        return f"{random.choice(self.game_adjectives)} {random.choice(self.game_nouns)}"
    
    def generate_game_id(self) -> str:
        # Generate a game ID with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        random_num = random.randint(1000, 9999)
        return f"G{timestamp}_{random_num}"
    
    def init_game(self, chat_id: int, admin_id: int):
        game_name = self.generate_game_name()
        game_id = self.generate_game_id()
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.games[chat_id] = {
            "players": [],
            "scores": {},
            "current_player": None,
            "state": GameState.IDLE,
            "admin_id": admin_id,
            "game_name": game_name,
            "game_id": game_id,
            "start_time": start_time
        }
        return game_name, game_id, start_time
    
    def add_player(self, chat_id: int, user_id: int, username: str) -> bool:
        if chat_id not in self.games:
            print(f"Chat {chat_id} not found in games")
            return False
        
        if user_id in self.games[chat_id]["players"]:
            print(f"Player {username} ({user_id}) already in game")
            return False
        
        self.games[chat_id]["players"].append(user_id)
        self.games[chat_id]["scores"][user_id] = 0
        print(f"Added player {username} ({user_id}) to game in chat {chat_id}")
        return True

game = TruthDareGame() 
#NOTEPAD PASTE HERRE

# Configure logging
#logging.basicConfig(level=logging.INFO)

# Utility function to check if the chat is a group or supergroup
def is_group_chat(update: Update) -> bool:
    return update.effective_chat and update.effective_chat.type in ["group", "supergroup"]

# Function to enforce group-only command behavior
async def check_group_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not is_group_chat(update):
        await update.message.reply_text("This command can only be used in groups!")
        return False
    return True

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    print(f"Chat ID: {chat_id}, Chat Type: {update.effective_chat.type}")  # Debug statement

    # Check if the chat type is private
    if update.effective_chat.type == "private":
        await update.message.reply_text(
            "🎉 Welcome to the Virtual Truth and Dare Bot! 🎉\n"
            "This bot will make your game more fun and easy to play. Just create a group with whom you want to play, "
            "add me to that group, and boom! Let's go!\n\n"
            "### Game Features:\n"
            "• Unique game IDs for tracking\n"
            "• Random game names\n"
            "• Score tracking\n"
            "• Task changing option (deducts 1 point)\n"
            "• Admin controls\n\n"
            "### Rules:\n"
            "• Minimum 2 players required\n"
            "• Only group admin can verify task completion\n"
            "• Only selected player can choose Truth or Dare\n"
            "• Points are awarded for completed tasks\n"
            "• Changing task will deduct 1 point\n"
            "• Players can leave using /remove\n\n"
            "### Available Commands:\n"
            "• /newgame - Start a new game\n"
            "• /stop - Stop current game (admin)\n"
            "• /help - Show this message\n"
            "• /add - Join the game\n"
            "• /remove - Leave the game\n"
            "• /startgame - Begin playing (admin)\n"
            "• /scores - View scoreboard\n\n"
            "For any issues or feedback, contact: [@ReachMateSR96_bot](https://t.me/ReachMateSR96_bot)"
        )
    else:
        await update.message.reply_text(
            "Welcome to the group! Please use /newgame to create a Truth and Dare game here."
        )

        #New CODE TILL HERE 
async def add_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_group_chat(update):
        await update.message.reply_text("This command works only in groups!")
    
        return
    
    try:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        if chat_id not in game.games:
            await update.message.reply_text(
                "❌ No active game found!\n"
                "Please start a new game with /newgame"
            )
            return
        
        game_data = game.games[chat_id]
        game_name = game_data["game_name"]
        
        # Check if player is already in the game
        if user_id in game_data["players"]:
            await update.message.reply_text(
                f"❌ *{game_name}*\n\n"
                "You are already in the game!",
                parse_mode='Markdown'
            )
            return
        
        # Check if command is used by admin to add someone else
        if user_id == game_data["admin_id"] and context.args:
            target = context.args[0]
            # Remove @ if present in username
            target = target.replace("@", "")
            
            try:
                # Try to get chat member info
                if target.isdigit():
                    chat_member = await context.bot.get_chat_member(chat_id, int(target))
                    target_user = chat_member.user
                else:
                    chat_member = await context.bot.get_chat_member(chat_id, "@" + target)
                    target_user = chat_member.user
                
                # Check if target player is already in game
                if target_user.id in game_data["players"]:
                    await update.message.reply_text(
                        f"❌ *{game_name}*\n\n"
                        f"{target_user.username or target_user.first_name} is already in the game!",
                        parse_mode='Markdown'
                    )
                    return
                
                # Add the target player
                game_data["players"].append(target_user.id)
                game_data["scores"][target_user.id] = 0
                
                await update.message.reply_text(
                    f"✅ *{game_name}*\n\n"
                    f"{target_user.username or target_user.first_name} has been added to the game!\n"
                    f"Current players: {len(game_data['players'])}",
                    parse_mode='Markdown'
                )
                
            except Exception as e:
                print(f"Error adding player: {e}")
                await update.message.reply_text(
                    "❌ Could not add player.\n"
                    "Make sure they are in the group and the username/ID is correct!"
                )
            return
        
        # Add the command user to the game
        username = update.effective_user.username or update.effective_user.first_name
        game_data["players"].append(user_id)
        game_data["scores"][user_id] = 0
        
        await update.message.reply_text(
            f"✅ *{game_name}*\n\n"
            f"Welcome {username}! You've been added to the game!\n"
            f"Current players: {len(game_data['players'])}",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        print(f"Error in add_player: {e}")
        await update.message.reply_text(
            "❌ An error occurred while processing your request.\n"
            "Please try again or contact the admin."
        )

async def remove_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_group_chat(update):
        await update.message.reply_text("This command works only in groups!")
           
        return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if chat_id not in game.games:
        await update.message.reply_text("No active game in this group!")
        return
    
    game_data = game.games[chat_id]
    
    # Only admin can remove other players
    if user_id == game_data["admin_id"] and context.args:
        target = context.args[0].replace("@", "")
        try:
            if target.isdigit():
                chat_member = await context.bot.get_chat_member(chat_id, int(target))
                target_user = chat_member.user
            else:
                chat_member = await context.bot.get_chat_member(chat_id, "@" + target)
                target_user = chat_member.user
            
            if target_user.id in game_data["players"]:
                game_data["players"].remove(target_user.id)
                del game_data["scores"][target_user.id]
                await update.message.reply_text(f"Player {target_user.username or target_user.first_name} removed from the game!")
            else:
                await update.message.reply_text("This player is not in the game!")
            
        except Exception as e:
            await update.message.reply_text("Could not remove player. Make sure the username/ID is correct!")
        return
    
    # Allow players to remove themselves
    if user_id in game_data["players"]:
        game_data["players"].remove(user_id)
        del game_data["scores"][user_id]
        await update.message.reply_text("You have been removed from the game!")
    else:
        await update.message.reply_text("You are not in the game!")

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_group_chat(update):
        
        return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if chat_id not in game.games:
        await update.message.reply_text("Please First Create a Game using /newgame .")
        return
    
    game_data = game.games[chat_id]
    game_name = game_data["game_name"]
    
    if user_id != game_data["admin_id"]:
        await update.message.reply_text("Only the admin can start the game!")
        return
    
    if len(game_data["players"]) < 2:
        await update.message.reply_text("Need at least 2 players to start!")
        return
    
    try:
        game_data["state"] = GameState.PLAYING
        await update.message.reply_text(
            f"🎯 {game_name} is starting!\nGet ready for some fun!"
        )
        await select_next_player(update, context)
    except Exception as e:
        print(f"Error in start_game: {e}")
        await update.message.reply_text(
            "An error occurred while starting the game. Please try again."
        )

async def select_next_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game_data = game.games[chat_id]
    game_name = game_data["game_name"]
    
    # Select random player
    current_player = random.choice(game_data["players"])
    game_data["current_player"] = current_player
    
    try:
        user = await context.bot.get_chat_member(chat_id, current_player)
        username = user.user.username or user.user.first_name
    except:
        username = f"Player{current_player}"
    
    # Create truth/dare buttons
    keyboard = [
        [
            InlineKeyboardButton("Truth 🤔", callback_data="truth"),
            InlineKeyboardButton("Dare 🎯", callback_data="dare")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        # Changed message format to avoid parsing issues
        message_text = f"🎲 {game_name}\n\n{username}, Truth or Dare?"
        await context.bot.send_message(
            chat_id=chat_id,
            text=message_text,
            reply_markup=reply_markup
        )
        game_data["state"] = GameState.WAITING_CHOICE
    except Exception as e:
        print(f"Error in select_next_player: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="An error occurred while selecting the next player. Please try again."
        )

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    
    if chat_id not in game.games:
        await query.answer("Game not active!")
        return
    
    game_data = game.games[chat_id]
    if user_id != game_data["current_player"]:
        await query.answer("This is not your turn!")
        return
    
    choice = query.data  # "truth" or "dare"
    game_data["current_choice"] = choice  # Store the current choice
    question = random.choice(game.truth_questions if choice == "truth" else game.dare_questions)
    game_data["current_question"] = question  # Store the current question
    
    # Create completion buttons including change task
    keyboard = [
        [
            InlineKeyboardButton("Task Completed ✅", callback_data="complete"),
            InlineKeyboardButton("Skip ⏭️", callback_data="skip")
        ],
        [
            InlineKeyboardButton("Change Task 🔄", callback_data="change_task")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        f"Here's your {choice}:\n\n{question}",
        reply_markup=reply_markup
    )
    game_data["state"] = GameState.WAITING_COMPLETION

async def handle_change_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    
    if chat_id not in game.games:
        await query.answer("Game not active!")
        return
    
    game_data = game.games[chat_id]
    if user_id != game_data["current_player"]:
        await query.answer("Only the current player can change their task!")
        return
    
    # Get the current choice (truth/dare) and get a new question
    current_choice = game_data.get("current_choice")
    if not current_choice:
        await query.answer("Cannot change task at this time!")
        return
    
    # Deduct point for changing task (allow negative scores)
    game_data["scores"][user_id] = game_data["scores"][user_id] - 1
    
    # Get a new question different from the current one
    current_question = game_data.get("current_question", "")
    questions = game.truth_questions if current_choice == "truth" else game.dare_questions
    new_question = current_question
    
    # Make sure we get a different question
    while new_question == current_question and len(questions) > 1:
        new_question = random.choice(questions)
    
    game_data["current_question"] = new_question
    
    # Recreate the buttons
    keyboard = [
        [
            InlineKeyboardButton("Task Completed ✅", callback_data="complete"),
            InlineKeyboardButton("Skip ⏭️", callback_data="skip")
        ],
        [
            InlineKeyboardButton("Change Task 🔄", callback_data="change_task")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        f"Here's your new {current_choice}:\n\n{new_question}\n\n"
        f"(-1 point for changing task. Current score: {game_data['scores'][user_id]})",
        reply_markup=reply_markup
    )
    await query.answer("Task changed! -1 point")

async def handle_completion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    
    if chat_id not in game.games:
        await query.answer("Game not active!")
        return
    
    game_data = game.games[chat_id]
    action = query.data  # "complete" or "skip"
    
    if user_id != game_data["admin_id"]:
        # Different messages for complete and skip buttons
        if action == "complete":
            await query.answer("Only the admin can verify task completion!")
        else:  # skip
            await query.answer("Only the admin can skip the task!")
        return
    
    current_player = game_data["current_player"]
    
    try:
        if action == "complete":
            game_data["scores"][current_player] += 1
            await query.message.edit_text(
                f"Task completed! Current score: {game_data['scores'][current_player]}",
                reply_markup=None
            )
        else:  # skip
            # First answer the callback query
            await query.answer("Task skipped!")
            # Then edit the message with new text
            try:
                await query.message.edit_text(
                    "Task skipped! Moving to next player...",
                    reply_markup=None
                )
            except Exception as e:
                # If edit fails, send a new message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="Task skipped! Moving to next player..."
                )
        
        # Select next player
        await select_next_player(update, context)
        
    except Exception as e:
        print(f"Error in handle_completion: {e}")
        # If there's an error, still try to move to next player
        await select_next_player(update, context)

async def show_scores(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if chat_id not in game.games:
        await update.message.reply_text("No active game!")
        return
    
    game_data = game.games[chat_id]
    game_name = game_data["game_name"]
    scores = game_data["scores"]
    
    score_text = f"📊 *{game_name}* - Current Scores:\n\n"
    # Sort players by score
    sorted_players = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    for player_id, score in sorted_players:
        try:
            user = await context.bot.get_chat_member(chat_id, player_id)
            username = user.user.username or user.user.first_name
            score_text += f"• {username}: {score} points\n"
        except:
            score_text += f"• Player{player_id}: {score} points\n"
    
    await update.message.reply_text(score_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🎮 *Truth or Dare Bot Commands*

*How to Join:*
• Click the Join button when a new game starts
• Use /add to join the game yourself
• Wait for admin to add you with `/add @username`
• You must be in the group to be added

*How to Play:*
1\\. Use /newgame to start a new game session
2\\. Players join using the button or /add
3\\. Admin starts the game with /startgame
4\\. Follow the bot's instructions for Truth or Dare
5\\. Admin can stop the game anytime with /stop

*Rules:*
• Minimum 2 players required
• Only group admin can verify task completion
• Only selected player can choose Truth or Dare
• Points are awarded for completed tasks
• Changing task will deduct 1 point
• Players can leave using /remove

*Game Features:*
• Unique game IDs for tracking
• Random game names
• Score tracking
• Task changing option \\(\\-1 point\\)
• Admin controls

*Available Commands:*
• /newgame \\- Start a new game
• /stop \\- Stop current game \\(admin\\)
• /help \\- Show this message
• /add \\- Join the game
• /remove \\- Leave the game
• /startgame \\- Begin playing \\(admin\\)
• /scores \\- View scoreboard

For any issues or feedback, contact: [@ReachMateSR96\\_bot](https://t.me/ReachMateSR96_bot)"""

    try:
        await update.message.reply_text(
            help_text,
            parse_mode='MarkdownV2',
            disable_web_page_preview=True
        )
    except Exception as e:
        # Fallback without formatting if Markdown parsing fails
        await update.message.reply_text(
            help_text.replace('*', '').replace('_', '').replace('\\', ''),
            parse_mode=None
        )

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Sorry, I didn't understand that command. 🤔\n"
        "Use /help to see available commands!"
    )

# Add error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')
    try:
        if update and update.callback_query:
            await update.callback_query.answer(
                "An error occurred. Please try again.",
                show_alert=True
            )
        elif update and update.effective_message:
            await update.effective_message.reply_text(
                "Sorry, an error occurred. Please try again or use a different command."
            )
    except Exception as e:
        print(f"Error in error_handler: {e}")

async def stop_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Received /stop command")  # Debug statement
    if not await check_group_chat(update, context):
        return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if chat_id not in game.games:
        await update.message.reply_text("No active game to stop!")
        return
    
    game_data = game.games[chat_id]
    if user_id != game_data["admin_id"]:
        await update.message.reply_text("Only the admin can stop the game!")
        return
    
    game_name = game_data["game_name"]
    start_time = game_data["start_time"]
    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Capture end time

    # Show final scores before stopping
    score_text = f"🏁 *{game_name}* has ended!\n\n*Final Scores:*\n"
    sorted_players = sorted(game_data["scores"].items(), key=lambda x: x[1], reverse=True)
    
    for player_id, score in sorted_players:
        try:
            user = await context.bot.get_chat_member(chat_id, player_id)
            username = user.user.username or user.user.first_name
            score_text += f"• {username}: {score} points\n"
        except:
            score_text += f"• Player{player_id}: {score} points\n"
    
    # Include start and end times in the message
    score_text += f"\n🕒 Start Time: {start_time}\n🕔 End Time: {end_time}"
    
    await update.message.reply_text(score_text, parse_mode='Markdown')
    del game.games[chat_id]  # Remove the game data after stopping

async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_group_chat(update, context):
        return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if chat_id in game.games:
        if user_id != game.games[chat_id]["admin_id"]:
            await update.message.reply_text("Only the admin can start a new game!")
            return
        # End current game
        await stop_game(update, context)
    
    # Start new game
    game_name, game_id, start_time = game.init_game(chat_id, user_id)
    
    # Create join button
    keyboard = [[InlineKeyboardButton("Join Game 🎮", callback_data="join_game")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎮 {game_name}\n"
        f"📋 Game ID: {game_id}\n"
        f"⏰ Started: {start_time}\n\n"
        "Players can join by:\n"
        "1️⃣ Clicking the Join button below\n"
        "2️⃣ Using /add command\n"
        "3️⃣ Being added by admin using: /add @username\n\n"
        "📜 Rules:\n"
        "• Minimum 2 players needed to start\n"
        "• Only admin can verify task completion\n"
        "• Changing task will deduct 1 point\n"
        "• Points are awarded for completed tasks\n"
        "• Players can leave using /remove",
        reply_markup=reply_markup
    )

async def handle_join_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        if not query:
            return
            
        chat_id = query.message.chat_id
        user_id = query.from_user.id
        username = query.from_user.username or query.from_user.first_name
        
        if chat_id not in game.games:
            await query.answer("No active game to join!")
            return
        
        game_data = game.games[chat_id]
        game_name = game_data["game_name"]
        
        # Check if player is already in game
        if user_id in game_data["players"]:
            await query.answer("You're already in the game!")
            return
        
        # Add player to game
        game_data["players"].append(user_id)
        game_data["scores"][user_id] = 0
        
        # Send success message without Markdown
        await query.answer("Successfully joined the game!")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ {game_name}\n\n"
                 f"Welcome {username}! You've joined the game!\n"
                 f"Current players: {len(game_data['players'])}"
        )
        
    except Exception as e:
        print(f"Error in handle_join_button: {e}")
        if update.callback_query:
            await query.answer(
                "Error joining game. Please try using /add command instead.",
                show_alert=True
            )

def main():
    # Read the bot token from the environment variable
    BOT_TOKEN = os.getenv('BOT_TOKEN')

    if not BOT_TOKEN:
        raise ValueError("No BOT_TOKEN found. Set it as an environment variable.")

    # Continue with bot setup and execution
    application = Application.builder().token(BOT_TOKEN).build()

    # Add your bot's handlers and start logic here
    print("Bot is running...")
    if __name__ == "__main__":
    main()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("newgame", new_game))
    application.add_handler(CommandHandler("stop", stop_game))
    application.add_handler(CommandHandler("add", add_player))
    application.add_handler(CommandHandler("remove", remove_player))
    application.add_handler(CommandHandler("startgame", start_game))
    application.add_handler(CommandHandler("scores", show_scores))
    application.add_handler(CommandHandler("help", help_command))
    
    # Make sure join_game handler is before the other callback handlers
    application.add_handler(CallbackQueryHandler(handle_join_button, pattern="^join_game$"))
    application.add_handler(CallbackQueryHandler(handle_choice, pattern="^(truth|dare)$"))
    application.add_handler(CallbackQueryHandler(handle_change_task, pattern="^change_task$"))
    application.add_handler(CallbackQueryHandler(handle_completion, pattern="^(complete|skip)$"))
    
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    application.run_polling()

