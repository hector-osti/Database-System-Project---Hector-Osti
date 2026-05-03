from flask import Flask, render_template, request, redirect
import mysql.connector
from datetime import date

app = Flask(__name__, template_folder='templates')

# MySQL Connection
def get_db():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="",
        password="",
        database="game_platform"
    )

# Users
# -----
@app.route('/', methods=['GET'])
def index():
    db = get_db(); cursor = db.cursor()
    search = request.args.get('search')
    if search:
        cursor.execute(
            "select * from Users where username like %s or email like %s",
            (f"%{search}%", f"%{search}%")
        )
    else:
        cursor.execute("select * from users")
    users = cursor.fetchall()
    db.close()
    return render_template('index.html', users=users)

# Add
@app.route('/add', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        db = get_db(); cursor = db.cursor()
        cursor.execute(
            "insert into Users (username, email, join_date) values (%s, %s, %s)", (request.form['username'], request.form['email'], date.today())
        )
        db.commit(); db.close()
        return redirect('/')
    return render_template('add_user.html')

# Update
@app.route('/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    db = get_db(); cursor = db.cursor()
    if request.method == 'POST':
        cursor.execute(
            "update Users set username=%s, email=%s where user_id=%s",
            (request.form['username'], request.form['email'], user_id)
        )
        db.commit(); db.close()
        return redirect('/')
    cursor.execute("select * from Users where user_id=%s", (user_id,))
    user = cursor.fetchone(); db.close()
    return render_template('edit_user.html', user=user)

# Delete
@app.route('/delete/<int:user_id>')
def delete_user(user_id):
    db = get_db(); cursor = db.cursor()
    cursor.execute("delete from Users where user_id=%s", (user_id,))
    db.commit(); db.close()
    return redirect('/')

# Games
# -----
@app.route('/games')
def games():
    db = get_db(); cursor = db.cursor()
    search = request.args.get('search')
    if search:
        cursor.execute(
            "select * from Games where title like %s or genre like %s",
            (f"%{search}%", f"%{search}%")
        )
    else:
        cursor.execute("select * from Games order by game_id")
    games = cursor.fetchall(); db.close()
    return render_template('games.html', games=games)

# Add
@app.route('/games/add', methods=['GET', 'POST'])
def add_game():
    if request.method == 'POST':
        db = get_db(); cursor = db.cursor()
        cursor.execute(
            "insert into Games (title, genre, price, release_date) values (%s, %s, %s, %s)",
            (request.form['title'], request.form['genre'],
             request.form['price'], request.form['release_date'])
        )
        db.commit(); db.close()
        return redirect('/games')
    return render_template('add_game.html')

# Update
@app.route('/games/edit/<int:game_id>', methods=['GET', 'POST'])
def edit_game(game_id):
    db = get_db(); cursor = db.cursor()
    if request.method == 'POST':
        cursor.execute(
            "update Games set title=%s, genre=%s, price=%s, release_date=%s where game_id=%s",
            (request.form['title'], request.form['genre'],
             request.form['price'], request.form['release_date'], game_id)
        )
        db.commit(); db.close()
        return redirect('/games')
    cursor.execute("select * from Games where game_id=%s", (game_id,))
    game = cursor.fetchone(); db.close()
    return render_template('edit_game.html', game=game)

# Delete
@app.route('/games/delete/<int:game_id>')
def delete_game(game_id):
    db = get_db(); cursor = db.cursor()
    cursor.execute("delete from Games where game_id=%s", (game_id,))
    db.commit(); db.close()
    return redirect('/games')


# Game Sessions
# -------------
@app.route('/sessions')
def sessions():
    db = get_db(); cursor = db.cursor()
    cursor.execute("""
        select gs.session_id, u.username, g.title, gs.start_time, gs.end_time, gs.score
        from GameSessions gs
        join Users u on gs.user_id = u.user_id
        join Games g on gs.game_id = g.game_id
        order by gs.session_id desc
    """)
    sessions = cursor.fetchall(); db.close()
    return render_template('sessions.html', sessions=sessions)

# Add
@app.route('/sessions/add', methods=['GET', 'POST'])
def add_session():
    db = get_db(); cursor = db.cursor()
    if request.method == 'POST':
        cursor.execute(
            """insert into GameSessions (user_id, game_id, start_time, end_time, score)
            values (%s, %s, %s, %s, %s)""",
            (request.form['user_id'], request.form['game_id'],
             request.form['start_time'], request.form['end_time'] or None,
             request.form['score'])
        )
        db.commit(); db.close()
        return redirect('/sessions')
    cursor.execute("select user_id, username from Users order by username")
    users = cursor.fetchall()
    cursor.execute("select game_id, title from Games order by title")
    games = cursor.fetchall(); db.close()
    return render_template('add_session.html', users=users, games=games)

# Delete
@app.route('/sessions/delete/<int:session_id>')
def delete_session(session_id):
    db = get_db(); cursor = db.cursor()
    cursor.execute("delete from GameSessions where session_id=%s", (session_id,))
    db.commit(); db.close()
    return redirect('/sessions')


# Achievements
# ------------
@app.route('/achievements')
def achievements():
    db = get_db(); cursor = db.cursor()
    cursor.execute("""
        select a.achievement_id, g.title, a.name, a.description, a.points, a.score_required
        from Achievements a
        join Games g on a.game_id = g.game_id
        order by g.title, a.score_required
    """)
    achievements = cursor.fetchall(); db.close()
    return render_template('achievements.html', achievements=achievements)


# Add
@app.route('/achievements/add', methods=['GET', 'POST'])
def add_achievement():
    db = get_db(); cursor = db.cursor()
    if request.method == 'POST':
        cursor.execute(
            """insert into Achievements (game_id, name, description, points, score_required)
            values (%s, %s, %s, %s, %s)""",
            (request.form['game_id'], request.form['name'],
             request.form['description'], request.form['points'] or None,
             request.form['score_required'])
        )
        db.commit(); db.close()
        return redirect('/achievments')
    cursor.execute("select game_id, title from Games order by title")
    games = cursor.fetchall(); db.close()
    return render_template('add_achievement.html', games=games)

# Delete
@app.route('/achievements/delete/<int:achievement_id>')
def delete_achievement(achievement_id):
    db = get_db(); cursor = db.cursor()
    cursor.execute("delete from Achievements where achievement_id=%s", (achievement_id,))
    db.commit(); db.close()
    return redirect('/achivements')


# Purchases
# ---------
@app.route('/purchases')
def purchases():
    db = get_db(); cursor = db.cursor()
    cursor.execute("""
        select p.purchase_id, u.username, g.title, p.purchased_at, p.amount_paid
        from Purchases p
        join Users u on p.user_id = u.user_id
        join Games g on p.game_id = g.game_id
        order by p.purchased_at desc
    """)
    purchases = cursor.fetchall(); db.close()
    return render_template('purchases.html', purchases=purchases)


# Add
@app.route('/purchases/add', methods=['GET', 'POST'])
def add_purchase():
    db = get_db(); cursor = db.cursor()
    if request.method == 'POST':
        cursor.execute(
            "insert into Purchases (user_id, game_id, amount_paid) values (%s, %s, %s)",
            (request.form['user_id'], request.form['game_id'],
             request.form['amount_paid'])
        )
        db.commit(); db.close()
        return redirect('/purchases')
    cursor.execute("select user_id, username from Users order by username")
    users = cursor.fetchall()
    cursor.execute("select game_id, title, price from Games orber by title")
    games = cursor.fetchall(); db.close()
    return render_template('add_purchase.html', users=users, games=games)

# Delete
@app.route('/purchases/delete/<int:purchase_id>')
def delete_purchase(purchase_id):
    db = get_db(); cursor = db.cursor()
    cursor.execute("delete from Purchases where purchase_id=%s", (purchase_id,))
    db.commit(); db.close()
    return redirect('/purchases')


# Friends
# -------
@app.route('/friends')
def friends():
    db = get_db(); cursor = db.cursor()
    cursor.execute("""
        select u1.username, u2.username, f.since_date, f.user_id, f.friend_id
        from Friends f
        join Users u1 on f.user_id = u1.user_id
        join Users u2 on f.friend_id = u2.user_id
        where f.user_id < f.friend_id
        order by u1.username
    """)
    friends = cursor.fetchall(); db.close()
    return render_template('friends.html', friends=friends)

# Add
@app.route('/friends/add', methods=['GET', 'POST'])
def add_friend():
    db = get_db(); cursor = db.cursor()
    if request.method == 'POST':
        cursor.execute(
            "call AddFriends(%s, %s)",
            (request.form['user_id'], request.form['friend_id'])
        )
        db.commit(); db.close()
        return redirect('/friends')
    cursor.execute("select user_id, username from Users order by username")
    users = cursor.fetchall(); db.close()
    return render_template('add_friend.html', users=users)

# Delete
@app.route('/friends/delete/<int:user_id>/<int:friend_id>')
def delete_friend(user_id, friend_id):
    db = get_db(); cursor = db.cursor()
    cursor.execute("call RemoveFriend(%s, %s)", (user_id, friend_id))
    db.commit(); db.close()
    return redirect('/friends')


# Reports
# -------
@app.route('/reports')
def reports():
    db = get_db(); cursor = db.cursor(buffered=True)

    # Revenue by Genre
    cursor.execute("""
        select g.genre,
                count(distinct p.purchase_id) as total_purchases,
                sum(p.amount_paid) as total_revenue,
                round(avg(p.amount_paid), 2) as avg_sale_price
        from Purchases p, Games g
        where p.game_id = g.game_id
        group by g.genre
        order by total_revenue desc
    """)
    revenue_by_genre = cursor.fetchall()

    # Top users by achievement points
    cursor.execute("""
        select u.username,
                count(ua.achievement_id) as achievement_earned,
                coalesce(sum(a.points), 0) as total_points,
                GetTotalPlaytime(u.user_id) as hours_played
        from Users u
        left join UserAchievements ua on u.user_id = ua.user_id
        left join Achievements a on ua.achievement_id = a.achievement_id
        group by u.user_id, u.username
        order by total_points desc
    """)
    top_users = cursor.fetchall()

    # Avg score per game
    cursor.execute("""
        select g.title,
                count(gs.session_id) as total_sessions,
                round(avg(gs.score), 0) as avg_score,
                max(gs.score) as top_score
        from Games g
        left join GameSessions gs on g.game_id = gs.game_id and end_time is not null
        group by g.game_id, g.title order by avg_score desc
    """)
    game_stats = cursor.fetchall()

    db.close()
    return render_template('reports.html',
                           revenue_by_genre=revenue_by_genre,
                           top_users=top_users,
                           game_stats=game_stats)


if __name__ == '__main__':
    app.run(debug=True)
