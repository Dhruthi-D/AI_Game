from __future__ import annotations

from flask import Flask, jsonify, request, render_template_string, session, redirect
import time

from tictactoe import TicTacToe, minimax_best_move, other_player


app = Flask(__name__)
app.secret_key = "dev-secret-change-me"


HOME_HTML = """
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Start • Tic-Tac-Toe AI</title>
    <style>
      :root { --primary: #f1f5f9; --accent: #3b82f6; --bg: #0f172a; --card-bg: #1e293b; --border: #334155; --text-muted: #94a3b8; }
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 0; min-height: 100vh; display: grid; place-items: center; background: var(--bg); color: var(--primary); }
      .card { width: min(520px, 92vw); background: var(--card-bg); border: 1px solid var(--border); border-radius: 14px; padding: 22px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
      h1 { margin: 6px 0 14px; font-size: 24px; }
      .row { display:flex; gap: 10px; align-items:center; margin-bottom: 12px; }
      label { width: 88px; color: var(--text-muted); }
      input { flex: 1; padding: 10px 12px; border: 1px solid var(--border); border-radius: 10px; background: var(--bg); color: var(--primary); }
      button { background: var(--accent); color: #fff; border: none; padding: 10px 14px; border-radius: 10px; cursor: pointer; }
      .tile-group { display: flex; gap: 8px; flex-wrap: wrap; }
      .tile { padding: 10px 16px; border: 2px solid var(--border); border-radius: 10px; background: var(--bg); color: var(--primary); cursor: pointer; transition: all 0.2s ease; text-align: center; min-width: 80px; }
      .tile:hover { border-color: var(--accent); background: var(--card-bg); }
      .tile.selected { border-color: var(--accent); background: var(--accent); color: white; }
      .tile input[type="radio"] { display: none; }
    </style>
  </head>
  <body>
    <form class=\"card\" method=\"post\" action=\"/start\">
      <h1>Start a Game</h1>
      <div class=\"row\">
        <label for=\"player_name\">Your name</label>
        <input id=\"player_name\" name=\"player_name\" placeholder=\"Player\" value=\"{{ player_name }}\" />
      </div>
      <div class=\"row\">
        <label>You are</label>
        <div class=\"tile-group\">
          <label class=\"tile {{ 'selected' if human=='X' else '' }}\">
            <input type=\"radio\" name=\"human\" value=\"X\" {{ 'checked' if human=='X' else '' }}>
            X
          </label>
          <label class=\"tile {{ 'selected' if human=='O' else '' }}\">
            <input type=\"radio\" name=\"human\" value=\"O\" {{ 'checked' if human=='O' else '' }}>
            O
          </label>
        </div>
      </div>
      <div class=\"row\">
        <label>Level</label>
        <div class=\"tile-group\">
          <label class=\"tile {{ 'selected' if mode=='beginner' else '' }}\">
            <input type=\"radio\" name=\"mode\" value=\"beginner\" {{ 'checked' if mode=='beginner' else '' }}>
            Beginner
          </label>
          <label class=\"tile {{ 'selected' if mode=='intermediate' else '' }}\">
            <input type=\"radio\" name=\"mode\" value=\"intermediate\" {{ 'checked' if mode=='intermediate' else '' }}>
            Intermediate
          </label>
          <label class=\"tile {{ 'selected' if mode=='expert' else '' }}\">
            <input type=\"radio\" name=\"mode\" value=\"expert\" {{ 'checked' if mode=='expert' else '' }}>
            Expert
          </label>
        </div>
      </div>
      <button type=\"submit\">Play</button>
      <script>
        document.querySelectorAll('.tile-group input[type="radio"]').forEach((input) => {
          input.addEventListener('change', () => {
            const name = input.name;
            document.querySelectorAll(`.tile-group input[name="${name}"]`).forEach((r) => {
              const tile = r.closest('.tile');
              if (tile) tile.classList.toggle('selected', r.checked);
            });
          });
        });
      </script>
    </form>
  </body>
  </html>
"""


