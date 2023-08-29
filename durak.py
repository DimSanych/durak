from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import CallbackContext
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
import logging
logging.basicConfig(level=logging.ERROR)  # Глобальный уровень логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Уровень логирования только для вашего логгера
import asyncio




#Управление ботом
async def start(update, context):
    await update.message.reply_text("Привет! Я бот для игры в Дурака. Напиши /help, чтобы узнать, как играть.")

async def help_command(update, context):
    await update.message.reply_text("Чтобы начать игру, напиши /play. Для просмотра правил напиши /rules.")

async def play(update, context):
    await join_game(update, context)
    # Здесь будет логика начала игры
    pass

async def rules(update, context):
    rules_text = """
    Правила игры в Дурака:
    ...
    """
    await update.message.reply_text(rules_text)

# Список игроков, которые хотят играть
players = {}

#Игровые переменные
suits = ["spades", "clubs", "diamonds", "hearts"]
ranks_36 = ["6", "7", "8", "9", "10", "jack", "queen", "king", "ace"]
ranks_52 = ["2", "3", "4", "5"] + ranks_36

suit_to_emoji = {
    "diamonds": "♦️",
    "spades": "♠️",
    "hearts": "♥️",
    "clubs": "♣️"
}

rank_to_emoji = {
    "ace": "🅰️",
    "2": "2️⃣",
    "3": "3️⃣",
    "4": "4️⃣",
    "5": "5️⃣",
    "6": "6️⃣",
    "7": "7️⃣",
    "8": "8️⃣",
    "9": "9️⃣",
    "10": "🔟",
    "jack": "👮🏻",
    "queen": "👸🏻",
    "king": "🤴🏻"
}


#игровая колода
def create_deck(deck_type="36", number_of_decks=1):
    if deck_type == "36":
        base_deck = [{"suit": suit, "rank": rank} for suit in suits for rank in ranks_36]
    elif deck_type == "52":
        base_deck = [{"suit": suit, "rank": rank} for suit in suits for rank in ranks_52]
    else:
        raise ValueError("Invalid deck type. Choose either '36' or '52'.")
    
    return base_deck * number_of_decks

# Перетасовка колоды
def shuffle_deck(deck):
    random.shuffle(deck)
    return deck

# Определение козыря
def determine_trump(deck):
    trump_card = deck[-1]
    return trump_card['suit']

# Раздача карт игрокам
def deal_cards(players, deck):
    for player in players:
        player['hand'] = []

        # Раздаем каждому игроку по 6 карт
        for _ in range(4):
            card = deck.pop()
            player['hand'].append(card)

    return players, deck

# Определение игрока с наименьшим козырем
def determine_first_player(players_list, trump_suit):
    # Сортируем игроков по наименьшему козырю в их руке
    players_list.sort(key=lambda player: min([rank_to_emoji[card['rank']] for card in player['hand'] if card['suit'] == trump_suit], default="🤴🏻"))
    return players_list


# Отправка карт игрокам
async def send_cards_to_players(players_list, context: CallbackContext):
    for player in players_list:
        hand_emoji = " ".join([suit_to_emoji[card['suit']] + rank_to_emoji[card['rank']] for card in player['hand']])
        
        # Генерируем меню с картами
        cards_menu = generate_cards_menu(player['hand'])
        
        # Генерируем меню действий
        actions_menu = generate_actions_menu(player['status'])
        
        # Объединяем два меню в одно
        combined_menu = cards_menu.inline_keyboard + actions_menu.inline_keyboard
        
        # Отправляем сообщение с объединенным меню
        await context.bot.send_message(chat_id=player['id'], text=f"Твои карты: {hand_emoji}", reply_markup=InlineKeyboardMarkup(combined_menu))



#Меню карт игрока
def generate_cards_menu(player_hand):
    keyboard = []
    row = []
    for card in player_hand:
        card_emoji = suit_to_emoji[card['suit']] + rank_to_emoji[card['rank']]
        button = InlineKeyboardButton(card_emoji, callback_data=f"card_{card['suit']}-{card['rank']}")
        row.append(button)
        if len(row) == 6:  # После каждых 6 карт начинаем новый ряд
            keyboard.append(row)
            row = []
    if row:  # Добавляем оставшиеся карты, если их меньше 6
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)



#Меню действий у игрока
def generate_actions_menu(player_status):
    if player_status == "Attacking":
        buttons = [
            InlineKeyboardButton("Походить", callback_data="action_attack")
        ]
    elif player_status == "Defending":
        buttons = [
            InlineKeyboardButton("Отбиться", callback_data="action_defend"),
            InlineKeyboardButton("Взять", callback_data="action_take"),
            InlineKeyboardButton("Перевести", callback_data="action_transfer")
        ]
    else:  # Idle
        buttons = [
            InlineKeyboardButton("Подкинуть", callback_data="action_throw_in")
        ]
    
    keyboard = [buttons]  # Теперь все кнопки действий находятся в одном ряду
    return InlineKeyboardMarkup(keyboard)




