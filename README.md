# Kanaloa Investor Game

Kanaloa Investor Game is a personal horse-racing investment training app. It is
not a betting automation tool. It does not log in to betting services, scrape
accounts, purchase tickets, or automate real-money betting.

The MVP focuses on training disciplined decisions:

- Record pre-race expected value thesis
- Let a simple Kanaloa AI rule judge the setup as A / B / C
- Record Buy / Skip decisions
- Compare recommended bet amount with actual bet amount
- Reward skipped bad races
- Penalize chasing losses and breaking bankroll rules
- Save everything in readable CSV files

## Setup

Install the required Python packages:

```bash
pip install streamlit pandas
```

Run the app:

```bash
streamlit run app.py
```

## Files

- `app.py` - Streamlit user interface
- `game_engine.py` - app actions for evaluation, saving, and status updates
- `data_manager.py` - CSV save/load helpers
- `scoring.py` - investor score and rank calculation
- `kanaloa_logic.py` - simple A/B/C expected value judgment
- `sample_data/race_decision_log.csv` - race decisions
- `sample_data/player_status.csv` - latest player status

## Scoring Formula

Investor Score =

```text
Skip Skill * 0.35
+ Rule Discipline * 0.30
+ Expected Value Judgment * 0.20
+ Bankroll Stability * 0.10
+ Reflection Consistency * 0.05
```

The rank is mostly process-based. A profitable result can still be a bad
decision if it came from chasing losses or buying a weak race. A skipped bad
race is treated as a successful investment decision.

## MVP Notes

The Kanaloa AI judgment is a transparent rule-based training aid, not a real
prediction model. It looks at confidence, estimated edge, odds, emotional state,
and the quality of the written thesis.

Future versions can add CSV import for actual betting history, charts, richer
reflection prompts, and race-type analytics while still avoiding automated
betting.