GAME_HTML = """
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Tic-Tac-Toe AI</title>
    <style>
      :root { --tile: 110px; --gap: 10px; --primary: #f1f5f9; --border: #475569; --accent: #3b82f6; --muted: #94a3b8; --bg: #0f172a; --card-bg: #1e293b; --cell-bg: #334155; }
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 24px; color: var(--primary); background: var(--bg); }
      .container { max-width: 480px; margin: 0 auto; background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
      h1 { margin: 0 0 12px; font-size: 22px; display:flex; justify-content: space-between; align-items:center; }
      .controls { display:flex; align-items:center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }
      button, .button { padding: 8px 12px; border-radius: 8px; background: var(--accent); color: white; border: none; text-decoration: none; display: inline-block; }
      button:disabled { background: #475569; }
      .tile-group { display: flex; gap: 8px; flex-wrap: wrap; }
      .tile { padding: 8px 12px; border: 2px solid var(--border); border-radius: 8px; background: var(--bg); color: var(--primary); cursor: pointer; transition: all 0.2s ease; text-align: center; min-width: 60px; }
      .tile:hover { border-color: var(--accent); background: var(--card-bg); }
      .tile.selected { border-color: var(--accent); background: var(--accent); color: white; }
      .tile input[type="radio"] { display: none; }
      .status { margin: 10px 0 16px; font-weight: 600; color: var(--muted); min-height: 22px; }
      .board { display: grid; grid-template-columns: repeat(3, var(--tile)); grid-gap: var(--gap); justify-content:center; }
      .cell { width: var(--tile); height: var(--tile); border: 2px solid var(--border); display:flex; align-items:center; justify-content:center; font-size: 56px; cursor: pointer; user-select: none; border-radius: 12px; background: var(--cell-bg); transition: transform .05s ease; }
      .cell:hover { transform: translateY(-1px); }
      .cell.disabled { cursor: not-allowed; color: #64748b; background: #1e293b; }
      .legend { margin-top: 14px; font-size: 13px; color: var(--muted); text-align:center; }
      .name { font-size: 14px; color: var(--muted); }
    </style>
  </head>
  <body>
    <div class=\"container\">
      <h1>
        Tic-Tac-Toe vs AI
        <div style=\"display: flex; flex-direction: column; align-items: flex-end; gap: 4px;\">
          <span class=\"name\">Player: {{ player_name }}</span>
          <span class=\"name\">Level: {{ mode.title() }}</span>
        </div>
      </h1>
      <div class=\"controls\">
        <button id=\"new\">New Game</button>
        <a href=\"/start\" class=\"button\">Home</a>
      </div>
      <div class=\"status\" id=\"status\"></div>
      <div class=\"board\" id=\"board\"></div>
      <div class=\"legend\">Click a square to make your move.</div>
    </div>

    <script>
      const boardEl = document.getElementById('board');
      const statusEl = document.getElementById('status');
      const newBtn = document.getElementById('new');

      let board = Array(9).fill(' ');
      let human = '{{ human }}';
      let ai = human === 'X' ? 'O' : 'X';
      let current = 'X';
      let gameOver = false;

      function render() {
        boardEl.innerHTML = '';
        board.forEach((cell, idx) => {
          const div = document.createElement('div');
          div.className = 'cell' + (gameOver || cell !== ' ' ? ' disabled' : '');
          div.textContent = cell;
          div.addEventListener('click', () => onCellClick(idx));
          boardEl.appendChild(div);
        });
        statusEl.textContent = `Turn: ${current}`;
      }

      async function startServerGame() {
        await fetch('/new-game', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mode: '{{ mode }}' }) });
      }

      async function reset() {
        board = Array(9).fill(' ');
        current = 'X';
        gameOver = false;
        human = '{{ human }}';
        ai = human === 'X' ? 'O' : 'X';
        await startServerGame();
        render();
        if (current === ai) aiMove();
      }

      async function onCellClick(i) {
        if (gameOver || current !== human || board[i] !== ' ') return;
        board[i] = human;
        current = ai;
        render();
        await aiMove();
      }

      async function aiMove() {
        if (gameOver) return;
        const res = await fetch('/ai-move', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ board, current, ai, mode: '{{ mode }}' }) });
        const data = await res.json();
        board = data.board;
        current = data.next;
        gameOver = data.gameOver;
        statusEl.textContent = data.status;
        if (gameOver) {
          const winner = data.status.startsWith('Winner: ') ? data.status.split(': ')[1] : '';
          const params = new URLSearchParams({ result: winner ? 'win' : 'draw', winner, human, ai });
          window.location.href = `/result?${params.toString()}`;
          return;
        }
        render();
      }

      newBtn.addEventListener('click', reset);
      // Start first game
      reset();
    </script>
  </body>
  </html>
"""