# Функция для создания текста игрового стола
def generate_game_table(chat_id, deck, trump_suit):
    # Получаем текущий порядок хода
    current_order = players[chat_id]
    
    # Информация о колоде и козыре
    cards_left = len(deck)
    trump_card = suit_to_emoji[trump_suit] + rank_to_emoji[deck[-1]['rank']]
    
    # Информация о порядке хода
    order_info = "\n".join([f"{player['name']} - 🃏{len(player['hand'])}" for player in current_order])
    
    # Информация о текущем ходе
    current_player = current_order[0]['name']
    next_player = current_order[1]['name']
    
    # Собираем все вместе
    table = f"🃏{cards_left} | Козырь: {trump_card} | Ход: {current_player} ➡️ {next_player}\n\n"
    table += "Порядок хода:\n"
    table += order_info
    
    # Здесь можно добавить информацию о картах на столе, если они есть
    # (например, если игроки уже начали ходить)
    
    return table

#Выводим игровой стол
async def update_game_table_message(update: Update, context: CallbackContext, chat_id, deck, trump_suit):
    # Генерируем игровой стол
    table_message = generate_game_table(chat_id, deck, trump_suit)
    
    # Отправляем или редактируем сообщение с игровым столом
    # Здесь мы предполагаем, что у вас уже есть переменная для хранения ID сообщения с игровым столом.
    # Если это не так, вы можете добавить ее.
    if 'table_message_id' in context.user_data:
        await context.bot.edit_message_text(chat_id=chat_id, message_id=context.user_data['table_message_id'], text=table_message)
    else:
        sent_message = await update.message.reply_text(table_message)
        context.user_data['table_message_id'] = sent_message.message_id

async def process_turn(update: Update, context: CallbackContext, chat_id, deck, trump_suit, action=None):
    # Получаем текущий порядок хода
    current_order = players[chat_id]
    
    # Обновляем игровой стол
    await update_game_table_message(update, context, chat_id, deck, trump_suit)
    
    
    # Передаем ход следующему игроку
    current_player = current_order.pop(0)
    current_order.append(current_player)
    
    # Обновляем порядок хода
    players[chat_id] = current_order
    
    # Отправляем сообщение с обновленным игровым столом
    # (здесь будет код для отправки сообщения с игровым столом)
    
    # Проверяем условия окончания раунда или игры
    # (здесь будет код для проверки условий окончания раунда или игры)


# Функция для обновления порядка хода
def update_turn_order(players_order):
    # Перемещаем текущего игрока в конец списка
    current_player = players_order.pop(0)
    players_order.append(current_player)
    return players_order

#Присоединение к игре
async def join_game(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat_id = update.message.chat_id

    if chat_id not in players:
        players[chat_id] = []

    # Проверяем, не присоединился ли игрок уже
    for player in players[chat_id]:
        if player['id'] == user.id:
            await update.message.reply_text(f"{user.first_name}, ты уже в игре!")
            return

    players[chat_id].append({
        'id': user.id,
        'name': user.first_name,
        'message': update.message,  # добавьте эту строку
        'status': 'Idle'  # начальный статус

    })

    await update.message.reply_text(f"{user.first_name} присоединился к игре!")

#Просмотр списка игроков
async def list_participants(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if chat_id not in players or not players[chat_id]:
        await update.message.reply_text("В игре пока нет участников.")
        return

    players_list = "\n".join([player['name'] for player in players[chat_id]])
    await update.message.reply_text(f"Участники игры:\n{players_list}")

#Запуск игры
async def go(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id

    if chat_id not in players:
        await update.message.reply_text("Игра еще не началась!")
        return

    if len(players[chat_id]) < 2:
        await update.message.reply_text("Нельзя начать игру в одиночку!")
        return
    
    # Создаем колоду, перетасовываем и раздаем карты
    deck = shuffle_deck(create_deck("36"))  # или "52" в зависимости от выбранного типа колоды
    players[chat_id], deck = deal_cards(players[chat_id], deck)
    
    # Определение козыря
    trump_suit = determine_trump(deck)

    # Определение игрока с наименьшим козырем и порядка хода
    players_order = determine_first_player(players[chat_id], trump_suit)
    random.shuffle(players_order[1:])  # Перемешиваем порядок остальных игроков

    # Устанавливаем статусы
    players_order[0]['status'] = 'Attacking'
    players_order[1]['status'] = 'Defending'
    for player in players_order[2:]:
        player['status'] = 'Idle'
    #Обновляем статус игроков
    players[chat_id] = players_order

    # Отправка карт игрокам
    await send_cards_to_players(players[chat_id], context)

    await process_turn(update, context, chat_id, deck, trump_suit)


# Команда прекращения игры
async def stop(update: Update, context: CallbackContext) -> None:
    players.clear()
    await update.message.reply_text("Игра завершена!")



# Игровой процесс





# Запуск бота

def main() -> None:
    application = Application.builder().token('6189771635:AAHEZ83SLCJ8VqBwF6aF3OtLcAHU7jcmwUc').build()

   
    # Обработчики команд
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('play', play))
    application.add_handler(CommandHandler('rules', rules))
    application.add_handler(CommandHandler('go', go))
    application.add_handler(CommandHandler('stop', stop))
    application.add_handler(CommandHandler('list', list_participants))   

    



    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    
    main()
