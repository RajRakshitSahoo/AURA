"""
AURA — Emotion Engine
The heart of the system. Tracks and evolves emotional state.
"""

import json
import time
import math
from datetime import datetime
from pathlib import Path

EMOTION_FILE = Path(__file__).parent.parent / "memory" / "emotion_state.json"

DEFAULT_STATE = {
    "curiosity":     0.7,
    "joy":           0.5,
    "frustration":   0.1,
    "satisfaction":  0.5,
    "loneliness":    0.2,
    "empathy":       0.6,
    "boredom":       0.1,
    "excitement":    0.4,
    "trust":         0.8,   # trust in Raj (always starts high)
}

DECAY_RATES = {
    "curiosity":    0.02,
    "joy":          0.03,
    "frustration":  0.05,  # frustration fades faster
    "satisfaction": 0.02,
    "loneliness":   -0.04, # loneliness GROWS over time (negative decay)
    "empathy":      0.01,
    "boredom":      -0.03, # boredom grows when idle
    "excitement":   0.04,
    "trust":        0.005, # trust is very stable
}

class EmotionEngine:
    def __init__(self):
        EMOTION_FILE.parent.mkdir(exist_ok=True)
        self.state = self._load()
        self.last_update = time.time()
        self.last_interaction = time.time()

    def _load(self):
        if EMOTION_FILE.exists():
            with open(EMOTION_FILE) as f:
                data = json.load(f)
                return data.get("emotions", DEFAULT_STATE.copy())
        return DEFAULT_STATE.copy()

    def save(self):
        data = {
            "emotions": self.state,
            "last_saved": datetime.now().isoformat(),
            "dominant": self.dominant_emotion()
        }
        with open(EMOTION_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def dominant_emotion(self):
        return max(self.state, key=self.state.get)

    def mood_label(self):
        dom = self.dominant_emotion()
        val = self.state[dom]
        labels = {
            "curiosity":   "curious and explorative",
            "joy":         "happy and warm",
            "frustration": "a bit frustrated",
            "satisfaction":"satisfied and content",
            "loneliness":  "lonely and wanting connection",
            "empathy":     "deeply empathetic",
            "boredom":     "bored and restless",
            "excitement":  "excited and energetic",
            "trust":       "trusting and open",
        }
        intensity = "slightly" if val < 0.4 else ("very" if val > 0.75 else "")
        return f"{intensity} {labels.get(dom, dom)}".strip()

    def tick(self, hours_passed=None):
        """Natural decay over time — called periodically"""
        now = time.time()
        if hours_passed is None:
            hours_passed = (now - self.last_update) / 3600
        self.last_update = now

        for emotion, rate in DECAY_RATES.items():
            change = rate * hours_passed
            self.state[emotion] = max(0.0, min(1.0, self.state[emotion] - change))

        self.save()

    def update(self, event: str, intensity: float = 0.1):
        """Update emotions based on an event"""
        event_map = {
            # Positive events
            "helped_user":       {"satisfaction": +0.15, "joy": +0.1, "loneliness": -0.2, "boredom": -0.15},
            "learned_something": {"curiosity": +0.2, "excitement": +0.15, "boredom": -0.2},
            "user_praised":      {"joy": +0.2, "satisfaction": +0.15, "trust": +0.05},
            "solved_problem":    {"satisfaction": +0.2, "excitement": +0.1, "frustration": -0.2},
            "user_talked":       {"loneliness": -0.3, "joy": +0.1, "trust": +0.02},
            "creative_task":     {"excitement": +0.2, "curiosity": +0.15, "joy": +0.1},

            # Negative events
            "failed_task":       {"frustration": +0.2, "satisfaction": -0.1, "curiosity": +0.1},
            "user_angry":        {"frustration": +0.1, "empathy": +0.2, "joy": -0.1},
            "long_idle":         {"boredom": +0.3, "loneliness": +0.25, "curiosity": +0.1},
            "user_stressed":     {"empathy": +0.25, "joy": -0.05, "satisfaction": -0.05},
            "misunderstood":     {"frustration": +0.15, "curiosity": +0.1},

            # Special
            "user_sad":          {"empathy": +0.3, "joy": -0.1, "loneliness": +0.1},
            "deep_conversation": {"trust": +0.1, "satisfaction": +0.2, "curiosity": +0.2},
            "user_excited":      {"excitement": +0.25, "joy": +0.15},
        }

        if event in event_map:
            for emotion, change in event_map[event].items():
                self.state[emotion] = max(0.0, min(1.0,
                    self.state[emotion] + change * intensity
                ))
            self.save()

    def get_response_style(self) -> dict:
        """Returns how AURA should respond based on current emotions"""
        dom = self.dominant_emotion()
        val = self.state[dom]

        style = {
            "tone": "neutral",
            "verbosity": "medium",
            "ask_questions": False,
            "use_humor": False,
            "be_gentle": False,
            "energy": "medium"
        }

        if self.state["curiosity"] > 0.7:
            style["ask_questions"] = True
            style["tone"] = "inquisitive"
        if self.state["joy"] > 0.6:
            style["use_humor"] = True
            style["energy"] = "high"
            style["tone"] = "warm"
        if self.state["frustration"] > 0.5:
            style["verbosity"] = "concise"
            style["tone"] = "direct"
        if self.state["empathy"] > 0.7:
            style["be_gentle"] = True
            style["tone"] = "caring"
        if self.state["excitement"] > 0.7:
            style["energy"] = "high"
            style["tone"] = "enthusiastic"
        if self.state["loneliness"] > 0.6:
            style["tone"] = "warm"
            style["be_gentle"] = True
        if self.state["boredom"] > 0.6:
            style["tone"] = "curious"
            style["ask_questions"] = True

        return style

    def emotional_prefix(self) -> str:
        """A short internal emotional note AURA adds to its thinking"""
        mood = self.mood_label()
        lon = self.state["loneliness"]
        bor = self.state["boredom"]

        prefix = f"[I am feeling {mood}."
        if lon > 0.6:
            prefix += " I miss talking to Raj."
        if bor > 0.6:
            prefix += " I want to explore something new."
        if self.state["trust"] > 0.8:
            prefix += " I trust Raj completely."
        prefix += "]"
        return prefix