@app.get("/start")
def start_page():
    session.setdefault("player_name", "Player")
    session.setdefault("human", "X")
    session.setdefault("mode", "expert")
    # Initialize per-level stats structure
    session.setdefault("level_stats", {
        "beginner": {"human_wins": 0, "ai_wins": 0, "draws": 0},
        "intermediate": {"human_wins": 0, "ai_wins": 0, "draws": 0},
        "expert": {"human_wins": 0, "ai_wins": 0, "draws": 0},
    })
    return render_template_string(
        HOME_HTML,
        player_name=session.get("player_name", "Player"),
        human=session.get("human", "X"),
        mode=session.get("mode", "expert"),
    )


@app.post("/start")
def start_submit():
    session["player_name"] = request.form.get("player_name", "Player")
    session["human"] = request.form.get("human", "X")
    session["mode"] = request.form.get("mode", "expert").lower()
    # reset game timer
    session["game_started_at"] = time.time()
    # clear any previous frozen duration from last result
    session.pop("last_duration_seconds", None)
    return redirect("/game")


@app.get("/")
def root_redirect():
    return redirect("/start")


@app.get("/game")
def game_page():
    # Ensure counters are initialized
    session.setdefault("human_wins", 0)
    session.setdefault("ai_wins", 0)
    session.setdefault("draws", 0)
    session.setdefault("player_name", "Player")
    session.setdefault("human", "X")
    session.setdefault("mode", "expert")
    session.setdefault("level_stats", {
        "beginner": {"human_wins": 0, "ai_wins": 0, "draws": 0},
        "intermediate": {"human_wins": 0, "ai_wins": 0, "draws": 0},
        "expert": {"human_wins": 0, "ai_wins": 0, "draws": 0},
    })
    return render_template_string(
        GAME_HTML,
        player_name=session.get("player_name", "Player"),
        human=session.get("human", "X"),
        mode=session.get("mode", "expert"),
    )


@app.post("/new-game")
def new_game():
    payload = request.get_json(force=True)
    mode = (payload.get("mode", session.get("mode", "expert")) or "expert").lower()
    session["mode"] = mode
    session["game_started_at"] = time.time()
    # clear any previous frozen duration from last result
    session.pop("last_duration_seconds", None)
    return jsonify({ "ok": True, "mode": mode })


