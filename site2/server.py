from flask import Flask, render_template, request, redirect, url_for, flash, session
from random import randint  
import random
from flask_session import Session
import sqlite3
from datetime import datetime
from flask_bcrypt import Bcrypt
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = 'your_secret_key'


app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

def get_db_connection():
    conn = sqlite3.connect('mydatabase.db')
    conn.row_factory = sqlite3.Row
    return conn
    
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('profile'))
    return render_template('index.html')


def get_balance(client_id):
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    cursor.execute("SELECT Balance FROM Clients WHERE ClientID = ?", (client_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result is not None:
        balance = result[0]
        return balance
    else:
        return 0  

def update_balance(client_id, new_balance):
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE Clients SET Balance = ? WHERE ClientID = ?", (new_balance, client_id))
    conn.commit()
    conn.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        raw_password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM Users WHERE login = ?", (login,))
        user = cursor.fetchone()
        
        if user and bcrypt.check_password_hash(user['password'], raw_password):
            session['user_id'] = user['id']
            flash('Вы успешно вошли в систему!', 'success')
            conn.close()
            return redirect(url_for('profile'))
        else:
            flash('Неверный логин или пароль. Попробуйте ещё раз.', 'danger')
            conn.close()
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Вы успешно вышли из системы.', 'success')
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if 'user_id' in session:

        conn = get_db_connection()
        cursor = conn.cursor()
        

        user_id = session['user_id']
        cursor.execute("SELECT * FROM Users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        conn.close()
        
        if user:
            return render_template('profile.html', username=user['login'])
    
    flash('Пожалуйста, войдите в систему для просмотра профиля.', 'warning')
    return redirect(url_for('login'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login = request.form['login']
        raw_password = request.form['password']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        birthdate = request.form['birthdate']
        contactinfo = request.form['contactinfo']
        balance = 0
        
        # Хешируем пароль
        password = bcrypt.generate_password_hash(raw_password).decode('utf-8')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM Users WHERE login = ?", (login,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash('Пользователь с таким логином уже существует. Выберите другой логин.', 'danger')
        else:
            cursor.execute("INSERT INTO Users (login, password) VALUES (?, ?)",
                           (login, password))
            
            user_id = cursor.lastrowid
            
            cursor.execute("INSERT INTO Clients (ClientID, FirstName, LastName, BirthDate, ContactInfo, Balance) VALUES (?, ?, ?, ?, ?, ?)",
                           (user_id, firstname, lastname, birthdate, contactinfo, balance))

            conn.commit()
            conn.close()
            
            flash('Регистрация успешно завершена!', 'success')
            return redirect(url_for('register'))
    
    return render_template('register.html')
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        birthdate = request.form['birthdate']
        contactinfo = request.form['contactinfo']
        balance = request.form['balance']
        balance = 0
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM Users WHERE login = ?", (login,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash('Пользователь с таким логином уже существует. Выберите другой логин.', 'danger')
        else:
            cursor.execute("INSERT INTO Users (login, password) VALUES (?, ?)",
                           (login, password))
            
            user_id = cursor.lastrowid
            
            cursor.execute("INSERT INTO Clients (ClientID, FirstName, LastName, BirthDate, ContactInfo, Balance) VALUES (?, ?, ?, ?, ?, ?)",
                           (user_id, firstname, lastname, birthdate, contactinfo, balance))

            conn.commit()
            conn.close()
            
            flash('Регистрация успешно завершена!', 'success')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/gamelist')
def gamelist():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM Games")
    games = cursor.fetchall()
    
    conn.close()

    return render_template('gamelist.html', games=games)

@app.route('/game/<int:game_id>')
def game(game_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Games WHERE GameID = ?", (game_id,))
    game = cursor.fetchone()
    conn.close()

    if game:
        return render_template('game.html', game=game)
    else:
        flash('Игра не найдена.', 'warning')
        return redirect(url_for('gamelist'))



        
@app.route('/play_coin_flip/<int:game_id>', methods=['GET', 'POST'])
def play_coin_flip(game_id):
    if request.method == 'POST':
        client_id = session['user_id']
        current_balance = get_balance(client_id)

        bet_amount = int(request.form['bet_amount'])
        user_choice = request.form['choice']  # Получаем выбор пользователя

        game_chance = get_game_chance(game_id)

        if bet_amount > current_balance:
            flash('У вас недостаточно средств для этой ставки.', 'error')
            return redirect(url_for('play_coin_flip', game_id=game_id))

        coin = random.choices([1, 2], weights=[game_chance, 100 - game_chance])[0]

        if (user_choice == 'eagle' and coin == 1) or (user_choice == 'tail' and coin == 2):
            result = 'Поздравляем! Вы выиграли!'
            new_balance = current_balance + bet_amount
        else:
            result = 'К сожалению, вы проиграли.'
            new_balance = current_balance - bet_amount

        update_balance(client_id, new_balance)

        conn = sqlite3.connect('mydatabase.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO CoinFlipGames (ClientID, Choice, CoinOutcome, Result) VALUES (?, ?, ?, ?)",
               (client_id, user_choice, coin, result))

        conn.commit()
        conn.close()

        flash(result, 'result')
        return render_template('coin_flip.html', balance=new_balance, result=result)

    return render_template('coin_flip.html', game_id=game_id)

def get_game_chance(game_id):
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    cursor.execute("SELECT WinChance FROM Games WHERE GameID = ?", (game_id,))
    result = cursor.fetchone()
    conn.close()

    if result is not None:
        return float(result[0])
    else:
        return 0.0

@app.route('/transactions', methods=['GET', 'POST'])
def transactions():
    if request.method == 'POST':
        client_id = session['user_id']
        transaction_type = request.form['transaction_type']
        amount = float(request.form['amount'])

        if amount <= 0:
            flash('Сумма должна быть больше нуля.', 'error')
        else:
            if transaction_type == 'deposit':
                current_balance = get_balance(client_id)
                new_balance = current_balance + amount
                update_balance(client_id, new_balance)

                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Transactions (ClientID, TransactionType, Amount, TransactionDate) VALUES (?, ?, ?, ?)",
                               (client_id, transaction_type, amount, datetime.now()))
                conn.commit()
                conn.close()

                flash(f'Средства в размере {amount} успешно зачислены на ваш баланс.', 'success')
            elif transaction_type == 'withdraw':
                current_balance = get_balance(client_id)
                if amount > current_balance:
                    flash('У вас недостаточно средств для вывода.', 'error')
                else:
                    new_balance = current_balance - amount
                    update_balance(client_id, new_balance)

                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO Transactions (ClientID, TransactionType, Amount, TransactionDate) VALUES (?, ?, ?, ?)",
                                   (client_id, transaction_type, amount, datetime.now()))
                    conn.commit()
                    conn.close()

                    flash(f'Средства в размере {amount} успешно выведены с вашего баланса.', 'success')

    return render_template('transactions.html')
###########################################################################################################################
# ЕБАНОЕ 21 СУКА
@app.route('/play_21')
def play_21():
    return redirect(url_for('place_bet'))


def get_game_data(game_id):
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM TwentyOneGames WHERE GameID=?", (game_id,))
    game_data = cursor.fetchone()
    conn.close()
    return game_data


@app.route('/place_bet', methods=['GET', 'POST'])
def place_bet():
    if request.method == 'POST':
        client_id = session['user_id']
        bet_amount = int(request.form['bet_amount'])
        
        # Создаем новую игру и получаем начальные карты
        player_hand, dealer_hand = create_new_game(client_id, bet_amount)
        session['current_game_id'] = get_user_current_game_id(session['user_id'])
        game_id=session['current_game_id']
        
        return render_template('21_play.html', player_hand=player_hand, dealer_hand=dealer_hand,game_id=game_id)
    
    return render_template('21_bet.html')


def get_user_current_game_id(client_id):
    conn = sqlite3.connect('mydatabase.db')  # Замените 'mydatabase.db' на имя вашей базы данных
    cursor = conn.cursor()
    
    # Выполняем SQL-запрос для выбора текущей игры пользователя
    cursor.execute("SELECT GameID FROM TwentyOneGames WHERE ClientID = ? AND Result = 'Игра началась'", (client_id,))
    
    # Получаем результат запроса
    game_id = cursor.fetchone()
    
    # Закрываем соединение с базой данных
    conn.close()
    
    # Если найдена активная игра для пользователя, возвращаем GameID, в противном случае возвращаем None
    if game_id:
        return game_id[0]
    else:
        return None



# Функция для создания новой игры "21"
def create_new_game(client_id, bet_amount):
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    
    # Создаем новую игру
    player_hand = [draw_card(), draw_card()]
    dealer_hand = [draw_card(), draw_card()]
    
    # Информацию о новой игре добавляем в базу данных
    cursor.execute("INSERT INTO TwentyOneGames (ClientID, BetAmount, PlayerHand, DealerHand, Result) VALUES (?, ?, ?, ?, ?)",
                   (client_id, bet_amount, str(player_hand), str(dealer_hand), 'Игра началась'))
    
    conn.commit()
    conn.close()
    
    return player_hand, dealer_hand

# Функция для извлечения случайной карты
def draw_card():
    return random.randint(1, 10)
# Роут для обработки действий игрока (взять карту или спасовать)


@app.route('/play_21_action', methods=['POST'])
def play_21_action():
    # Ваш код обработки действий игрока здесь
    client_id = session['user_id']

    # Вызываем функцию get_user_current_game_id для получения game_id
    game_id = get_user_current_game_id(client_id)

    # Получаем текущее состояние игры
    game_data = get_game_data(game_id)
    if game_data is not None:
        player_hand = eval(game_data[3])
    else:
        # Если game_data равно None, перенаправляем на game_list
        return redirect(url_for('gamelist'))
    dealer_hand = eval(game_data[4])
    result = game_data[5]
    
    action = request.form['action']
        
    if action == 'hit':
        # Игрок берет карту
        hit(player_hand,game_id)

        # Проверяем, не завершилась ли игра
        if sum(player_hand) >= 21:
            result, player_sum, dealer_sum = stand(player_hand, dealer_hand,game_id)
            update_game_data(game_id, player_hand, dealer_hand, result)
    elif action == 'stand':
        # Игрок завершает ход, идет ход дилера
        result, player_sum, dealer_sum = stand(player_hand, dealer_hand,game_id)
        update_game_data(game_id, player_hand, dealer_hand, result)
    elif action == 'finish':
        # Обработка завершения игры
        result = "Игра завершена досрочно."
        update_game_data(game_id, player_hand, dealer_hand, result)
        finish_game_session(game_id, player_hand, dealer_hand)


    return render_template('21_play.html', player_hand=player_hand, dealer_hand=dealer_hand, result=result, game_id=game_id)



@app.route('/finish_game/<int:game_id>', methods=['POST'])
def finish_game_session(game_id, player_hand, dealer_hand):
    # Получите результат и другие необходимые данные из формы
    result = 'Игра окончена. Вы проиграли.'
    
    # Обновите информацию о текущей игре в базе данных
    update_game_data(game_id, player_hand, dealer_hand, result)
    

    
    # Перенаправьте пользователя на страницу с играми
    return redirect(url_for('gamelist'))

# Другие маршруты и код приложения






# Функция для набора карты игроком
def hit(player_hand, game_id):
    # Получаем новую карту
    new_card = draw_card()
    
    # Добавляем новую карту в руку игрока
    player_hand.append(new_card)

    # Обновляем данные в базе данных
    game_data = get_game_data(game_id)
    player_hand_db = eval(game_data[3])
    player_hand_db.append(new_card)
    update_game_data(game_id, player_hand_db, eval(game_data[4]), game_data[5])




def stand(player_hand, dealer_hand, game_id):
    # Ход дилера
    while sum(dealer_hand) < 17:
        dealer_hand.append(draw_card())

    # Определение победителя
    player_sum = sum(player_hand)
    dealer_sum = sum(dealer_hand)
    
    if player_sum > 21:
        result = 'Игра окончена. Вы проиграли.'
    elif dealer_sum > 21 or player_sum == 21 or (player_sum > dealer_sum and player_sum <= 21):
        result = 'Игра окончена. Вы выиграли!'
    else:
        result = 'Игра окончена. Вы проиграли.'

    # Обновляем данные в базе данных
    update_game_data(game_id, player_hand, dealer_hand, result)

    return result, player_sum, dealer_sum


def update_game_data(game_id, player_hand, dealer_hand, result):
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()

    # Обновляем информацию о текущей игре в базе данных, включая значение Result
    cursor.execute("UPDATE TwentyOneGames SET PlayerHand=?, DealerHand=?, Result=? WHERE GameID=?",
                   (str(player_hand), str(dealer_hand), result, game_id))

    conn.commit()
    conn.close()















if __name__ == '__main__':
    app.run(debug=True)
