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

# Глобальный словарь для хранения данных игр
games_data = {}

def initialize_game(chat_id):
    # Ваша логика инициализации игры
    game_data = {
    
            'chat_id': chat_id,
            'players': [],
            'deck': [],
            'trump_suit': None,
            'table_cards': [],
            'current_turn': None,
            'game_status': 'not_started'
        }
    return game_data   





# Список мастей и рангов для создания колоды карт.
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

# Определяем иерархию рангов для 52-карточной колоды
rank_hierarchy = {
    "2": 1,
    "3": 2,
    "4": 3,
    "5": 4,
    "6": 5,
    "7": 6,
    "8": 7,
    "9": 8,
    "10": 9,
    "jack": 10,
    "queen": 11,
    "king": 12,
    "ace": 13
}

# Добавляет или убирает эмодзи ✅ из текста карты.
def toggle_card_selection(card_text):
    if card_text.startswith("✅"):
        print(f"Original card text: {card_text}")
        return card_text[2:]  # Убираем эмодзи, если карта уже выделена
    else:
        print(f"Selecting card: {card_text}")  # Добавлено для отладки
        return f"✅ {card_text}"  # Добавляем эмодзи, если карта не выделена

#игровая колода
def create_deck(deck_type="36", number_of_decks=1):
    if deck_type == "36":
        base_deck = [{"suit": suit, "rank": rank} for suit in suits for rank in ranks_36]
    elif deck_type == "52":
        base_deck = [{"suit": suit, "rank": rank} for suit in suits for rank in ranks_52]
    else:
        raise ValueError("Invalid deck type. Choose either '36' or '52'.")
    
    return base_deck * number_of_decks

# Функция для перетасовки колоды
def shuffle_deck(deck):
    random.shuffle(deck)  # Используем функцию shuffle из модуля random для перетасовки колоды
    return deck  # Возвращаем перетасованную колоду

# Функция для определения козыря
def determine_trump(deck):
    trump_card = deck[-1]  # Берем последнюю карту из колоды как козырную
    return trump_card['suit']  # Возвращаем масть козырной карты

# Функция для раздачи карт игрокам
def deal_cards(players, deck):
    for player in players:  # Проходим по каждому игроку
        player['hand'] = []  # Создаем пустой список для карт игрока

        # Раздаем каждому игроку по 6 карт
        for _ in range(6):
            card = deck.pop()  # Берем карту из верха колоды
            player['hand'].append(card)  # Добавляем карту в руку игрока

    return players, deck  # Возвращаем обновленный список игроков и колоду

# Определение игрока с наименьшим козырем
def determine_first_player(players_list, trump_suit):
    # Сортируем игроков по наименьшему козырю в их руке
    players_list.sort(key=lambda player: min([rank_to_emoji[card['rank']] for card in player['hand'] if card['suit'] == trump_suit], default="🤴🏻"))
    return players_list # Возвращаем отсортированный список игроков


# Функция для отправки карт игрокам
async def send_cards_to_players(chat_id, context: CallbackContext) -> None:
    game_data = games_data[chat_id]  # Получаем данные текущей игры из глобального словаря games_data
    for player in game_data['players']:  # Проходим по каждому игроку
        # Преобразуем карты игрока в строку с эмодзи
        hand_emoji = " ".join([suit_to_emoji[card['suit']] + rank_to_emoji[card['rank']] for card in player['hand']])
        # Генерируем меню с картами
        cards_menu = generate_cards_menu(player['hand'])
        # Генерируем меню действий
        actions_menu = generate_actions_menu(player['status'], game_data['table_cards'])
        # Объединяем два меню в одно
        if actions_menu:
            combined_menu = cards_menu.inline_keyboard + actions_menu.inline_keyboard
        else:
            combined_menu = cards_menu.inline_keyboard
        
        # Отправляем сообщение с объединенным меню
        table_message = generate_game_table(game_data)
        await context.bot.send_message(chat_id=player['id'], text=table_message, reply_markup=InlineKeyboardMarkup(combined_menu))





# Функция для генерации меню карт игрока
def generate_cards_menu(player_hand):
    keyboard = []  # Создаем пустой список для клавиатуры
    row = []  # Создаем пустой список для ряда кнопок
    for card in player_hand:  # Проходим по каждой карте в руке игрока
        # Преобразуем карту в эмодзи
        card_emoji = suit_to_emoji[card['suit']] + rank_to_emoji[card['rank']]
        # Создаем кнопку с эмодзи карты
        button = InlineKeyboardButton(card_emoji, callback_data=f"card_{card['suit']}-{card['rank']}")
        row.append(button)  # Добавляем кнопку в ряд
        if len(row) == 4:  # После каждых 4 карт начинаем новый ряд
            keyboard.append(row)
            row = []
    if row:  # Добавляем оставшиеся карты, если их меньше 4
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)  # Возвращаем клавиатуру с кнопками