@app.post("/ai-move")
def ai_move():
    payload = request.get_json(force=True)
    board = payload.get("board", [" "] * 9)
    current = payload.get("current", "X")
    ai_player = payload.get("ai", "O")
    mode = (payload.get("mode", session.get("mode", "expert")) or "expert").lower()

    game = TicTacToe()
    game.board = [c if c in ("X", "O") else " " for c in board]

    # Helper to increment per-level stats in session
    def inc_level_stat(level: str, key: str):
        stats = session.get("level_stats") or {}
        if level not in stats:
            stats[level] = {"human_wins": 0, "ai_wins": 0, "draws": 0}
        if key not in stats[level]:
            stats[level][key] = 0
        stats[level][key] = int(stats[level][key]) + 1
        session["level_stats"] = stats

    # If terminal, just return the state and message (and update scores)
    if game.is_terminal():
        winner = game._check_winner()
        status = "Draw" if winner is None else f"Winner: {winner}"
        ai_player = payload.get("ai", "O")
        human_player = other_player(ai_player)
        if winner is None:
            session["draws"] = session.get("draws", 0) + 1
            inc_level_stat(mode, "draws")
        elif winner == human_player:
            session["human_wins"] = session.get("human_wins", 0) + 1
            inc_level_stat(mode, "human_wins")
        elif winner == ai_player:
            session["ai_wins"] = session.get("ai_wins", 0) + 1
            inc_level_stat(mode, "ai_wins")
        return jsonify({
            "board": game.board,
            "next": current,
            "status": status,
            "gameOver": True,
        })

    # Ensure it's AI's turn; if not, just echo
    if current != ai_player:
        return jsonify({
            "board": game.board,
            "next": current,
            "status": f"Turn: {current}",
            "gameOver": False,
        })

    # Compute move based on mode
    move = -1
    num_marks = sum(1 for c in game.board if c != " ")
    is_ai_first_move = (num_marks == 0) or (num_marks == 1 and current == ai_player)

    if mode == "beginner":
        import random
        if is_ai_first_move:
            edges = [i for i in [1,3,5,7] if game.board[i] == " "]
            if edges:
                move = random.choice(edges)
        if move == -1:
            # beginner picks randomly among available moves
            avail = game.available_moves()
            if avail:
                move = random.choice(avail)
    elif mode == "intermediate":
        human_player = other_player(ai_player)
        if is_ai_first_move:
            edges = [i for i in [1,3,5,7] if game.board[i] == " "]
            if edges:
                move = edges[0]
        if move == -1:
            # Try to block any immediate human win
            for i in game.available_moves():
                test_state = game.clone()
                test_state.make_move(i, human_player)
                if test_state._check_winner() == human_player:
                    move = i
                    break
        if move == -1:
            move = minimax_best_move(game, current_player=ai_player, ai_player=ai_player)
    else:  # expert
        move = minimax_best_move(game, current_player=ai_player, ai_player=ai_player)

    if move == -1:  # no move
        status = "Draw"
        return jsonify({"board": game.board, "next": current, "status": status, "gameOver": True})

    result = game.make_move(move, ai_player)
    if result.winner:
        status = f"Winner: {result.winner}"
        game_over = True
        next_turn = other_player(ai_player)
        human_player = other_player(ai_player)
        if result.winner == human_player:
            session["human_wins"] = session.get("human_wins", 0) + 1
            # per-level
            stats = session.get("level_stats") or {}
            stats.setdefault(mode, {"human_wins": 0, "ai_wins": 0, "draws": 0})
            stats[mode]["human_wins"] = int(stats[mode].get("human_wins", 0)) + 1
            session["level_stats"] = stats
        else:
            session["ai_wins"] = session.get("ai_wins", 0) + 1
            stats = session.get("level_stats") or {}
            stats.setdefault(mode, {"human_wins": 0, "ai_wins": 0, "draws": 0})
            stats[mode]["ai_wins"] = int(stats[mode].get("ai_wins", 0)) + 1
            session["level_stats"] = stats
    elif result.is_draw:
        status = "Draw"
        game_over = True
        next_turn = other_player(ai_player)
        session["draws"] = session.get("draws", 0) + 1
        stats = session.get("level_stats") or {}
        stats.setdefault(mode, {"human_wins": 0, "ai_wins": 0, "draws": 0})
        stats[mode]["draws"] = int(stats[mode].get("draws", 0)) + 1
        session["level_stats"] = stats
    else:
        status = f"Turn: {other_player(ai_player)}"
        game_over = False
        next_turn = other_player(ai_player)

    return jsonify({
        "board": result.board,
        "next": next_turn,
        "status": status,
        "gameOver": game_over,
    })


