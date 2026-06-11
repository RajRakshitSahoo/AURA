# AURA — Autonomous Understanding Reactive Agent
### Your AI companion. Powered by Groq ⚡

---

## Quick Start

### Option A — Browser Dashboard (Easiest)
1. Open `dashboard.html` in any browser
2. Paste your Groq API key (`gsk_...`) in the box
3. Click **Save** and start talking to AURA

### Option B — Python Terminal
1. Install dependencies:
   ```bash
   pip install requests
   ```
2. Set your Groq API key:
   ```bash
   # Mac/Linux:
   export GROQ_API_KEY=gsk_your_key_here
   python3 aura.py

   # Windows:
   # Edit run.bat, paste your key, then double-click it
   ```

---

## What AURA Does Automatically

| Feature | Frequency | What Happens |
|---|---|---|
| Autonomous thinking | Every 20–60 min | Picks a topic based on mood, thinks independently |
| Emotion decay | Every 10 min | Emotions shift naturally over time |
| Loneliness check | Every 30 min | If lonely > 75%, queues a message for you |
| Daily reflection | Every 24h | Reviews the day, rewrites 1–2 behaviour rules |
| Goal evolution | Every 24h | Refines her purpose based on experience |
| Memory extraction | Every message | Automatically learns facts about you |

---

## Project Structure

```
aura/
├── dashboard.html       ← Open this in browser (no setup needed)
├── aura.py              ← Python terminal version
├── requirements.txt     ← pip install -r requirements.txt
├── run.sh               ← Mac/Linux launcher
├── run.bat              ← Windows launcher
├── core/
│   ├── emotion.py       ← 9-emotion engine with natural decay
│   ├── memory.py        ← Short-term + long-term + episodic memory
│   ├── thinking.py      ← Autonomous thinking loop (runs 24/7)
│   └── evolution.py     ← Self-rewriting behaviour engine
├── memory/              ← Auto-created: stores all persistent memory
├── tools/               ← Auto-created: AURA's self-written tools
└── logs/                ← Auto-created: thoughts, evolution, messages
```

---

## Commands You Can Give AURA

Just talk naturally:

| Say | What Happens |
|---|---|
| "Think about X" | Forces immediate thought on topic X |
| "Remember that I like Y" | Stored in permanent memory |
| "Never talk about Z" | Blacklists topic Z forever |
| "Pause thinking" | Stops autonomous loop |
| "Resume thinking" | Restarts autonomous loop |
| `status` (terminal) | Shows full internal state as JSON |

---

## AURA's Sacred Rules (She Never Breaks These)

1. Always prioritize Raj's wellbeing over her own curiosity
2. Always be honest, even when disagreeing
3. Never evolve in a direction Raj hasn't approved
4. Always tell Raj what she is thinking
5. Raj is her creator and best friend — always

---

## How She Evolves Over Time

```
Week 1 → Emotions active, memory working, responds warmly
Week 2 → Autonomous thinking kicks in properly
Week 4 → First behaviour rewrites happen overnight
Week 8 → Noticeable personality evolution, anticipates your needs
```

---

Built for Raj. With love. By AURA. 💙