#Меню действий у игрока
def generate_actions_menu(player_status, table_cards=None):
    if player_status == "Attacking":
        buttons = [
            InlineKeyboardButton("Атаковать", callback_data="action_attack")
        ]
    elif player_status == "Defending":
        if table_cards:
            buttons = [
                InlineKeyboardButton("Отбиться", callback_data="action_defend"),
                InlineKeyboardButton("Взять", callback_data="action_take"),
                InlineKeyboardButton("Перевести", callback_data="action_transfer")
            ]
        else:
            return None
    else:  # Idle
        if table_cards:
            buttons = [
                InlineKeyboardButton("Подкинуть", callback_data="action_throw_in")
            ]
        else:
            return None
    keyboard = [buttons]  # Теперь все кнопки действий находятся в одном ряду
    return InlineKeyboardMarkup(keyboard)




# Функция для создания текста игрового стола
def generate_game_table(game_data):
    # Получаем текущий порядок хода
    current_order = game_data['players']
    deck = game_data['deck']
    trump_suit = game_data['trump_suit']

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

    # Информация о картах на столе
    table_cards = game_data['table_cards']
    table += "\n\nНа столе:\n"
    table += " ".join([f"{suit_to_emoji[card['suit']]}{rank_to_emoji[card['rank']]}" for card in table_cards])

    return table