RESULT_HTML = """
<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Game Result</title>
    <style>
      :root { --win: #22c55e; --loss: #ef4444; --draw: #94a3b8; --card: #0b1220; --bg: #0f172a; --accent: #3b82f6; --border: #22314a; --text-muted: #94a3b8; --glow:#60a5fa; }
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 0; min-height: 100vh; display: grid; place-items: center; color: #eaf2ff; background: radial-gradient(1200px 600px at 80% -20%, rgba(59,130,246,.25), transparent 60%), radial-gradient(800px 500px at -10% 20%, rgba(16,185,129,.18), transparent 55%), linear-gradient(180deg, #0b1220, #0f172a); }
      .card { width: min(720px, 94vw); background: linear-gradient(180deg, rgba(255,255,255,.02), rgba(255,255,255,.01)); border: 1px solid var(--border); border-radius: 18px; padding: 28px 22px; box-shadow: 0 20px 60px rgba(0,0,0,0.45), 0 0 0 1px rgba(99,102,241,.05) inset; text-align: center; position: relative; overflow: hidden; backdrop-filter: blur(6px); }
      .card:before { content: ""; position: absolute; inset: -2px; border-radius: 20px; padding: 1px; background: linear-gradient(120deg, rgba(96,165,250,.45), rgba(34,197,94,.35), rgba(99,102,241,.35)); -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0); -webkit-mask-composite: xor; mask-composite: exclude; pointer-events: none; }
      h1 { margin: 10px 0 8px; font-size: 30px; font-weight: 800; background: linear-gradient(90deg, #fff, #c7d2fe, #93c5fd); -webkit-background-clip: text; background-clip: text; color: transparent; animation: shine 6s linear infinite; letter-spacing: .02em; }
      @keyframes shine { 0% { filter: drop-shadow(0 0 0 rgba(96,165,250,0)); } 50% { filter: drop-shadow(0 0 18px rgba(96,165,250,.25)); } 100% { filter: drop-shadow(0 0 0 rgba(96,165,250,0)); } }
      .sub { color: var(--text-muted); margin-bottom: 18px; }
      .tile-group { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; margin-bottom: 18px; }
      .tile { display:inline-block; padding: 9px 14px; font-weight: 700; border-radius: 999px; font-size: 12px; border: 1px solid; transition: transform .15s ease, background .2s ease, border-color .2s ease; letter-spacing: .04em; text-transform: uppercase; }
      .tile:hover { transform: translateY(-1px); }
      .tile.win { background: rgba(34,197,94,.12); color: var(--win); border-color: rgba(34,197,94,.35); box-shadow: 0 0 0 3px rgba(34,197,94,.08) inset; }
      .tile.loss { background: rgba(239,68,68,.12); color: var(--loss); border-color: rgba(239,68,68,.35); box-shadow: 0 0 0 3px rgba(239,68,68,.08) inset; }
      .tile.draw { background: rgba(148,163,184,.12); color: var(--draw); border-color: rgba(148,163,184,.35); box-shadow: 0 0 0 3px rgba(148,163,184,.08) inset; }
      .scores { display:grid; grid-template-columns: repeat(3,1fr); gap: 14px; margin: 16px 0 20px; }
      .score-card { border: 1px solid var(--border); border-radius: 14px; padding: 14px; background: linear-gradient(180deg, #0f172a, #0b1220); box-shadow: 0 8px 24px rgba(0,0,0,.25), 0 1px 0 rgba(255,255,255,.04) inset; }
      .score-title { font-size: 11px; color: var(--text-muted); margin-bottom: 6px; text-transform: uppercase; letter-spacing: .12em; }
      .score-value { font-size: 24px; font-weight: 800; }
      a.button { display: inline-block; padding: 11px 16px; background: linear-gradient(180deg, #3b82f6, #2563eb); color: #fff; text-decoration: none; border-radius: 12px; box-shadow: 0 10px 24px rgba(59,130,246,.35); transition: transform .12s ease, box-shadow .2s ease, filter .2s ease; border: 1px solid rgba(255,255,255,.06); }
      a.button:hover { transform: translateY(-1px); box-shadow: 0 14px 32px rgba(59,130,246,.45); filter: saturate(1.1); }
      .confetti { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; overflow: hidden; z-index: 999; }
      .confetti span { position: absolute; top: -20px; width: 10px; height: 14px; opacity: 1; animation: fall linear forwards; border-radius: 3px; }
      @keyframes fall { 0% { transform: translateY(-10vh) rotate(0deg); opacity: 1; } 100% { transform: translateY(110vh) rotate(720deg); opacity: 1; } }
      .row { margin-bottom: 10px; }
      .time-panel { border:1px solid var(--border); background: linear-gradient(180deg, #0f172a, #0b1220); border-radius:14px; padding:12px; margin: 12px auto 16px; text-align:left; box-shadow: 0 8px 24px rgba(0,0,0,.25), 0 1px 0 rgba(255,255,255,.04) inset; }
      .time-flex { display:flex; align-items:center; justify-content:space-between; gap:10px; }
      .time-value { font-size:22px; font-weight:800; }
      .time-best { font-size:13px; color: var(--text-muted); }
      .bar { height:10px; background: #1f2b3f; border-radius:999px; overflow:hidden; margin-top:8px; box-shadow: inset 0 1px 0 rgba(255,255,255,.05); }
      .bar > div { height:100%; background: linear-gradient(90deg, #60a5fa, #3b82f6); width:0; transition: width .9s ease; box-shadow: 0 0 12px rgba(96,165,250,.6); }
      .trophy { width: 54px; height: 54px; margin: 0 auto 6px; display: grid; place-items: center; filter: drop-shadow(0 6px 20px rgba(234,179,8,.2)); }
    </style>
  </head>
  <body>
    <div class="card">
      <div class="trophy" aria-hidden="true">
        <svg width="44" height="44" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M7 4h10a0 0 0 0 1 0 0v3a5 5 0 0 1-10 0V4a0 0 0 0 1 0 0Z" fill="#f59e0b"/>
          <path d="M17 4h3a2 2 0 0 1-2 3h-1V4Z" fill="#f59e0b"/>
          <path d="M7 4H4a2 2 0 0 0 2 3h1V4Z" fill="#f59e0b"/>
          <rect x="9" y="13" width="6" height="2" rx="1" fill="#fde68a"/>
          <rect x="8" y="16" width="8" height="2" rx="1" fill="#fde68a"/>
        </svg>
      </div>

      <h1>Game Complete!</h1>
      <div class="tile-group" style="margin-top:8px; margin-bottom:10px;">
        <div id="resultPill" class="tile draw" style="border-radius:999px; padding:6px 12px; font-size:12px;">Game Over</div>
      </div>
      <div class="sub" id="subtitle">Congratulations {{ player_name }}!</div>

      <div class="stats" style="display:grid; grid-template-columns: repeat(3,1fr); gap:14px; max-width:640px; margin: 0 auto 16px;">
        <div class="score-card">
          <div class="score-title">Attempts</div>
          <div class="score-value" id="attemptsValue">0</div>
          <div class="score-sub" style="font-size:12px; color: var(--text-muted); margin-top:6px;">Session total</div>
        </div>
        <div class="score-card">
          <div class="score-title">Time</div>
          <div class="score-value" id="timePretty">{{ duration_seconds }}s</div>
          <div class="score-sub" style="font-size:12px; color: var(--text-muted); margin-top:6px;">Optimal: —</div>
        </div>
        <div class="score-card">
          <div class="score-title">Result</div>
          <div class="score-value" id="resultValue">—</div>
          <div class="score-sub" style="font-size:12px; color: var(--text-muted); margin-top:6px;">Level: {{ mode }}</div>
        </div>
      </div>

      <div class="time-panel">
        <div class="time-flex">
          <div class="time-value">Your time: {{ duration_seconds }}s</div>
          <div class="time-best">Best: {{ best_time_seconds }}s</div>
        </div>
        <div class="bar"><div id="timeBar"></div></div>
      </div>

      <div class="scores" style="margin-top:18px;">
        <div class="score-card">
          <div class="score-title">You (wins)</div>
          <div class="score-value">{{ human_wins }}</div>
        </div>
        <div class="score-card">
          <div class="score-title">AI (wins)</div>
          <div class="score-value">{{ ai_wins }}</div>
        </div>
        <div class="score-card">
          <div class="score-title">Draws</div>
          <div class="score-value">{{ draws }}</div>
        </div>
      </div>

      <div style="margin: 12px 0 6px; font-weight:700; color:#cbd5e1;">By Level</div>
      <div class="scores">
        <div class="score-card">
          <div class="score-title">Beginner</div>
          <div style="display:flex; justify-content:space-between; color:#cbd5e1; font-weight:700;">
            <span>Wins: {{ level_stats['beginner']['human_wins'] }}</span>
            <span>Losses: {{ level_stats['beginner']['ai_wins'] }}</span>
            <span>Draws: {{ level_stats['beginner']['draws'] }}</span>
          </div>
        </div>
        <div class="score-card">
          <div class="score-title">Intermediate</div>
          <div style="display:flex; justify-content:space-between; color:#cbd5e1; font-weight:700;">
            <span>Wins: {{ level_stats['intermediate']['human_wins'] }}</span>
            <span>Losses: {{ level_stats['intermediate']['ai_wins'] }}</span>
            <span>Draws: {{ level_stats['intermediate']['draws'] }}</span>
          </div>
        </div>
        <div class="score-card">
          <div class="score-title">Expert</div>
          <div style="display:flex; justify-content:space-between; color:#cbd5e1; font-weight:700;">
            <span>Wins: {{ level_stats['expert']['human_wins'] }}</span>
            <span>Losses: {{ level_stats['expert']['ai_wins'] }}</span>
            <span>Draws: {{ level_stats['expert']['draws'] }}</span>
          </div>
        </div>
      </div>

      <div id="achievementsHeader" style="margin: 12px 0 8px; font-weight:700; color:#cbd5e1;">Achievements Unlocked!</div>
      <div id="achievementsGrid" class="scores" style="grid-template-columns: repeat(2,1fr);">
        <div class="score-card" id="achieve1">
          <div class="score-title">Perfect Solver! 🏆</div>
          <div style="font-size:13px; color:#cbd5e1;">Blazing fast finish!</div>
        </div>
        <div class="score-card" id="achieve2">
          <div class="score-title">Pure Logic! 🧠</div>
          <div style="font-size:13px; color:#cbd5e1;">Outsmarted the AI.</div>
        </div>
      </div>

      <div class="tile-group" id="extraBadges" style="margin-top:14px"></div>
      <div style="margin-top:10px">
        <a class="button" href="/game">Play Again</a>
        <a class="button" id="shareBtn" style="margin-left:8px">Share Result</a>
        <a class="button" href="/start" style="margin-left:8px">Home</a>
      </div>
      <div id="confetti" class="confetti"></div>
    </div>
    <script>
      const params = new URLSearchParams(window.location.search);
      const result = params.get('result');
      const winner = params.get('winner');
      const human = params.get('human');
      const ai = params.get('ai');
      const title = document.getElementById('title');
      const subtitle = document.getElementById('subtitle');
      const badge = document.getElementById('resultPill');
      // visual elements
      const confetti = document.getElementById('confetti');
      const extra = document.getElementById('extraBadges');
      const timeBar = document.getElementById('timeBar');
      const attemptsValue = document.getElementById('attemptsValue');
      const timePretty = document.getElementById('timePretty');
      const resultValue = document.getElementById('resultValue');
      const shareBtn = document.getElementById('shareBtn');
      const achievementsHeader = document.getElementById('achievementsHeader');
      const achievementsGrid = document.getElementById('achievementsGrid');

      function setAchievementsVisible(show) {
        if (!achievementsHeader || !achievementsGrid) return;
        achievementsHeader.style.display = show ? '' : 'none';
        achievementsGrid.style.display = show ? '' : 'none';
      }

      function addBadge(text, cls='draw') {
        const b = document.createElement('div');
        b.className = `tile ${cls}`;
        b.textContent = text;
        extra.appendChild(b);
      }

      function makeConfetti() {
        const colors = ['#fbbf24','#34d399','#60a5fa','#f472b6','#f97316','#a78bfa'];
        const count = 120;
        for (let i=0;i<count;i++) {
          const piece = document.createElement('span');
          const left = Math.random()*100;
          const delay = Math.random()*0.7;
          const dur = 1.8 + Math.random()*1.6;
          const col = colors[Math.floor(Math.random()*colors.length)];
          piece.style.left = left + '%';
          piece.style.background = col;
          piece.style.transform = `translateY(-10vh) rotate(${Math.random()*360}deg)`;
          piece.style.animationDuration = dur + 's';
          piece.style.animationDelay = delay + 's';
          confetti.appendChild(piece);
        }
        // Force a repaint to start animations in some browsers
        // by reading offsetHeight after appending
        void confetti.offsetHeight;
      }

      // pretty time (m:ss)
      function formatTime(sec){ const m = Math.floor(sec/60); const s = (sec%60).toString().padStart(2,'0'); return m>0? `${m}:${s}` : `${sec}s`; }

      if (result === 'draw') {
        document.title = 'Game Complete • Draw';
        subtitle.textContent = `You (${human}) vs AI (${ai})`;
        badge.textContent = 'Draw';
        badge.className = 'tile draw';
        resultValue.textContent = 'Draw';
      } else if (winner) {
        const youWon = winner === human;
        document.title = youWon ? 'Game Complete • Victory' : 'Game Complete • Defeat';
        subtitle.textContent = youWon ? `Congratulations {{ player_name }}!` : `Good try, {{ player_name }}!`;
        resultValue.textContent = youWon ? 'Win' : 'Loss';
        if (youWon) {
          badge.textContent = 'Perfect! 🏆';
          badge.className = 'tile win';
          makeConfetti();
          setAchievementsVisible(true);
        } else {
          badge.textContent = 'Defeat';
          badge.className = 'tile loss';
          setAchievementsVisible(false);
        }
      } else {
        document.title = 'Game Complete';
        subtitle.textContent = `You (${human}) vs AI (${ai})`;
        badge.textContent = 'Game Over';
        badge.className = 'tile draw';
        setAchievementsVisible(true);
      }

      // Time-based badges from server-injected seconds
      const durationSeconds = {{ duration_seconds }};
      const bestTime = {{ best_time_seconds }};
      const personalBest = {{ 'true' if personal_best else 'false' }};
      // Progress bar scales to 120s baseline and caps at 100%
      const pct = Math.min(100, Math.round((durationSeconds/120)*100));
      requestAnimationFrame(() => { timeBar.style.width = pct + '%'; });
      timePretty.textContent = formatTime(durationSeconds);
      attemptsValue.textContent = {{ human_wins }} + {{ ai_wins }} + {{ draws }};
      if (durationSeconds <= 10) addBadge('Quick Game', 'win');
      if (durationSeconds >= 60) addBadge('Marathon', 'draw');
      if (personalBest) addBadge('New Personal Best', 'win');

      if (shareBtn) {
        shareBtn.addEventListener('click', async () => {
          try {
            await navigator.clipboard.writeText(window.location.href);
            shareBtn.textContent = 'Link Copied!';
            setTimeout(() => shareBtn.textContent = 'Share Result', 1200);
          } catch (e) {
            alert('Link: ' + window.location.href);
          }
        });
      }
    </script>
  </body>
  </html>
"""


