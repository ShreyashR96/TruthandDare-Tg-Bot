import random
import telepot

TOKEN = 'BOT TOKEN'
bot = telepot.Bot(TOKEN)

def handle_messages(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)

    if content_type == 'text':
        command = msg['text'].lower()
        user_id = msg['from']['id']

        if command == '/startgame':
            start_game(chat_id)
        elif command == '/stopgame':
            stop_game(chat_id)
        elif command.startswith('/addplayer'):
            add_player(chat_id, user_id, command.split(' ')[1])
        elif command == '/truthordare':
            truth_or_dare(chat_id)


def start_game(chat_id, players=[]):
    # Initialize game state or variables
    game_state = {
        'chat_id': chat_id,
        'players': players,
        'game_started': True,
    }

    # Send a message to the group indicating the start of the game
    message = "🎉 The Truth or Dare game has started! 🎉\n\n"
    message += "Players:\n"
    for player in players:
        message += f" - {player}\n"

    bot.sendMessage(chat_id, message)

    # Store the game state (you might want to use a database for a persistent solution)
    # For simplicity, we'll just store it in a global variable
    global game_states
    game_states[chat_id] = game_state
    pass

def stop_game(chat_id):
    # Get the game state
    game_state = game_states.get(chat_id)

    if game_state and game_state['game_started']:
        # Send a closing message to the group
        message = "🏁 The Truth or Dare game has ended! Thanks for playing! 🏁"
        bot.sendMessage(chat_id, message)

        # Clear the game state for this chat_id
        del game_states[chat_id]

    else:
        # Inform the group that there was no active game
        message = "There is no active game to stop."
        bot.sendMessage(chat_id, message)
    pass


def add_player(chat_id, user_id, username):
    # Get the game state
    game_state = game_states.get(chat_id)

    if game_state and game_state['game_started']:
        # Check if the player is already in the game
        if username not in game_state['players']:
            # Add the new player to the list
            game_state['players'].append(username)

            # Send a notification about the new player
            message = f"👤 {username} has joined the game! 👤"
            bot.sendMessage(chat_id, message)
        else:
            # Inform the group that the player is already in the game
            message = f"{username} is already in the game."
            bot.sendMessage(chat_id, message)
    else:
        # Inform the group that there is no active game
        message = "There is no active game to join."
        bot.sendMessage(chat_id, message)
    pass



def truth_or_dare(chat_id):
    # Get the game state
    game_state = game_states.get(chat_id)

    if game_state and game_state['game_started']:
        # Check if there are enough players to play
        if len(game_state['players']) >= 2:
            # Randomly select a player
            selected_player = random.choice(game_state['players'])

            # Randomly choose between truth and dare
            truth_or_dare_choice = random.choice(['Truth', 'Dare'])

            # Fetch a truth or dare prompt from your database (replace with your logic)
            prompt = fetch_truth_or_dare_from_database(truth_or_dare_choice)

            # Send the truth or dare prompt to the group
            message = f"🤔 {selected_player}, choose {truth_or_dare_choice.lower()}! 🤔\n\n{prompt}"
            bot.sendMessage(chat_id, message)
        else:
            # Inform the group that there are not enough players to play
            message = "Not enough players to play Truth or Dare. Add more players to the game."
            bot.sendMessage(chat_id, message)
    else:
        # Inform the group that there is no active game
        message = "There is no active game to play Truth or Dare."
        bot.sendMessage(chat_id, message)

def fetch_truth_or_dare_from_database(choice):
    # Implement your logic to fetch a truth or dare prompt from your database
    # Replace this with your actual implementation
    if choice == 'Truth':
        return "What is the most embarrassing thing that has happened to you?"
    elif choice == 'Dare':
        return "Dance for 30 seconds without music."
    
    
def remove_player(chat_id, username):
    # Get the game state
    game_state = game_states.get(chat_id)

    if game_state and game_state['game_started']:
        # Check if the player is in the game
        if username in game_state['players']:
            # Remove the player from the list
            game_state['players'].remove(username)

            # Send a notification about the removed player
            message = f"❌ {username} has been removed from the game. ❌"
            bot.sendMessage(chat_id, message)
        else:
            # Inform the group that the player is not in the game
            message = f"{username} is not in the game."
            bot.sendMessage(chat_id, message)
    else:
        # Inform the group that there is no active game
        message = "There is no active game to remove a player from."
        bot.sendMessage(chat_id, message)


# Assume game_states is a global dictionary storing the state of each ongoing game
game_states = {}

pass

bot.message_loop(handle_messages)

while True:
    pass  # Keep the program running

