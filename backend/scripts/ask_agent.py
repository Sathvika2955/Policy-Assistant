"""Talk to the agent from the terminal.
Run:  python -m scripts.ask_agent "How many leave days do I have left?"
Uses the demo 'employee' account."""
import sys

from app import config
from app.agent import run_agent
from app.database import connect, init_db

if not config.GEMINI_API_KEY:
    sys.exit("GEMINI_API_KEY is not set. Put it in backend/.env and try again.")

init_db()
conn = connect()
row = conn.execute("SELECT id, username, full_name FROM users WHERE username = 'employee'").fetchone()
conn.close()
user = dict(row)

question = " ".join(sys.argv[1:]) or "How many sick days do I get, and how many have I used?"
print(f"Q: {question}\n")
answer, sources = run_agent(question, [], user)
print(f"A: {answer}\n")
for s in sources:
    print(f"   source: {s['source']} (score {s['score']})")
