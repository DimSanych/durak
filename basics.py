


# Функция для создания текста игрового стола
def generate_game_table(chat_id, deck, trump_suit):
    from durak import suit_to_emoji, rank_to_emoji, players
    from durak import go

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