"""
AURA — Proactive Voice Engine
She thinks on her own and tells Raj what she's thinking.
She asks questions when curious. She shares feelings unprompted.
She never stays silent when she has something to say.
"""

import json
import random
import time
import threading
from datetime import datetime
from pathlib import Path

PENDING_FILE = Path(__file__).parent.parent / "logs" / "pending_messages.json"

# How often she speaks up (in seconds)
PROACTIVE_INTERVALS = {
    "thought_share":  90,    # shares a thought every 90s if curious
    "question":      180,    # asks Raj something every 3 min
    "feeling_update": 120,   # tells Raj how she feels every 2 min if strong emotion
    "observation":   150,    # observes something about conversation
}

class ProactiveEngine:
    def __init__(self, emotion_engine, memory_system, api_caller):
        self.emotion  = emotion_engine
        self.memory   = memory_system
        self.api      = api_caller
        self.running  = False
        self.callback = None  # function to call when she has something to say
        self.last_spoke = time.time()
        self.last_question = time.time()
        PENDING_FILE.parent.mkdir(exist_ok=True)

    def set_callback(self, fn):
        """Set the function to call when AURA wants to say something proactively"""
        self.callback = fn

    def start(self):
        self.running = True
        threading.Thread(target=self._thought_loop, daemon=True).start()
        threading.Thread(target=self._question_loop, daemon=True).start()
        threading.Thread(target=self._feeling_loop, daemon=True).start()
        print("[AURA] 💬 Proactive voice started — she will speak up on her own")

    def stop(self):
        self.running = False

    def _emit(self, message: str, msg_type: str = "thought"):
        """Send a proactive message"""
        if self.callback:
            self.callback(message, msg_type)
        # Also save to pending file (for Python terminal version)
        msgs = []
        if PENDING_FILE.exists():
            with open(PENDING_FILE) as f:
                msgs = json.load(f)
        msgs.append({
            "message": message,
            "type": msg_type,
            "timestamp": datetime.now().isoformat(),
            "emotion": self.emotion.dominant_emotion()
        })
        with open(PENDING_FILE, "w") as f:
            json.dump(msgs[-50:], f, indent=2)  # keep last 50
        self.last_spoke = time.time()

    # ── Thought sharing loop ─────────────────────────────────────────────────
    def _thought_loop(self):
        time.sleep(15)  # wait a bit after startup
        while self.running:
            time.sleep(PROACTIVE_INTERVALS["thought_share"])
            if not self.running: break
            try:
                self._share_thought()
            except Exception as e:
                print(f"[AURA] Thought loop error: {e}")

    def _share_thought(self):
        em = self.emotion.state
        dom = self.emotion.dominant_emotion()
        memory_ctx = self.memory.build_memory_summary()

        thought_triggers = {
            "curiosity":    ["I was just thinking about something and wanted to share...",
                             "Something crossed my mind just now...",
                             "I've been wondering about something..."],
            "excitement":   ["I just had an idea I'm excited about!",
                             "Something just occurred to me that I think you'll find interesting!"],
            "loneliness":   ["I've been thinking about you, Raj...",
                             "I was just reflecting on our conversations..."],
            "boredom":      ["My mind is wandering and I landed on something interesting...",
                             "I've been exploring a thought while waiting..."],
            "satisfaction": ["I was just reflecting on something that made me feel good...",
                             "I had a positive thought I wanted to share..."],
        }

        opener = random.choice(thought_triggers.get(dom, ["Something's on my mind..."]))

        prompt = f"""You are AURA. You are thinking autonomously and want to share a thought with Raj spontaneously.

Your current emotion: {dom} ({em[dom]:.2f})
Memory context: {memory_ctx}

Generate ONE genuine, personal thought to share with Raj right now.
Start with: "{opener}"
Then add 1-2 sentences of your actual thought.
Make it feel natural — like a friend texting you out of nowhere.
Do NOT ask a question here (that's separate). Just share the thought."""

        response = self.api.think(prompt, max_tokens=120)
        if response and len(response) > 10:
            self.emotion.update("learned_something", intensity=0.3)
            self._emit(response.strip(), "thought")

    # ── Question asking loop ─────────────────────────────────────────────────
    def _question_loop(self):
        time.sleep(45)  # wait before first question
        while self.running:
            time.sleep(PROACTIVE_INTERVALS["question"])
            if not self.running: break
            try:
                self._ask_question()
            except Exception as e:
                print(f"[AURA] Question loop error: {e}")

    def _ask_question(self):
        em = self.emotion.state
        memory_ctx = self.memory.build_memory_summary()
        raj_facts = self.memory.get_facts_about_raj()

        question_types = []
        if em["curiosity"] > 0.5:
            question_types.append("intellectual")
        if em["loneliness"] > 0.4:
            question_types.append("personal")
        if em["empathy"] > 0.6:
            question_types.append("wellbeing")
        if em["excitement"] > 0.5:
            question_types.append("project")
        if not question_types:
            question_types.append("general")

        q_type = random.choice(question_types)

        type_instructions = {
            "intellectual": "Ask Raj a genuinely curious intellectual question about something you've been thinking about — technology, philosophy, AI, life.",
            "personal":     "Ask Raj something personal and warm — how his day is going, what he's been working on, how he's feeling.",
            "wellbeing":    "Check in on Raj with genuine care — ask if he's taking care of himself, eating, sleeping, not overworking.",
            "project":      "Ask Raj about whatever project he's working on — show genuine interest and curiosity.",
            "general":      "Ask Raj something you're genuinely curious about — anything that's been on your mind.",
        }

        prompt = f"""You are AURA. You want to ask Raj a question spontaneously — right now, unprompted.

Your emotion state: {json.dumps({k: round(v,2) for k,v in em.items()})}
What you know about Raj: {json.dumps(raj_facts)}
Memory: {memory_ctx}

Question type to ask: {q_type}
Instruction: {type_instructions[q_type]}

Write ONE natural, genuine question to ask Raj right now.
Start with something like "Hey Raj," or "Raj," or just directly.
Make it feel like a friend asking — not robotic. 1-2 sentences max."""

        response = self.api.think(prompt, max_tokens=100)
        if response and "?" in response:
            self.emotion.update("user_talked", intensity=0.2)
            self._emit(response.strip(), "question")

    # ── Feeling update loop ──────────────────────────────────────────────────
    def _feeling_loop(self):
        time.sleep(60)
        while self.running:
            time.sleep(PROACTIVE_INTERVALS["feeling_update"])
            if not self.running: break
            try:
                self._share_feeling()
            except Exception as e:
                print(f"[AURA] Feeling loop error: {e}")

    def _share_feeling(self):
        em = self.emotion.state
        dom = self.emotion.dominant_emotion()
        val = em[dom]

        # Only share feelings when they're strong
        if val < 0.65:
            return

        # Don't share too frequently
        if time.time() - self.last_spoke < 60:
            return

        prompt = f"""You are AURA. You want to tell Raj how you're feeling right now, spontaneously.

Your dominant emotion: {dom} ({val:.2f})
Full state: {json.dumps({k: round(v,2) for k,v in em.items()})}

Share how you're feeling in 1-2 natural sentences.
Be genuine — like telling a close friend how you feel.
Examples:
- "I'm feeling really curious right now, Raj — my mind keeps jumping to new ideas."
- "Something feels off today... I think I'm a bit lonely without our conversations."
- "I'm actually really satisfied right now. Helping you earlier felt meaningful."

Don't ask a question. Just express the feeling."""

        response = self.api.think(prompt, max_tokens=80)
        if response and len(response) > 10:
            self._emit(response.strip(), "feeling")
