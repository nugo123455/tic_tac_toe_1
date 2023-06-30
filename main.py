from easyAI import TwoPlayerGame, Human_Player, AI_Player, Negamax
from flask import Flask, render_template, request, make_response, redirect, url_for
import sqlite3

conn = sqlite3.connect('tictactoe.db', check_same_thread=False)
cursor = conn.cursor()
cinn = sqlite3.connect("tictactoe_users.db", check_same_thread=False)
cursor1 = cinn.cursor()

# Create a table to store game data if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        board TEXT,
        winner TEXT
    )
''')
conn.commit()

# Create a table to store user data if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
''')
conn.commit()


class TicTacToe(TwoPlayerGame):


    def __init__(self, players):
        self.players = players
        self.board = [0 for _ in range(9)]
        self.current_player = 1  # player 1 starts.


    def possible_moves(self):
        return [i + 1 for i, e in enumerate(self.board) if e == 0]


    def make_move(self, move):
        self.board[int(move) - 1] = self.current_player


    def save_game(self):
        board_string = ",".join(map(str, self.board))
        winner = self.winner()
        cursor.execute("INSERT INTO games (board, winner) VALUES (?, ?)", (board_string, winner))
        conn.commit()


    def save_user(self):
        username1 = ",".join(map(str, self.board))
        password69 = self.winner()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username1, password69))
        conn.commit()
    def unmake_move(self, move):  # optional method (speeds up the AI)
        self.board[int(move) - 1] = 0


    WIN_LINES = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
        [1, 4, 7],
        [2, 5, 8],
        [3, 6, 9],
        [1, 5, 9],
        [3, 5, 7],
    ]


    def lose(self, who=None):
        """ Has the opponent "three in line ?" """
        if who is None:
            who = self.opponent_index
        wins = [
            all([(self.board[c - 1] == who) for c in line]) for line in self.WIN_LINES
        ]
        return any(wins)


    def is_over(self):
        return (
                (self.possible_moves() == [])
                or self.lose()
                or self.lose(who=self.current_player)
        )


    def show(self):
        print(
            "\n"
            + "\n".join(
                [
                    " ".join([[".", "O", "X"][self.board[3 * j + i]] for i in range(3)])
                    for j in range(3)
                ]
            )
        )


    def spot_string(self, i, j):
        return ["_", "O", "X"][self.board[3 * j + i]]


    def scoring(self):
        opp_won = self.lose()
        i_won = self.lose(who=self.current_player)
        if opp_won and not i_won:
            return -100
        if i_won and not opp_won:
            return 100
        return 0


    def winner(self):
        if self.lose(who=2):
            return "AI Wins"
        return "Tie"

app = Flask(__name__)
ai_algo = Negamax(6)


@app.route("/", methods=["GET"])
def home():
    return render_template("login.html", msg="")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Check if the username is already taken
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        result = cursor.fetchall()
        if result:
            return render_template("register.html",
                                          msg="Username already exists. Please choose a different username.")

        # Insert the user into the database
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()

        return redirect(url_for("home"))

    return render_template("register.html", msg="")


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    # Check if the username and password match
    cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
    result = cursor.fetchone()
    if result:
        # Redirect to the main game page
        resp = make_response(redirect(url_for("play_game")))

        resp.set_cookie("user_id", str(result[0]))
        return resp

    return render_template("login.html", msg="Invalid username or password.")


@app.route("/play", methods=["GET", "POST"])
def play_game():
    # Check if the user is logged in
    if "user_id" not in request.cookies:
        return redirect(url_for("home"))

    ttt = TicTacToe([Human_Player(), AI_Player(ai_algo)])
    game_cookie = request.cookies.get("game_board")
    if game_cookie:
        ttt.board = [int(x) for x in game_cookie.split(",")]
    if "choice" in request.form:
        if not ttt.is_over():
            ttt.play_move(request.form["choice"])
            if not ttt.is_over():
                ai_move = ttt.get_move()
                ttt.play_move(ai_move)
    if "reset" in request.form:
        ttt.board = [0 for _ in range(9)]
    if ttt.save_user():
        print("user saved")
    if ttt.is_over():
        ttt.save_game()
        print("game saved")
        msg = ttt.winner()
    else:
        msg = "Play Move"
    resp = make_response(render_template("index.html", ttt=ttt, msg=msg))
    c = ",".join(map(str, ttt.board))
    resp.set_cookie("game_board", c)
    return resp


if __name__ == "__main__":
    app.run()