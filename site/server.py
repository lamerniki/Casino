from flask import Flask, render_template, request, redirect, url_for, flash, session
import random  
from flask_session import Session
import sqlite3
from datetime import datetime
app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

def get_db_connection():
    conn = sqlite3.connect('mydatabase.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
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
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM Users WHERE login = ? AND password = ?", (login, password))
        user = cursor.fetchone()
        
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Неверный логин или пароль. Попробуйте ещё раз.', 'danger')
    
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
        password = request.form['password']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        birthdate = request.form['birthdate']
        contactinfo = request.form['contactinfo']
        balance = request.form['balance']
        
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


        
@app.route('/play_coin_flip/<choice>/<game_id>', methods=['GET', 'POST'])
def play_coin_flip(choice, game_id):
    if request.method == 'POST':
        client_id = session['user_id']
        current_balance = get_balance(client_id)

        bet_amount = int(request.form['bet_amount'])

        game_chance = get_game_chance(game_id)

        if bet_amount > current_balance:
            flash('У вас недостаточно средств для этой ставки.', 'error')
            return redirect(url_for('play_coin_flip', choice=choice, game_id=game_id))

        coin = random.choices([1, 2], weights=[game_chance, 100 - game_chance])[0]

        if (choice == 'eagle' and coin == 1) or (choice == 'tail' and coin == 2):
            result = 'Поздравляем! Вы выиграли!'
            new_balance = current_balance + bet_amount
        else:
            result = 'К сожалению, вы проиграли.'
            new_balance = current_balance - bet_amount

        update_balance(client_id, new_balance)

        conn = sqlite3.connect('mydatabase.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO CoinFlipGames (ClientID, Choice, CoinOutcome, Result) VALUES (?, ?, ?, ?)",
               (client_id, choice, coin, result))

        conn.commit()
        conn.close()

        flash(result, 'result')
        return render_template('coin_flip.html', choice=choice, balance=new_balance, result=result)

    return render_template('coin_flip.html', choice=choice, game_id=game_id)

    if request.method == 'POST':
        client_id = session['user_id']
        current_balance = get_balance(client_id)

        bet_amount = int(request.form['bet_amount'])

        game_chance = get_game_chance(game_id)

        if bet_amount > current_balance:
            flash('У вас недостаточно средств для этой ставки.', 'error')
            return redirect(url_for('play_coin_flip', choice=choice, game_id=game_id))

        coin = random.choices([1, 2], [game_chance, 100 - game_chance])[0]

        if (choice == 'eagle' and coin == 1) or (choice == 'tail' and coin == 2):
            result = 'Поздравляем! Вы выиграли!'
            new_balance = current_balance + bet_amount
        else:
            result = 'К сожалению, вы проиграли.'
            new_balance = current_balance - bet_amount

        update_balance(client_id, new_balance)

        conn = sqlite3.connect('mydatabase.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO CoinFlipGames (ClientID, Choice, CoinOutcome, Result) VALUES (?, ?, ?, ?)",
               (client_id, choice, coin, result))

        conn.commit()
        conn.close()

        flash(result, 'result')
        return render_template('coin_flip.html', choice=choice, balance=new_balance, result=result)

    return render_template('coin_flip.html', choice=choice, game_id=game_id)

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

    
if __name__ == '__main__':
    app.run(debug=True)