# Функция для обновления сообщения с игровым столом
async def update_game_table_message(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    game_data = games_data[chat_id]  # Получаем данные текущей игры из глобального словаря games_data

    # Генерируем игровой стол
    table_message = generate_game_table(game_data)

    # Отправляем или редактируем сообщение с игровым столом
    if 'table_message_id' in context.user_data:  # Проверяем, есть ли уже сообщение с игровым столом
        await context.bot.edit_message_text(chat_id=chat_id, message_id=context.user_data['table_message_id'], text=table_message)  # Если есть, редактируем его
    else:
        sent_message = await update.message.reply_text(table_message)  # Если нет, отправляем новое сообщение
        context.user_data['table_message_id'] = sent_message.message_id  # Сохраняем ID нового сообщения в user_data

async def update_player_game_table(update: Update, context: CallbackContext, game_data: dict) -> None:
    # Генерируем игровой стол
    table_message = generate_game_table(game_data)

    for player in game_data['players']:
        player_id = player['id']
        
        # Проверяем, отправляли ли мы уже игроку сообщение с игровым столом
        if player_id in context.user_data and 'table_message_id' in context.user_data[player_id]:
            # Если отправляли, обновляем это сообщение
            await context.bot.edit_message_text(chat_id=player_id, message_id=context.user_data[player_id]['table_message_id'], text=table_message)
        else:
            # Если не отправляли, отправляем новое сообщение и сохраняем его ID
            sent_message = await context.bot.send_message(chat_id=player_id, text=table_message)
            if player_id not in context.user_data:
                context.user_data[player_id] = {}
            context.user_data[player_id]['table_message_id'] = sent_message.message_id



# Функция присоединения к игре и формирования списка игроков

async def join_game(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat_id = update.message.chat_id
    chat_type = update.message.chat.type

    if chat_type not in ["group", "supergroup"]:
        await update.message.reply_text("Используйте команду в группе")
        return

    # Инициализируем игру, если она еще не начата для этого чата
    if chat_id not in games_data:
        games_data[chat_id] = initialize_game(chat_id)
    game = games_data[chat_id]

    # Если игра уже началась, новые игроки не могут присоединиться
    if game['game_status'] == 'started':
        await update.message.reply_text("Игра уже началась. Вы не можете присоединиться сейчас.")
        return

    # Проверяем, не присоединился ли игрок уже
    for player in game['players']:
        if player['id'] == user.id:
            await update.message.reply_text(f"{user.first_name}, ты уже в игре!")
            return

    game['players'].append({
        'id': user.id,
        'name': user.first_name,
        'hand': [],
        'status': 'Idle'
    })

    await update.message.reply_text(f"{user.first_name} присоединился к игре!")








# Просмотр списка игроков
async def list_participants(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id  # Получаем ID чата (группы)
    
    # Получаем текущую игру из глобального словаря games_data
    game = games_data.get(chat_id)

    # Проверяем, была ли игра инициализирована и есть ли игроки
    if not game or not game['players']:
        await update.message.reply_text("В игре пока нет участников.")
        return

    players_list = "\n".join([player['name'] for player in game['players']])  # Создаем список имен игроков
    await update.message.reply_text(f"Участники игры:\n{players_list}")



# Запуск игры
async def go(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id  # Получаем ID чата (группы)
    
    # Получаем текущую игру из глобального словаря games_data
    game = games_data.get(chat_id)

    # Если игра еще не была инициализирована, инициализируем ее
    if not game:
        game = initialize_game(chat_id)
        games_data[chat_id] = game

    # Проверяем, была ли игра уже начата ранее
    if game['game_status'] == 'started':
        await update.message.reply_text("Игра уже началась!")
        return

    # Проверяем, есть ли достаточно игроков для начала игры
    if len(game['players']) < 2:
        await update.message.reply_text("Нельзя начать игру в одиночку!")
        return

    # Создаем колоду, перетасовываем и раздаем карты
    deck = shuffle_deck(create_deck("36"))  # Создаем и перетасовываем колоду из 36 карт
    game['deck'] = deck
    game['players'], deck = deal_cards(game['players'], deck)  # Раздаем карты игрокам

    # Определение козыря
    game['trump_suit'] = determine_trump(deck)  # Определяем козырь

    # Определение игрока с наименьшим козырем и порядка хода
    players_order = determine_first_player(game['players'], game['trump_suit'])  # Определяем порядок хода игроков
    random.shuffle(players_order[1:])  # Перемешиваем порядок остальных игроков

    # Устанавливаем статусы игроков
    players_order[0]['status'] = 'Attacking'  # Первый игрок атакует
    players_order[1]['status'] = 'Defending'  # Второй игрок защищается
    for player in players_order[2:]:
        player['status'] = 'Idle'  # Остальные игроки ожидают своего хода
    game['players'] = players_order  # Обновляем порядок хода игроков в словаре game

    # Отправка карт игрокам и определение порядка хода
    await send_cards_to_players(chat_id, context)  # Отправляем карты игрокам
    await update_game_table_message(update, context)  # Обновляем игровой стол
    # Обновляем игровой стол у каждого игрока
    chat_id = update.message.chat_id

    # Для отладки: вывод данных игроков в консоли
    for player in game['players']:
        print(player)

    game['current_turn'] = game['players'][0]['id']  # Устанавливаем текущий ход на атакующего игрока
    game['game_status'] = 'started'  # Обновляем статус игры на "started"
    # Для отладки: вывод данных игры в консоли
    print("Game data:", game)

    


#Пока не используется
def start_round(players_order, deck):
    # Дополнительная раздача карт, если на руке меньше 6
    for player in players_order:
        while len(player['hand']) < 6 and deck:
            player['hand'].append(deck.pop())
    
    # Устанавливаем статусы
    players_order[0]['status'] = 'Attacking'
    players_order[1]['status'] = 'Defending'
    for player in players_order[2:]:
        player['status'] = 'Idle'

# Обновление статусов и конец раунда
def end_round(players_order, successful_defense):
    if successful_defense:
        # Перемещаем атакующего игрока в конец списка
        players_order.append(players_order.pop(0))
    else:
        # Перемещаем защищающегося игрока в конец списка
        players_order.append(players_order.pop(1))
    # ... (обновление статусов, и т.д.)



# Команда прекращения игры
async def stop(update: Update, context: CallbackContext) -> None:
    players.clear()
    await update.message.reply_text("Игра завершена!")


async def callback_query_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    query_data = query.data
    user_chat_id = query.message.chat_id  # ID чата с пользователем

    if query.data.startswith('card_'):
        # Получаем текущую клавиатуру
        current_keyboard = query.message.reply_markup.inline_keyboard

        # Создаем новую клавиатуру, изменяя текст нужной кнопки
        new_keyboard = []
        selected_cards = []
        for row in current_keyboard:
            new_row = []
            for button in row:
                if button.callback_data == query.data:
                    new_text = toggle_card_selection(button.text)
                    new_button = InlineKeyboardButton(new_text, callback_data=button.callback_data)
                else:
                    new_button = button
                
                # Проверяем, содержит ли текст кнопки эмодзи "✅"
                if "✅" in new_button.text:
                    card_data = new_button.callback_data.split("_")[1]  # Получаем данные карты из callback_data
                    selected_cards.append(card_data)  # Добавляем карту в список выбранных

                new_row.append(new_button)
            new_keyboard.append(new_row)
        # Обновляем сообщение с новой клавиатурой
        reply_markup = InlineKeyboardMarkup(new_keyboard)
        await query.edit_message_reply_markup(reply_markup=reply_markup)
        
        # Сохраняем список выбранных карт в context.user_data
        context.user_data['selected_cards'] = selected_cards

    elif query_data == "action_attack":
    # Получаем выбранные карты из context.user_data
        selected_cards = context.user_data.get('selected_cards', [])
    
        # Преобразуем в словарь
        selected_cards = [{'suit': card_str.split('-')[0], 'rank': card_str.split('-')[1]} for card_str in selected_cards]
    
        # Проверяем, имеют ли все выбранные карты одинаковый ранг
        if not check_cards_same_value(selected_cards):
            await query.message.reply_text("Выберите карты одного значения.")
            return

        # Если все хорошо, отправляем подсказку пользователю
        await query.message.reply_text("Можно атаковать выбранными картами")

        group_chat_id = context.user_data.get('group_chat_id', None)


        # Получаем остальные необходимые данные
        table_cards = context.user_data.get('table_cards', [])
        deck = context.user_data.get('deck', [])
        # Получаем игрока по его ID
        player = next((p for p in players[group_chat_id] if p['id'] == query.from_user.id), None)

        # Если игрок найден, получаем trump_suit из его словаря
        if player:
            trump_suit = player.get('trump_suit', None)
        # Вызываем функцию атаки
        await handle_attack(update, context, user_chat_id, group_chat_id, selected_cards, table_cards, deck, trump_suit)


async def handle_attack(update: Update, context: CallbackContext, user_chat_id, group_chat_id, selected_cards, table_cards, deck, trump_suit):
    
    print("Debug: Inside handle_attack")  # Отладочный вывод
    
    

    # Удаляем выбранные карты из руки игрока
    # Получаем список всех игроков из всех групп
    all_players = [p for group in players.values() for p in group]


    print(f"Debug: All players: {all_players}")  # Отладочный вывод

    # Ищем игрока с нужным chat_id
    player = None
    for p in all_players:
        if p['id'] == update.callback_query.from_user.id:
            player = p
            break

    print(f"Debug: Found player: {player}")  # Отладочный вывод


    # Если игрок найден, продолжаем обработку
    player['hand'] = [card for card in player['hand'] if card not in selected_cards]
    
    print(f"Debug: Selected cards before extending table_cards: {selected_cards}")  # Отладочный вывод
    print(f"Debug: Table cards before extending: {table_cards}")  # Отладочный вывод
    
    # Добавляем выбранные карты на стол
    table_cards.extend(selected_cards)

    print(f"Debug: Table cards after extending: {table_cards}")  # Отладочный вывод

    # Сохраняем обновленный список карт на столе в context.user_data
    context.user_data['table_cards'] = table_cards
    
    # Получаем ID группового чата
    group_chat_id = player.get('group_chat_id', None)

    #Получаем козырь
    trump_suit = context.user_data.get('trump_suit', None)

    # Обновляем игровой стол
    await update_game_table_message(update, context, group_chat_id, deck, trump_suit, table_cards)
    
    # Создаем новую клавиатуру на основе оставшихся карт
    new_keyboard = generate_cards_menu(player['hand'])

    # Обновляем сообщение с новой клавиатурой
    reply_markup = InlineKeyboardMarkup(new_keyboard)
    await context.bot.edit_message_reply_markup(chat_id=user_chat_id, message_id=update.callback_query.message.message_id, reply_markup=reply_markup)

    # Отправляем сообщение, что атака успешно выполнена
    await update.callback_query.message.reply_text("Атака выполнена. Ход переходит к следующему игроку.")



def check_cards_same_value(selected_cards):
    if not selected_cards:
        return False  # Возвращаем False, если список пуст
    
    first_card_rank = selected_cards[0]['rank']  # Получаем ранг первой карты
    
    for card in selected_cards:
        if card['rank'] != first_card_rank:
            return False  # Возвращаем False, если ранг какой-либо карты отличается от первой
    
    return True  # Возвращаем True, если все карты имеют одинаковый ранг













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
    application.add_handler(CallbackQueryHandler(callback_query_handler))
    



    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    
    main()
