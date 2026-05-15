"""
Interactive Memory Challenge System
====================================
A fully functional memory card matching game built with Streamlit.

WHY STREAMLIT?
- Streamlit makes it easy to build interactive Python web apps without JavaScript.
- It handles UI rendering, state management, and deployment out of the box.

WHY SESSION_STATE?
- Streamlit reruns the entire script on every user interaction.
- session_state preserves game data (cards, score, moves, timer) across reruns.
- Without it, the game would reset on every click.

WHY RANDOM.SHUFFLE()?
- Ensures cards appear in a different random order every game.
- Makes the game fair and replayable.
"""

import streamlit as st
import random
import time
import sqlite3  # Built-in Python library — no pip install needed

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Memory Challenge",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# CSS STYLING
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Space Mono', monospace;
    background-color: #0e0e1a;
    color: #e0e0f0;
}
.main { background-color: #0e0e1a; }

h1.title {
    font-family: 'Syne', sans-serif;
    font-size: 2.6rem;
    font-weight: 800;
    background: linear-gradient(135deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 0.2rem;
}
.subtitle {
    text-align: center;
    color: #6b7280;
    font-size: 0.85rem;
    margin-bottom: 1.5rem;
}
.stat-box {
    background: #1a1a2e;
    border: 1px solid #2d2d4e;
    border-radius: 12px;
    padding: 14px 10px;
    text-align: center;
}
.stat-label {
    font-size: 0.7rem;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.stat-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #a78bfa;
}
.card-btn button {
    width: 100% !important;
    height: 72px !important;
    font-size: 1.8rem !important;
    border-radius: 12px !important;
    background: #1a1a2e !important;
    border: 2px solid #2d2d4e !important;
    color: #e0e0f0 !important;
    transition: all 0.15s ease !important;
}
.card-btn button:hover {
    border-color: #a78bfa !important;
    background: #24243e !important;
}
.card-matched button {
    width: 100% !important;
    height: 72px !important;
    font-size: 1.8rem !important;
    border-radius: 12px !important;
    background: #0f2d1f !important;
    border: 2px solid #34d399 !important;
    color: #34d399 !important;
}
.card-flipped button {
    width: 100% !important;
    height: 72px !important;
    font-size: 1.8rem !important;
    border-radius: 12px !important;
    background: #1e1b4b !important;
    border: 2px solid #a78bfa !important;
    color: #e0e0f0 !important;
}
.card-hidden button {
    width: 100% !important;
    height: 72px !important;
    font-size: 1.8rem !important;
    border-radius: 12px !important;
    background: #1a1a2e !important;
    border: 2px solid #2d2d4e !important;
    color: #2d2d4e !important;
}
.section-divider {
    border: none;
    border-top: 1px solid #2d2d4e;
    margin: 1.2rem 0;
}
.leaderboard-row {
    display: flex;
    justify-content: space-between;
    padding: 7px 12px;
    border-radius: 8px;
    margin-bottom: 5px;
    background: #1a1a2e;
    font-size: 0.82rem;
}
.leaderboard-row.top { border-left: 3px solid #f59e0b; }
.msg-success {
    text-align: center;
    font-size: 1.1rem;
    color: #34d399;
    font-weight: 700;
    padding: 10px;
}
.msg-info {
    text-align: center;
    font-size: 0.88rem;
    color: #60a5fa;
    padding: 6px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
DIFFICULTY_CONFIG = {
    "Easy":   {"pairs": 6,  "cols": 4},
    "Medium": {"pairs": 10, "cols": 5},
    "Hard":   {"pairs": 15, "cols": 6},
}

EMOJI_POOL = [
    "🐶","🐱","🦊","🐻","🐼","🦁","🐯","🦋",
    "🌸","🍕","🎸","🚀","⚡","🎯","🎪","🏆",
    "🌈","🔮","💎","🎭","🦄","🍀","🎲","🧩","🎨",
]

# Path to the SQLite database file.
# On Streamlit Cloud this lives in the app's working directory (ephemeral per session).
# Locally it persists between runs in the same folder as app.py.
DB_PATH = "leaderboard.db"

# ─────────────────────────────────────────────
# DATABASE FUNCTIONS
# ─────────────────────────────────────────────

def init_db():
    """
    Create the leaderboard table if it doesn't already exist.

    WHY 'IF NOT EXISTS'?
    - Streamlit reruns this script on every interaction.
    - Without this guard, it would try to CREATE the table every time and crash.

    WHY sqlite3.connect()?
    - Opens (or creates) the .db file automatically.
    - No separate server needed — the database is just a single file.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # CREATE TABLE only if it's missing — safe to call on every startup
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leaderboard (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            player     TEXT    NOT NULL,
            score      INTEGER NOT NULL,
            moves      INTEGER NOT NULL,
            difficulty TEXT    NOT NULL,
            time_secs  INTEGER NOT NULL,
            played_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    conn.commit()   # Write the schema change to disk
    conn.close()    # Always close the connection when done


def insert_score(player: str, score: int, moves: int, difficulty: str, time_secs: int):
    """
    Insert one completed-game record into the leaderboard table.

    WHY parameterised query (the '?' placeholders)?
    - Prevents SQL injection — never build queries by string-concatenating user input.
    - The tuple of values maps 1-to-1 with the '?' placeholders.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO leaderboard (player, score, moves, difficulty, time_secs)
        VALUES (?, ?, ?, ?, ?)
    """, (player, score, moves, difficulty, time_secs))

    conn.commit()
    conn.close()


def fetch_top_scores(limit: int = 10) -> list[dict]:
    """
    Retrieve the top scores from the database, ordered by score DESC then time ASC.
    Returns plain dicts so the rest of the app stays database-agnostic.

    WHY ORDER BY score DESC, time_secs ASC?
    - Highest scores rank first.
    - Ties are broken by fastest completion time (lower = better).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Lets us access columns by name: row["score"]
    cursor = conn.cursor()

    cursor.execute("""
        SELECT player, score, moves, difficulty, time_secs, played_at
        FROM leaderboard
        ORDER BY score DESC, time_secs ASC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()   # Fetch all matching rows into memory
    conn.close()

    # Convert sqlite3.Row objects → plain dicts for easy use in Streamlit
    return [dict(row) for row in rows]


# ─────────────────────────────────────────────
# CORE GAME FUNCTIONS
# ─────────────────────────────────────────────

def generate_cards(num_pairs: int) -> list[dict]:
    """
    Create a shuffled deck of card pairs.
    WHY random.shuffle()? So every game has a unique layout, keeping it fun.
    Each card is a dict with id, emoji, flipped, matched.
    """
    chosen = random.sample(EMOJI_POOL, num_pairs)
    deck = []
    for i, emoji in enumerate(chosen * 2):  # each emoji appears twice
        deck.append({
            "id": i,
            "emoji": emoji,
            "flipped": False,
            "matched": False,
        })
    random.shuffle(deck)  # randomise positions
    # Re-assign IDs after shuffle so they reflect position
    for idx, card in enumerate(deck):
        card["id"] = idx
    return deck


def reset_to_lobby():
    """
    Send the app back to the lobby (pre-game) screen and wipe ALL game state.
    Call this after a game ends OR when the player explicitly clicks 'New Game'.

    WHY clear everything explicitly?
    - Streamlit session_state is sticky: old values survive reruns unless deleted.
    - If we only set game_active=False, cards/score/player_name from the last
      game would bleed into the next one — exactly the bug we're fixing.
    """
    keys_to_clear = [
        "cards", "cols", "score", "moves", "matched_count", "total_pairs",
        "flipped_indices", "game_active", "game_over", "start_time",
        "elapsed", "difficulty", "waiting", "player_name",
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)   # pop() is safe even if key is missing

    # screen="lobby" is the single flag that drives which screen main() renders
    st.session_state.screen = "lobby"


def initialize_game(player_name: str, difficulty: str):
    """
    Set up ALL session_state variables for a fresh game.

    WHY session_state? Streamlit reruns the script on every interaction;
    session_state is the only way to keep game data alive between reruns.

    Takes player_name explicitly so it is captured at the moment Start is pressed,
    not read lazily later (avoids stale-name bugs).
    """
    cfg = DIFFICULTY_CONFIG[difficulty]
    st.session_state.cards          = generate_cards(cfg["pairs"])
    st.session_state.cols           = cfg["cols"]
    st.session_state.score          = 0
    st.session_state.moves          = 0
    st.session_state.matched_count  = 0
    st.session_state.total_pairs    = cfg["pairs"]
    st.session_state.flipped_indices = []   # the 1–2 currently face-up card indices
    st.session_state.game_active    = True
    st.session_state.game_over      = False
    st.session_state.start_time     = time.time()
    st.session_state.elapsed        = 0
    st.session_state.difficulty     = difficulty
    st.session_state.waiting        = False  # True while showing a wrong pair
    st.session_state.player_name    = player_name.strip() or "Guest"
    st.session_state.screen         = "playing"


def check_match():
    """
    Compare the two flipped cards.
    If they match: mark both matched, award points.
    If not: schedule a flip-back (set waiting=True) — handled on next rerun.
    """
    idx_a, idx_b = st.session_state.flipped_indices
    card_a = st.session_state.cards[idx_a]
    card_b = st.session_state.cards[idx_b]
    st.session_state.moves += 1

    if card_a["emoji"] == card_b["emoji"]:
        # ✅ Match found
        st.session_state.cards[idx_a]["matched"] = True
        st.session_state.cards[idx_b]["matched"] = True
        st.session_state.matched_count += 1
        st.session_state.score += 10
        st.session_state.flipped_indices = []

        if st.session_state.matched_count == st.session_state.total_pairs:
            # 🎉 All pairs found → game over
            elapsed = time.time() - st.session_state.start_time
            st.session_state.elapsed = int(elapsed)
            st.session_state.game_over = True
            st.session_state.game_active = False
            save_score()
    else:
        # ❌ No match — flip both back after a short pause
        st.session_state.waiting = True


def save_score():
    """
    Persist the finished game to the SQLite database.

    player_name was captured at Start time by initialize_game(), so it is always
    clean — no risk of reading a stale or empty value here.
    """
    player = st.session_state.get("player_name", "Guest") or "Guest"

    # Write to the database — this is the single source of truth
    insert_score(
        player=player,
        score=st.session_state.score,
        moves=st.session_state.moves,
        difficulty=st.session_state.difficulty,
        time_secs=st.session_state.elapsed,
    )

    # Mark that we are now on the results screen
    st.session_state.screen = "results"


def flip_back_if_waiting():
    """
    If two non-matching cards are showing, pause briefly then flip them back.
    Called at the top of each rerun cycle so the delay is visible.
    """
    if st.session_state.get("waiting", False):
        time.sleep(0.7)  # brief pause so the player sees the wrong pair
        for idx in st.session_state.flipped_indices:
            st.session_state.cards[idx]["flipped"] = False
        st.session_state.flipped_indices = []
        st.session_state.waiting = False


def on_card_click(card_idx: int):
    """
    Handle a card click event:
    - Ignore if card is already matched/flipped, or waiting to flip back.
    - Flip the card; if it's the second flip, call check_match().
    """
    if st.session_state.waiting:
        return
    card = st.session_state.cards[card_idx]
    if card["matched"] or card["flipped"]:
        return
    if len(st.session_state.flipped_indices) >= 2:
        return

    # Flip this card face-up
    st.session_state.cards[card_idx]["flipped"] = True
    st.session_state.flipped_indices.append(card_idx)

    if len(st.session_state.flipped_indices) == 2:
        check_match()


def render_board():
    """
    Draw the card grid using Streamlit columns.
    Each card is a button. Appearance varies by state: hidden / flipped / matched.
    """
    cards = st.session_state.cards
    cols_count = st.session_state.cols

    for row_start in range(0, len(cards), cols_count):
        row_cards = cards[row_start: row_start + cols_count]
        cols = st.columns(cols_count)
        for col_idx, card in enumerate(row_cards):
            with cols[col_idx]:
                if card["matched"]:
                    # Show emoji, green border (matched)
                    st.markdown('<div class="card-matched">', unsafe_allow_html=True)
                    st.button(card["emoji"], key=f"card_{card['id']}", disabled=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                elif card["flipped"]:
                    # Show emoji, purple border (face-up, not yet matched)
                    st.markdown('<div class="card-flipped">', unsafe_allow_html=True)
                    st.button(card["emoji"], key=f"card_{card['id']}",
                              on_click=on_card_click, args=(card["id"],))
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    # Face-down card — show "?" symbol
                    st.markdown('<div class="card-btn">', unsafe_allow_html=True)
                    st.button("?", key=f"card_{card['id']}",
                              on_click=on_card_click, args=(card["id"],))
                    st.markdown('</div>', unsafe_allow_html=True)


def render_stats():
    """Display live stats: timer, score, moves, pairs found."""
    elapsed = int(time.time() - st.session_state.start_time) if st.session_state.game_active else st.session_state.elapsed
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="stat-box"><div class="stat-label">⏱ Time</div><div class="stat-value">{elapsed}s</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-box"><div class="stat-label">⭐ Score</div><div class="stat-value">{st.session_state.score}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-box"><div class="stat-label">🔄 Moves</div><div class="stat-value">{st.session_state.moves}</div></div>', unsafe_allow_html=True)
    with c4:
        matched = st.session_state.matched_count
        total = st.session_state.total_pairs
        st.markdown(f'<div class="stat-box"><div class="stat-label">✅ Pairs</div><div class="stat-value">{matched}/{total}</div></div>', unsafe_allow_html=True)


def render_leaderboard():
    """
    Fetch the top scores from SQLite and display them.

    WHY fetch from DB here instead of session_state?
    - The DB holds ALL-TIME scores, not just from the current browser session.
    - Every call reflects the latest data without needing a full page reload.
    """
    st.markdown("### 🏆 Leaderboard")

    # Always pull fresh data straight from the database
    scores = fetch_top_scores(10)

    if not scores:
        st.markdown('<div class="msg-info">No scores yet. Finish a game to appear here!</div>', unsafe_allow_html=True)
        return

    for i, entry in enumerate(scores):
        cls = "leaderboard-row top" if i == 0 else "leaderboard-row"
        medal = ["🥇","🥈","🥉"][i] if i < 3 else f"#{i+1}"
        # entry keys come from the SELECT columns: player, score, moves, difficulty, time_secs
        st.markdown(
            f'<div class="{cls}">' +
            f'<span>{medal} <b>{entry["player"]}</b></span>' +
            f'<span>{entry["difficulty"]}</span>' +
            f'<span>⭐ {entry["score"]} pts</span>' +
            f'<span>🔄 {entry["moves"]} moves</span>' +
            f'<span>⏱ {entry["time_secs"]}s</span>' +
            '</div>',
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────

def main():
    """
    Single dispatcher: reads st.session_state.screen and renders the right view.

    screen values:
        "lobby"   → name + difficulty entry, leaderboard preview
        "playing" → live card board + stats
        "results" → game-over summary + leaderboard + New Game button

    WHY a single 'screen' key instead of multiple booleans?
    - One source of truth is easier to reason about than game_active + game_over combos.
    - Transitioning between screens is one assignment: st.session_state.screen = "..."
    """
    # ── Shared header ─────────────────────────
    st.markdown('<h1 class="title">🧠 Memory Challenge</h1>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Flip cards · Find pairs · Beat your score</div>', unsafe_allow_html=True)

    screen = st.session_state.get("screen", "lobby")

    # ════════════════════════════════════════════
    # SCREEN 1 — LOBBY
    # ════════════════════════════════════════════
    if screen == "lobby":
        st.markdown("""
        <div style='text-align:center; padding: 1.5rem 1rem 0.5rem;'>
            <div style='font-size:4.5rem;'>🃏</div>
            <h2 style='color:#a78bfa; font-family:Syne,sans-serif; margin-bottom:0.2rem;'>
                Ready to test your memory?
            </h2>
            <p style='color:#6b7280;'>Enter your name and difficulty, then hit Start.</p>
        </div>
        """, unsafe_allow_html=True)

        col_l, col_c, col_r = st.columns([1, 2, 1])
        with col_c:
            # WHY value=""? Ensures the field is always blank for a new player —
            # no stale name from a previous session bleeds through.
            name = st.text_input(
                "👤 Your Name",
                value=st.session_state.get("pending_name", ""),
                placeholder="Leave blank to play as Guest",
                key="lobby_name_input",
            )
            difficulty = st.selectbox(
                "🎯 Difficulty",
                ["Easy", "Medium", "Hard"],
                key="lobby_difficulty",
            )
            if st.button("▶ Start Game", use_container_width=True, type="primary"):
                # Capture name NOW so it can never change mid-game
                initialize_game(player_name=name, difficulty=difficulty)
                st.rerun()   # jump straight to the playing screen

        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
        render_leaderboard()
        return

    # ════════════════════════════════════════════
    # SCREEN 2 — PLAYING
    # ════════════════════════════════════════════
    if screen == "playing":
        # Sidebar: in-game controls only
        with st.sidebar:
            st.markdown("## ⚙️ Controls")
            if st.button("🔄 Restart (same settings)", use_container_width=True):
                initialize_game(
                    player_name=st.session_state.player_name,
                    difficulty=st.session_state.difficulty,
                )
                st.rerun()
            if st.button("🏠 Back to Lobby", use_container_width=True):
                reset_to_lobby()
                st.rerun()
            st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
            render_leaderboard()

        # 1. Resolve any pending mismatch flip-back
        flip_back_if_waiting()

        # 2. Live stats
        render_stats()
        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

        # 3. Card grid
        render_board()

        # 4. Tick the timer — rerun every second while the game is live
        if st.session_state.get("game_active"):
            time.sleep(1)
            st.rerun()
        return

    # ════════════════════════════════════════════
    # SCREEN 3 — RESULTS
    # ════════════════════════════════════════════
    if screen == "results":
        player   = st.session_state.get("player_name", "Guest")
        score    = st.session_state.get("score", 0)
        moves    = st.session_state.get("moves", 0)
        elapsed  = st.session_state.get("elapsed", 0)
        pairs    = st.session_state.get("total_pairs", 0)

        st.markdown(f"""
        <div class="msg-success">
            🎉 Well done, {player}!  All {pairs} pairs matched!<br>
            Score: {score} pts &nbsp;·&nbsp; Moves: {moves} &nbsp;·&nbsp; Time: {elapsed}s
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

        col_l, col_c, col_r = st.columns([1, 2, 1])
        with col_c:
            # "Play Again" keeps the same player name pre-filled for convenience
            if st.button("🔄 Play Again (same name)", use_container_width=True, type="primary"):
                saved_name = st.session_state.get("player_name", "")
                reset_to_lobby()
                # Pre-fill the name so returning players don't have to retype it
                st.session_state.pending_name = saved_name
                st.rerun()

            if st.button("🏠 New Player / Change Name", use_container_width=True):
                reset_to_lobby()   # wipes everything, including player_name
                st.rerun()

        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
        render_leaderboard()
        return


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # ── One-time database setup ─────────────────────────────────
    # Safe to call on every rerun — "IF NOT EXISTS" means it's a no-op after first run.
    init_db()

    # ── Screen bootstrap ────────────────────────────────────────
    # "screen" is the single source of truth for which view is rendered.
    # Set it only once; after that main() and the buttons manage transitions.
    if "screen" not in st.session_state:
        st.session_state.screen = "lobby"

    main()
# """
# Interactive Memory Challenge System
# ====================================
# A fully functional memory card matching game built with Streamlit.

# WHY STREAMLIT?
# - Streamlit makes it easy to build interactive Python web apps without JavaScript.
# - It handles UI rendering, state management, and deployment out of the box.

# WHY SESSION_STATE?
# - Streamlit reruns the entire script on every user interaction.
# - session_state preserves game data (cards, score, moves, timer) across reruns.
# - Without it, the game would reset on every click.

# WHY RANDOM.SHUFFLE()?
# - Ensures cards appear in a different random order every game.
# - Makes the game fair and replayable.
# """

# import streamlit as st
# import random
# import time
# import sqlite3  # Built-in Python library — no pip install needed

# # ─────────────────────────────────────────────
# # PAGE CONFIG
# # ─────────────────────────────────────────────
# st.set_page_config(
#     page_title="Memory Challenge",
#     page_icon="🧠",
#     layout="wide",
#     initial_sidebar_state="collapsed",
# )

# # ─────────────────────────────────────────────
# # CSS STYLING
# # ─────────────────────────────────────────────
# st.markdown("""
# <style>
# @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@700;800&display=swap');

# html, body, [class*="css"] {
#     font-family: 'Space Mono', monospace;
#     background-color: #0e0e1a;
#     color: #e0e0f0;
# }
# .main { background-color: #0e0e1a; }

# h1.title {
#     font-family: 'Syne', sans-serif;
#     font-size: 2.6rem;
#     font-weight: 800;
#     background: linear-gradient(135deg, #a78bfa, #60a5fa, #34d399);
#     -webkit-background-clip: text;
#     -webkit-text-fill-color: transparent;
#     text-align: center;
#     margin-bottom: 0.2rem;
# }
# .subtitle {
#     text-align: center;
#     color: #6b7280;
#     font-size: 0.85rem;
#     margin-bottom: 1.5rem;
# }
# .stat-box {
#     background: #1a1a2e;
#     border: 1px solid #2d2d4e;
#     border-radius: 12px;
#     padding: 14px 10px;
#     text-align: center;
# }
# .stat-label {
#     font-size: 0.7rem;
#     color: #6b7280;
#     text-transform: uppercase;
#     letter-spacing: 1px;
# }
# .stat-value {
#     font-size: 1.6rem;
#     font-weight: 700;
#     color: #a78bfa;
# }
# .card-btn button {
#     width: 100% !important;
#     height: 72px !important;
#     font-size: 1.8rem !important;
#     border-radius: 12px !important;
#     background: #1a1a2e !important;
#     border: 2px solid #2d2d4e !important;
#     color: #e0e0f0 !important;
#     transition: all 0.15s ease !important;
# }
# .card-btn button:hover {
#     border-color: #a78bfa !important;
#     background: #24243e !important;
# }
# .card-matched button {
#     width: 100% !important;
#     height: 72px !important;
#     font-size: 1.8rem !important;
#     border-radius: 12px !important;
#     background: #0f2d1f !important;
#     border: 2px solid #34d399 !important;
#     color: #34d399 !important;
# }
# .card-flipped button {
#     width: 100% !important;
#     height: 72px !important;
#     font-size: 1.8rem !important;
#     border-radius: 12px !important;
#     background: #1e1b4b !important;
#     border: 2px solid #a78bfa !important;
#     color: #e0e0f0 !important;
# }
# .card-hidden button {
#     width: 100% !important;
#     height: 72px !important;
#     font-size: 1.8rem !important;
#     border-radius: 12px !important;
#     background: #1a1a2e !important;
#     border: 2px solid #2d2d4e !important;
#     color: #2d2d4e !important;
# }
# .section-divider {
#     border: none;
#     border-top: 1px solid #2d2d4e;
#     margin: 1.2rem 0;
# }
# .leaderboard-row {
#     display: flex;
#     justify-content: space-between;
#     padding: 7px 12px;
#     border-radius: 8px;
#     margin-bottom: 5px;
#     background: #1a1a2e;
#     font-size: 0.82rem;
# }
# .leaderboard-row.top { border-left: 3px solid #f59e0b; }
# .msg-success {
#     text-align: center;
#     font-size: 1.1rem;
#     color: #34d399;
#     font-weight: 700;
#     padding: 10px;
# }
# .msg-info {
#     text-align: center;
#     font-size: 0.88rem;
#     color: #60a5fa;
#     padding: 6px;
# }
# </style>
# """, unsafe_allow_html=True)

# # ─────────────────────────────────────────────
# # CONSTANTS
# # ─────────────────────────────────────────────
# DIFFICULTY_CONFIG = {
#     "Easy":   {"pairs": 6,  "cols": 4},
#     "Medium": {"pairs": 10, "cols": 5},
#     "Hard":   {"pairs": 15, "cols": 6},
# }

# EMOJI_POOL = [
#     "🐶","🐱","🦊","🐻","🐼","🦁","🐯","🦋",
#     "🌸","🍕","🎸","🚀","⚡","🎯","🎪","🏆",
#     "🌈","🔮","💎","🎭","🦄","🍀","🎲","🧩","🎨",
# ]

# # Path to the SQLite database file.
# # On Streamlit Cloud this lives in the app's working directory (ephemeral per session).
# # Locally it persists between runs in the same folder as app.py.
# DB_PATH = "leaderboard.db"

# # ─────────────────────────────────────────────
# # DATABASE FUNCTIONS
# # ─────────────────────────────────────────────

# def init_db():
#     """
#     Create the leaderboard table if it doesn't already exist.

#     WHY 'IF NOT EXISTS'?
#     - Streamlit reruns this script on every interaction.
#     - Without this guard, it would try to CREATE the table every time and crash.

#     WHY sqlite3.connect()?
#     - Opens (or creates) the .db file automatically.
#     - No separate server needed — the database is just a single file.
#     """
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()

#     # CREATE TABLE only if it's missing — safe to call on every startup
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS leaderboard (
#             id         INTEGER PRIMARY KEY AUTOINCREMENT,
#             player     TEXT    NOT NULL,
#             score      INTEGER NOT NULL,
#             moves      INTEGER NOT NULL,
#             difficulty TEXT    NOT NULL,
#             time_secs  INTEGER NOT NULL,
#             played_at  TEXT    DEFAULT (datetime('now'))
#         )
#     """)

#     conn.commit()   # Write the schema change to disk
#     conn.close()    # Always close the connection when done


# def insert_score(player: str, score: int, moves: int, difficulty: str, time_secs: int):
#     """
#     Insert one completed-game record into the leaderboard table.

#     WHY parameterised query (the '?' placeholders)?
#     - Prevents SQL injection — never build queries by string-concatenating user input.
#     - The tuple of values maps 1-to-1 with the '?' placeholders.
#     """
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()

#     cursor.execute("""
#         INSERT INTO leaderboard (player, score, moves, difficulty, time_secs)
#         VALUES (?, ?, ?, ?, ?)
#     """, (player, score, moves, difficulty, time_secs))

#     conn.commit()
#     conn.close()


# def fetch_top_scores(limit: int = 10) -> list[dict]:
#     """
#     Retrieve the top scores from the database, ordered by score DESC then time ASC.
#     Returns plain dicts so the rest of the app stays database-agnostic.

#     WHY ORDER BY score DESC, time_secs ASC?
#     - Highest scores rank first.
#     - Ties are broken by fastest completion time (lower = better).
#     """
#     conn = sqlite3.connect(DB_PATH)
#     conn.row_factory = sqlite3.Row  # Lets us access columns by name: row["score"]
#     cursor = conn.cursor()

#     cursor.execute("""
#         SELECT player, score, moves, difficulty, time_secs, played_at
#         FROM leaderboard
#         ORDER BY score DESC, time_secs ASC
#         LIMIT ?
#     """, (limit,))

#     rows = cursor.fetchall()   # Fetch all matching rows into memory
#     conn.close()

#     # Convert sqlite3.Row objects → plain dicts for easy use in Streamlit
#     return [dict(row) for row in rows]


# # ─────────────────────────────────────────────
# # CORE GAME FUNCTIONS
# # ─────────────────────────────────────────────

# def generate_cards(num_pairs: int) -> list[dict]:
#     """
#     Create a shuffled deck of card pairs.
#     WHY random.shuffle()? So every game has a unique layout, keeping it fun.
#     Each card is a dict with id, emoji, flipped, matched.
#     """
#     chosen = random.sample(EMOJI_POOL, num_pairs)
#     deck = []
#     for i, emoji in enumerate(chosen * 2):  # each emoji appears twice
#         deck.append({
#             "id": i,
#             "emoji": emoji,
#             "flipped": False,
#             "matched": False,
#         })
#     random.shuffle(deck)  # randomise positions
#     # Re-assign IDs after shuffle so they reflect position
#     for idx, card in enumerate(deck):
#         card["id"] = idx
#     return deck


# def initialize_game(difficulty: str):
#     """
#     Set up all session_state variables for a fresh game.
#     WHY session_state? Streamlit reruns the script on every interaction;
#     session_state is the only way to keep game data alive between reruns.
#     """
#     cfg = DIFFICULTY_CONFIG[difficulty]
#     st.session_state.cards = generate_cards(cfg["pairs"])
#     st.session_state.cols = cfg["cols"]
#     st.session_state.score = 0
#     st.session_state.moves = 0
#     st.session_state.matched_count = 0
#     st.session_state.total_pairs = cfg["pairs"]
#     st.session_state.flipped_indices = []   # tracks the 1–2 currently-revealed cards
#     st.session_state.game_active = True
#     st.session_state.game_over = False
#     st.session_state.start_time = time.time()
#     st.session_state.elapsed = 0
#     st.session_state.difficulty = difficulty
#     st.session_state.waiting = False        # True while showing a wrong pair before flipping back


# def check_match():
#     """
#     Compare the two flipped cards.
#     If they match: mark both matched, award points.
#     If not: schedule a flip-back (set waiting=True) — handled on next rerun.
#     """
#     idx_a, idx_b = st.session_state.flipped_indices
#     card_a = st.session_state.cards[idx_a]
#     card_b = st.session_state.cards[idx_b]
#     st.session_state.moves += 1

#     if card_a["emoji"] == card_b["emoji"]:
#         # ✅ Match found
#         st.session_state.cards[idx_a]["matched"] = True
#         st.session_state.cards[idx_b]["matched"] = True
#         st.session_state.matched_count += 1
#         st.session_state.score += 10
#         st.session_state.flipped_indices = []

#         if st.session_state.matched_count == st.session_state.total_pairs:
#             # 🎉 All pairs found → game over
#             elapsed = time.time() - st.session_state.start_time
#             st.session_state.elapsed = int(elapsed)
#             st.session_state.game_over = True
#             st.session_state.game_active = False
#             save_score()
#     else:
#         # ❌ No match — flip both back after a short pause
#         st.session_state.waiting = True


# def save_score():
#     """
#     Persist the finished game to the SQLite database.

#     Flow:
#     1. Read the player name stored in session_state (entered at game-over screen).
#     2. Call insert_score() to write one row to the DB.
#     3. Re-fetch the global top-10 so the leaderboard refreshes immediately.

#     WHY write to SQLite instead of only session_state?
#     - session_state is wiped when the browser tab closes or the app restarts.
#     - The database file survives restarts, giving a persistent all-time leaderboard.
#     """
#     player = st.session_state.get("player_name", "Anonymous").strip() or "Anonymous"

#     # Write to the database — this is the single source of truth
#     insert_score(
#         player=player,
#         score=st.session_state.score,
#         moves=st.session_state.moves,
#         difficulty=st.session_state.difficulty,
#         time_secs=st.session_state.elapsed,
#     )

#     # Refresh the in-memory cache so the UI updates without a full page reload
#     st.session_state.leaderboard = fetch_top_scores(10)


# def flip_back_if_waiting():
#     """
#     If two non-matching cards are showing, pause briefly then flip them back.
#     Called at the top of each rerun cycle so the delay is visible.
#     """
#     if st.session_state.get("waiting", False):
#         time.sleep(0.7)  # brief pause so the player sees the wrong pair
#         for idx in st.session_state.flipped_indices:
#             st.session_state.cards[idx]["flipped"] = False
#         st.session_state.flipped_indices = []
#         st.session_state.waiting = False


# def on_card_click(card_idx: int):
#     """
#     Handle a card click event:
#     - Ignore if card is already matched/flipped, or waiting to flip back.
#     - Flip the card; if it's the second flip, call check_match().
#     """
#     if st.session_state.waiting:
#         return
#     card = st.session_state.cards[card_idx]
#     if card["matched"] or card["flipped"]:
#         return
#     if len(st.session_state.flipped_indices) >= 2:
#         return

#     # Flip this card face-up
#     st.session_state.cards[card_idx]["flipped"] = True
#     st.session_state.flipped_indices.append(card_idx)

#     if len(st.session_state.flipped_indices) == 2:
#         check_match()


# def render_board():
#     """
#     Draw the card grid using Streamlit columns.
#     Each card is a button. Appearance varies by state: hidden / flipped / matched.
#     """
#     cards = st.session_state.cards
#     cols_count = st.session_state.cols

#     for row_start in range(0, len(cards), cols_count):
#         row_cards = cards[row_start: row_start + cols_count]
#         cols = st.columns(cols_count)
#         for col_idx, card in enumerate(row_cards):
#             with cols[col_idx]:
#                 if card["matched"]:
#                     # Show emoji, green border (matched)
#                     st.markdown('<div class="card-matched">', unsafe_allow_html=True)
#                     st.button(card["emoji"], key=f"card_{card['id']}", disabled=True)
#                     st.markdown('</div>', unsafe_allow_html=True)
#                 elif card["flipped"]:
#                     # Show emoji, purple border (face-up, not yet matched)
#                     st.markdown('<div class="card-flipped">', unsafe_allow_html=True)
#                     st.button(card["emoji"], key=f"card_{card['id']}",
#                               on_click=on_card_click, args=(card["id"],))
#                     st.markdown('</div>', unsafe_allow_html=True)
#                 else:
#                     # Face-down card — show "?" symbol
#                     st.markdown('<div class="card-btn">', unsafe_allow_html=True)
#                     st.button("?", key=f"card_{card['id']}",
#                               on_click=on_card_click, args=(card["id"],))
#                     st.markdown('</div>', unsafe_allow_html=True)


# def render_stats():
#     """Display live stats: timer, score, moves, pairs found."""
#     elapsed = int(time.time() - st.session_state.start_time) if st.session_state.game_active else st.session_state.elapsed
#     c1, c2, c3, c4 = st.columns(4)
#     with c1:
#         st.markdown(f'<div class="stat-box"><div class="stat-label">⏱ Time</div><div class="stat-value">{elapsed}s</div></div>', unsafe_allow_html=True)
#     with c2:
#         st.markdown(f'<div class="stat-box"><div class="stat-label">⭐ Score</div><div class="stat-value">{st.session_state.score}</div></div>', unsafe_allow_html=True)
#     with c3:
#         st.markdown(f'<div class="stat-box"><div class="stat-label">🔄 Moves</div><div class="stat-value">{st.session_state.moves}</div></div>', unsafe_allow_html=True)
#     with c4:
#         matched = st.session_state.matched_count
#         total = st.session_state.total_pairs
#         st.markdown(f'<div class="stat-box"><div class="stat-label">✅ Pairs</div><div class="stat-value">{matched}/{total}</div></div>', unsafe_allow_html=True)


# def render_leaderboard():
#     """
#     Fetch the top scores from SQLite and display them.

#     WHY fetch from DB here instead of session_state?
#     - The DB holds ALL-TIME scores, not just from the current browser session.
#     - Every call reflects the latest data without needing a full page reload.
#     """
#     st.markdown("### 🏆 Leaderboard")

#     # Always pull fresh data straight from the database
#     scores = fetch_top_scores(10)

#     if not scores:
#         st.markdown('<div class="msg-info">No scores yet. Finish a game to appear here!</div>', unsafe_allow_html=True)
#         return

#     for i, entry in enumerate(scores):
#         cls = "leaderboard-row top" if i == 0 else "leaderboard-row"
#         medal = ["🥇","🥈","🥉"][i] if i < 3 else f"#{i+1}"
#         # entry keys come from the SELECT columns: player, score, moves, difficulty, time_secs
#         st.markdown(
#             f'<div class="{cls}">' +
#             f'<span>{medal} <b>{entry["player"]}</b></span>' +
#             f'<span>{entry["difficulty"]}</span>' +
#             f'<span>⭐ {entry["score"]} pts</span>' +
#             f'<span>🔄 {entry["moves"]} moves</span>' +
#             f'<span>⏱ {entry["time_secs"]}s</span>' +
#             '</div>',
#             unsafe_allow_html=True,
#         )


# # ─────────────────────────────────────────────
# # MAIN APP
# # ─────────────────────────────────────────────

# def main():
#     # Title
#     st.markdown('<h1 class="title">🧠 Memory Challenge</h1>', unsafe_allow_html=True)
#     st.markdown('<div class="subtitle">Flip cards · Find pairs · Beat your score</div>', unsafe_allow_html=True)

#     # ── Sidebar controls ──────────────────────
#     with st.sidebar:
#         st.markdown("## ⚙️ Game Controls")
#         difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"],
#                                   index=0, key="difficulty_select")

#         if st.button("▶ Start Game", use_container_width=True, type="primary"):
#             initialize_game(difficulty)

#         if st.session_state.get("game_active") or st.session_state.get("game_over"):
#             if st.button("🔄 Restart Game", use_container_width=True):
#                 initialize_game(st.session_state.difficulty)

#             if st.button("⏹ End Game", use_container_width=True):
#                 st.session_state.game_active = False
#                 st.session_state.game_over = False
#                 st.session_state.elapsed = int(time.time() - st.session_state.get("start_time", time.time()))

#         st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
#         render_leaderboard()

#     # ── Pre-game splash ───────────────────────
#     if not st.session_state.get("game_active") and not st.session_state.get("game_over"):
#         st.markdown("""
#         <div style='text-align:center; padding: 2rem 1rem 1rem;'>
#             <div style='font-size:5rem;'>🃏</div>
#             <h2 style='color:#a78bfa; font-family:Syne,sans-serif;'>Ready to test your memory?</h2>
#             <p style='color:#6b7280;'>Enter your name, pick a difficulty, and press <b>Start Game</b> in the sidebar.</p>
#         </div>
#         """, unsafe_allow_html=True)

#         # Player name input — stored in session_state so save_score() can read it
#         col_l, col_c, col_r = st.columns([1, 2, 1])
#         with col_c:
#             st.text_input(
#                 "👤 Your Name",
#                 key="player_name",
#                 placeholder="Enter your name...",
#                 help="This name will appear on the leaderboard when you finish a game.",
#             )

#         st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
#         render_leaderboard()
#         return

#     # ── Game-over screen ──────────────────────
#     if st.session_state.get("game_over"):
#         player = st.session_state.get("player_name", "Anonymous") or "Anonymous"
#         st.markdown(f"""
#         <div class="msg-success">
#             🎉 Well done, {player}! All {st.session_state.total_pairs} pairs matched!<br>
#             Score: {st.session_state.score} pts · Moves: {st.session_state.moves} · Time: {st.session_state.elapsed}s
#         </div>
#         """, unsafe_allow_html=True)
#         st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
#         render_leaderboard()
#         return

#     # ── Active game ───────────────────────────
#     # 1. Handle pending flip-back before drawing anything
#     flip_back_if_waiting()

#     # 2. Stats bar
#     render_stats()
#     st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

#     # 3. Card board
#     render_board()

#     # 4. Auto-refresh timer while game is active (every 1 second)
#     #    We use a subtle empty placeholder to trigger a rerun for the clock.
#     if st.session_state.game_active:
#         time.sleep(1)
#         st.rerun()


# # ─────────────────────────────────────────────
# # ENTRY POINT
# # ─────────────────────────────────────────────
# if __name__ == "__main__":
#     # ── Database bootstrap ──────────────────────────────────────
#     # init_db() is safe to call on every script run because it uses
#     # "CREATE TABLE IF NOT EXISTS" — it only creates the table once.
#     init_db()

#     # ── Session-state bootstrap ─────────────────────────────────
#     # These keys must exist before main() tries to read them.
#     if "game_active" not in st.session_state:
#         st.session_state.game_active = False
#     if "game_over" not in st.session_state:
#         st.session_state.game_over = False
#     if "player_name" not in st.session_state:
#         st.session_state.player_name = ""
#     # leaderboard is now always fetched live from the DB — no session cache needed at boot
#     if "leaderboard" not in st.session_state:
#         st.session_state.leaderboard = []

#     main()
    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    # """
# Interactive Memory Challenge System
# ====================================
# A fully functional memory card matching game built with Streamlit.

# WHY STREAMLIT?
# - Streamlit makes it easy to build interactive Python web apps without JavaScript.
# - It handles UI rendering, state management, and deployment out of the box.

# WHY SESSION_STATE?
# - Streamlit reruns the entire script on every user interaction.
# - session_state preserves game data (cards, score, moves, timer) across reruns.
# - Without it, the game would reset on every click.

# WHY RANDOM.SHUFFLE()?
# - Ensures cards appear in a different random order every game.
# - Makes the game fair and replayable.
# """

# import streamlit as st
# import random
# import time

# # ─────────────────────────────────────────────
# # PAGE CONFIG
# # ─────────────────────────────────────────────
# st.set_page_config(
#     page_title="Memory Challenge",
#     page_icon="🧠",
#     layout="wide",
#     initial_sidebar_state="collapsed",
# )

# # ─────────────────────────────────────────────
# # CSS STYLING
# # ─────────────────────────────────────────────
# st.markdown("""
# <style>
# @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@700;800&display=swap');

# html, body, [class*="css"] {
#     font-family: 'Space Mono', monospace;
#     background-color: #0e0e1a;
#     color: #e0e0f0;
# }
# .main { background-color: #0e0e1a; }

# h1.title {
#     font-family: 'Syne', sans-serif;
#     font-size: 2.6rem;
#     font-weight: 800;
#     background: linear-gradient(135deg, #a78bfa, #60a5fa, #34d399);
#     -webkit-background-clip: text;
#     -webkit-text-fill-color: transparent;
#     text-align: center;
#     margin-bottom: 0.2rem;
# }
# .subtitle {
#     text-align: center;
#     color: #6b7280;
#     font-size: 0.85rem;
#     margin-bottom: 1.5rem;
# }
# .stat-box {
#     background: #1a1a2e;
#     border: 1px solid #2d2d4e;
#     border-radius: 12px;
#     padding: 14px 10px;
#     text-align: center;
# }
# .stat-label {
#     font-size: 0.7rem;
#     color: #6b7280;
#     text-transform: uppercase;
#     letter-spacing: 1px;
# }
# .stat-value {
#     font-size: 1.6rem;
#     font-weight: 700;
#     color: #a78bfa;
# }
# .card-btn button {
#     width: 100% !important;
#     height: 72px !important;
#     font-size: 1.8rem !important;
#     border-radius: 12px !important;
#     background: #1a1a2e !important;
#     border: 2px solid #2d2d4e !important;
#     color: #e0e0f0 !important;
#     transition: all 0.15s ease !important;
# }
# .card-btn button:hover {
#     border-color: #a78bfa !important;
#     background: #24243e !important;
# }
# .card-matched button {
#     width: 100% !important;
#     height: 72px !important;
#     font-size: 1.8rem !important;
#     border-radius: 12px !important;
#     background: #0f2d1f !important;
#     border: 2px solid #34d399 !important;
#     color: #34d399 !important;
# }
# .card-flipped button {
#     width: 100% !important;
#     height: 72px !important;
#     font-size: 1.8rem !important;
#     border-radius: 12px !important;
#     background: #1e1b4b !important;
#     border: 2px solid #a78bfa !important;
#     color: #e0e0f0 !important;
# }
# .card-hidden button {
#     width: 100% !important;
#     height: 72px !important;
#     font-size: 1.8rem !important;
#     border-radius: 12px !important;
#     background: #1a1a2e !important;
#     border: 2px solid #2d2d4e !important;
#     color: #2d2d4e !important;
# }
# .section-divider {
#     border: none;
#     border-top: 1px solid #2d2d4e;
#     margin: 1.2rem 0;
# }
# .leaderboard-row {
#     display: flex;
#     justify-content: space-between;
#     padding: 7px 12px;
#     border-radius: 8px;
#     margin-bottom: 5px;
#     background: #1a1a2e;
#     font-size: 0.82rem;
# }
# .leaderboard-row.top { border-left: 3px solid #f59e0b; }
# .msg-success {
#     text-align: center;
#     font-size: 1.1rem;
#     color: #34d399;
#     font-weight: 700;
#     padding: 10px;
# }
# .msg-info {
#     text-align: center;
#     font-size: 0.88rem;
#     color: #60a5fa;
#     padding: 6px;
# }
# </style>
# """, unsafe_allow_html=True)

# # ─────────────────────────────────────────────
# # CONSTANTS
# # ─────────────────────────────────────────────
# DIFFICULTY_CONFIG = {
#     "Easy":   {"pairs": 6,  "cols": 4},
#     "Medium": {"pairs": 10, "cols": 5},
#     "Hard":   {"pairs": 15, "cols": 6},
# }

# EMOJI_POOL = [
#     "🐶","🐱","🦊","🐻","🐼","🦁","🐯","🦋",
#     "🌸","🍕","🎸","🚀","⚡","🎯","🎪","🏆",
#     "🌈","🔮","💎","🎭","🦄","🍀","🎲","🧩","🎨",
# ]

# # ─────────────────────────────────────────────
# # CORE GAME FUNCTIONS
# # ─────────────────────────────────────────────

# def generate_cards(num_pairs: int) -> list[dict]:
#     """
#     Create a shuffled deck of card pairs.
#     WHY random.shuffle()? So every game has a unique layout, keeping it fun.
#     Each card is a dict with id, emoji, flipped, matched.
#     """
#     chosen = random.sample(EMOJI_POOL, num_pairs)
#     deck = []
#     for i, emoji in enumerate(chosen * 2):  # each emoji appears twice
#         deck.append({
#             "id": i,
#             "emoji": emoji,
#             "flipped": False,
#             "matched": False,
#         })
#     random.shuffle(deck)  # randomise positions
#     # Re-assign IDs after shuffle so they reflect position
#     for idx, card in enumerate(deck):
#         card["id"] = idx
#     return deck


# def initialize_game(difficulty: str):
#     """
#     Set up all session_state variables for a fresh game.
#     WHY session_state? Streamlit reruns the script on every interaction;
#     session_state is the only way to keep game data alive between reruns.
#     """
#     cfg = DIFFICULTY_CONFIG[difficulty]
#     st.session_state.cards = generate_cards(cfg["pairs"])
#     st.session_state.cols = cfg["cols"]
#     st.session_state.score = 0
#     st.session_state.moves = 0
#     st.session_state.matched_count = 0
#     st.session_state.total_pairs = cfg["pairs"]
#     st.session_state.flipped_indices = []   # tracks the 1–2 currently-revealed cards
#     st.session_state.game_active = True
#     st.session_state.game_over = False
#     st.session_state.start_time = time.time()
#     st.session_state.elapsed = 0
#     st.session_state.difficulty = difficulty
#     st.session_state.waiting = False        # True while showing a wrong pair before flipping back


# def check_match():
#     """
#     Compare the two flipped cards.
#     If they match: mark both matched, award points.
#     If not: schedule a flip-back (set waiting=True) — handled on next rerun.
#     """
#     idx_a, idx_b = st.session_state.flipped_indices
#     card_a = st.session_state.cards[idx_a]
#     card_b = st.session_state.cards[idx_b]
#     st.session_state.moves += 1

#     if card_a["emoji"] == card_b["emoji"]:
#         # ✅ Match found
#         st.session_state.cards[idx_a]["matched"] = True
#         st.session_state.cards[idx_b]["matched"] = True
#         st.session_state.matched_count += 1
#         st.session_state.score += 10
#         st.session_state.flipped_indices = []

#         if st.session_state.matched_count == st.session_state.total_pairs:
#             # 🎉 All pairs found → game over
#             elapsed = time.time() - st.session_state.start_time
#             st.session_state.elapsed = int(elapsed)
#             st.session_state.game_over = True
#             st.session_state.game_active = False
#             save_score()
#     else:
#         # ❌ No match — flip both back after a short pause
#         st.session_state.waiting = True


# def save_score():
#     """Persist the current result to the leaderboard in session_state."""
#     if "leaderboard" not in st.session_state:
#         st.session_state.leaderboard = []
#     st.session_state.leaderboard.append({
#         "difficulty": st.session_state.difficulty,
#         "score": st.session_state.score,
#         "moves": st.session_state.moves,
#         "time": st.session_state.elapsed,
#     })
#     # Keep only the top 8 scores, sorted by score descending
#     st.session_state.leaderboard.sort(key=lambda x: (-x["score"], x["time"]))
#     st.session_state.leaderboard = st.session_state.leaderboard[:8]


# def flip_back_if_waiting():
#     """
#     If two non-matching cards are showing, pause briefly then flip them back.
#     Called at the top of each rerun cycle so the delay is visible.
#     """
#     if st.session_state.get("waiting", False):
#         time.sleep(0.7)  # brief pause so the player sees the wrong pair
#         for idx in st.session_state.flipped_indices:
#             st.session_state.cards[idx]["flipped"] = False
#         st.session_state.flipped_indices = []
#         st.session_state.waiting = False


# def on_card_click(card_idx: int):
#     """
#     Handle a card click event:
#     - Ignore if card is already matched/flipped, or waiting to flip back.
#     - Flip the card; if it's the second flip, call check_match().
#     """
#     if st.session_state.waiting:
#         return
#     card = st.session_state.cards[card_idx]
#     if card["matched"] or card["flipped"]:
#         return
#     if len(st.session_state.flipped_indices) >= 2:
#         return

#     # Flip this card face-up
#     st.session_state.cards[card_idx]["flipped"] = True
#     st.session_state.flipped_indices.append(card_idx)

#     if len(st.session_state.flipped_indices) == 2:
#         check_match()


# def render_board():
#     """
#     Draw the card grid using Streamlit columns.
#     Each card is a button. Appearance varies by state: hidden / flipped / matched.
#     """
#     cards = st.session_state.cards
#     cols_count = st.session_state.cols

#     for row_start in range(0, len(cards), cols_count):
#         row_cards = cards[row_start: row_start + cols_count]
#         cols = st.columns(cols_count)
#         for col_idx, card in enumerate(row_cards):
#             with cols[col_idx]:
#                 if card["matched"]:
#                     # Show emoji, green border (matched)
#                     st.markdown('<div class="card-matched">', unsafe_allow_html=True)
#                     st.button(card["emoji"], key=f"card_{card['id']}", disabled=True)
#                     st.markdown('</div>', unsafe_allow_html=True)
#                 elif card["flipped"]:
#                     # Show emoji, purple border (face-up, not yet matched)
#                     st.markdown('<div class="card-flipped">', unsafe_allow_html=True)
#                     st.button(card["emoji"], key=f"card_{card['id']}",
#                               on_click=on_card_click, args=(card["id"],))
#                     st.markdown('</div>', unsafe_allow_html=True)
#                 else:
#                     # Face-down card — show "?" symbol
#                     st.markdown('<div class="card-btn">', unsafe_allow_html=True)
#                     st.button("?", key=f"card_{card['id']}",
#                               on_click=on_card_click, args=(card["id"],))
#                     st.markdown('</div>', unsafe_allow_html=True)


# def render_stats():
#     """Display live stats: timer, score, moves, pairs found."""
#     elapsed = int(time.time() - st.session_state.start_time) if st.session_state.game_active else st.session_state.elapsed
#     c1, c2, c3, c4 = st.columns(4)
#     with c1:
#         st.markdown(f'<div class="stat-box"><div class="stat-label">⏱ Time</div><div class="stat-value">{elapsed}s</div></div>', unsafe_allow_html=True)
#     with c2:
#         st.markdown(f'<div class="stat-box"><div class="stat-label">⭐ Score</div><div class="stat-value">{st.session_state.score}</div></div>', unsafe_allow_html=True)
#     with c3:
#         st.markdown(f'<div class="stat-box"><div class="stat-label">🔄 Moves</div><div class="stat-value">{st.session_state.moves}</div></div>', unsafe_allow_html=True)
#     with c4:
#         matched = st.session_state.matched_count
#         total = st.session_state.total_pairs
#         st.markdown(f'<div class="stat-box"><div class="stat-label">✅ Pairs</div><div class="stat-value">{matched}/{total}</div></div>', unsafe_allow_html=True)


# def render_leaderboard():
#     """Show the top scores saved in this session."""
#     st.markdown("### 🏆 Leaderboard")
#     if not st.session_state.get("leaderboard"):
#         st.markdown('<div class="msg-info">No scores yet. Finish a game to appear here!</div>', unsafe_allow_html=True)
#         return
#     for i, entry in enumerate(st.session_state.leaderboard):
#         cls = "leaderboard-row top" if i == 0 else "leaderboard-row"
#         medal = ["🥇","🥈","🥉"][i] if i < 3 else f"#{i+1}"
#         st.markdown(
#             f'<div class="{cls}">'
#             f'<span>{medal} {entry["difficulty"]}</span>'
#             f'<span>⭐ {entry["score"]} pts</span>'
#             f'<span>🔄 {entry["moves"]} moves</span>'
#             f'<span>⏱ {entry["time"]}s</span>'
#             f'</div>',
#             unsafe_allow_html=True,
#         )


# # ─────────────────────────────────────────────
# # MAIN APP
# # ─────────────────────────────────────────────

# def main():
#     # Title
#     st.markdown('<h1 class="title">🧠 Memory Challenge</h1>', unsafe_allow_html=True)
#     st.markdown('<div class="subtitle">Flip cards · Find pairs · Beat your score</div>', unsafe_allow_html=True)

#     # ── Sidebar controls ──────────────────────
#     with st.sidebar:
#         st.markdown("## ⚙️ Game Controls")
#         difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"],
#                                   index=0, key="difficulty_select")

#         if st.button("▶ Start Game", use_container_width=True, type="primary"):
#             initialize_game(difficulty)

#         if st.session_state.get("game_active") or st.session_state.get("game_over"):
#             if st.button("🔄 Restart Game", use_container_width=True):
#                 initialize_game(st.session_state.difficulty)

#             if st.button("⏹ End Game", use_container_width=True):
#                 st.session_state.game_active = False
#                 st.session_state.game_over = False
#                 st.session_state.elapsed = int(time.time() - st.session_state.get("start_time", time.time()))

#         st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
#         render_leaderboard()

#     # ── Pre-game splash ───────────────────────
#     if not st.session_state.get("game_active") and not st.session_state.get("game_over"):
#         st.markdown("""
#         <div style='text-align:center; padding: 3rem 1rem;'>
#             <div style='font-size:5rem;'>🃏</div>
#             <h2 style='color:#a78bfa; font-family:Syne,sans-serif;'>Ready to test your memory?</h2>
#             <p style='color:#6b7280;'>Pick a difficulty level and press <b>Start Game</b> in the sidebar.</p>
#         </div>
#         """, unsafe_allow_html=True)
#         if st.session_state.get("leaderboard"):
#             render_leaderboard()
#         return

#     # ── Game-over screen ──────────────────────
#     if st.session_state.get("game_over"):
#         st.markdown(f"""
#         <div class="msg-success">
#             🎉 You matched all {st.session_state.total_pairs} pairs!<br>
#             Score: {st.session_state.score} pts · Moves: {st.session_state.moves} · Time: {st.session_state.elapsed}s
#         </div>
#         """, unsafe_allow_html=True)
#         render_leaderboard()
#         return

#     # ── Active game ───────────────────────────
#     # 1. Handle pending flip-back before drawing anything
#     flip_back_if_waiting()

#     # 2. Stats bar
#     render_stats()
#     st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

#     # 3. Card board
#     render_board()

#     # 4. Auto-refresh timer while game is active (every 1 second)
#     #    We use a subtle empty placeholder to trigger a rerun for the clock.
#     if st.session_state.game_active:
#         time.sleep(1)
#         st.rerun()


# # ─────────────────────────────────────────────
# # ENTRY POINT
# # ─────────────────────────────────────────────
# if __name__ == "__main__":
#     # Initialise session keys that must exist before main() runs
#     if "game_active" not in st.session_state:
#         st.session_state.game_active = False
#     if "game_over" not in st.session_state:
#         st.session_state.game_over = False
#     if "leaderboard" not in st.session_state:
#         st.session_state.leaderboard = []

#     main()