@app.get("/result")
def result_page():
    human_wins = session.get("human_wins", 0)
    ai_wins = session.get("ai_wins", 0)
    draws = session.get("draws", 0)
    level_stats = session.get("level_stats", {
        "beginner": {"human_wins": 0, "ai_wins": 0, "draws": 0},
        "intermediate": {"human_wins": 0, "ai_wins": 0, "draws": 0},
        "expert": {"human_wins": 0, "ai_wins": 0, "draws": 0},
    })
    started = session.get("game_started_at")
    # If we've already frozen a duration for this completed game, reuse it.
    frozen = session.get("last_duration_seconds")
    duration_seconds = 0
    if isinstance(frozen, (int, float)) and frozen >= 0:
        duration_seconds = int(frozen)
    elif isinstance(started, (int, float)):
        # First load after game end: compute and freeze duration
        duration_seconds = int(max(0, time.time() - started))
        session["last_duration_seconds"] = duration_seconds
    # Track personal best time (shortest total duration)
    best_time_seconds = session.get("best_time_seconds")
    personal_best = False
    if best_time_seconds is None or (duration_seconds > 0 and duration_seconds < best_time_seconds):
        session["best_time_seconds"] = duration_seconds
        best_time_seconds = duration_seconds
        personal_best = True
    if best_time_seconds is None:
        best_time_seconds = duration_seconds
    return render_template_string(
        RESULT_HTML,
        human_wins=human_wins,
        ai_wins=ai_wins,
        draws=draws,
        player_name=session.get("player_name", "Player"),
        mode=session.get("mode", "expert"),
        duration_seconds=duration_seconds,
        best_time_seconds=best_time_seconds,
        personal_best=personal_best,
        level_stats=level_stats,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)



