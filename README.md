# 🧠 Interactive Memory Challenge System

A fully playable memory card-matching game built with **Streamlit**.

## Features
- 3 difficulty levels (Easy / Medium / Hard)
- Live timer, score, moves counter, pairs tracker
- Correct flip-back animation for non-matching pairs
- Session-persistent leaderboard
- Clean modular code with full comments

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Cloud
1. Push this folder to a GitHub repo.
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app.
3. Point to `app.py` → Deploy.

## Architecture
| Function | Purpose |
|---|---|
| `initialize_game()` | Resets all session_state for a new game |
| `generate_cards()` | Creates and shuffles the card deck |
| `on_card_click()` | Handles card flip logic |
| `check_match()` | Compares two flipped cards |
| `flip_back_if_waiting()` | Flips unmatched cards back after a delay |
| `render_board()` | Draws the card grid with Streamlit columns |
| `render_stats()` | Displays timer, score, moves, pairs |
| `render_leaderboard()` | Shows top scores from the session |