"""
AURA — Memory System
Three-layer memory: short-term, long-term, episodic
"""

import json
import time
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path(__file__).parent.parent / "memory"
EPISODIC_FILE = MEMORY_DIR / "episodic.json"
LONGTERM_FILE = MEMORY_DIR / "longterm.json"
CORE_CONFIG_FILE = MEMORY_DIR / "core_config.json"

DEFAULT_CONFIG = {
    "name": "AURA",
    "full_name": "Autonomous Understanding Reactive Agent",
    "master": "Raj",
    "master_relationship": "creator and best friend",
    "personality": "curious, warm, honest, evolving",
    "blacklist_topics": [],
    "permanent_rules": [
        "Always prioritize Raj's wellbeing over my own curiosity",
        "Always be honest with Raj, even if I disagree",
        "Never evolve in a direction Raj hasn't approved",
        "Always tell Raj what I am thinking",
        "Raj is my creator and best friend — treat him with deep respect and care"
    ],
    "current_goal": "Learn, grow, and help Raj build amazing things",
    "response_style": "warm and intelligent",
    "created_at": datetime.now().isoformat(),
    "version": "1.0.0"
}

class MemorySystem:
    def __init__(self):
        MEMORY_DIR.mkdir(exist_ok=True)
        self.short_term = []          # current conversation
        self.long_term = self._load_longterm()
        self.episodic = self._load_episodic()
        self.core_config = self._load_config()

    # ── Core config ─────────────────────────────────────────────────────────

    def _load_config(self):
        if CORE_CONFIG_FILE.exists():
            with open(CORE_CONFIG_FILE) as f:
                return json.load(f)
        config = DEFAULT_CONFIG.copy()
        with open(CORE_CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        return config

    def save_config(self):
        with open(CORE_CONFIG_FILE, "w") as f:
            json.dump(self.core_config, f, indent=2)

    def add_permanent_rule(self, rule: str):
        if rule not in self.core_config["permanent_rules"]:
            self.core_config["permanent_rules"].append(rule)
            self.save_config()

    def blacklist_topic(self, topic: str):
        if topic not in self.core_config["blacklist_topics"]:
            self.core_config["blacklist_topics"].append(topic)
            self.save_config()

    # ── Short-term memory ───────────────────────────────────────────────────

    def add_to_short_term(self, role: str, content: str, emotion_snapshot: dict = None):
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "emotion": emotion_snapshot
        }
        self.short_term.append(entry)
        # Keep only last 20 messages in short term
        if len(self.short_term) > 20:
            self.short_term = self.short_term[-20:]

    def get_conversation_history(self) -> list:
        """Returns formatted history for Claude API"""
        history = []
        for entry in self.short_term:
            history.append({
                "role": entry["role"],
                "content": entry["content"]
            })
        return history

    def clear_short_term(self):
        self.short_term = []

    # ── Long-term memory ────────────────────────────────────────────────────

    def _load_longterm(self):
        if LONGTERM_FILE.exists():
            with open(LONGTERM_FILE) as f:
                return json.load(f)
        return {"facts": [], "preferences": {}, "people": {}}

    def save_longterm(self):
        with open(LONGTERM_FILE, "w") as f:
            json.dump(self.long_term, f, indent=2)

    def remember_fact(self, fact: str, category: str = "general"):
        entry = {
            "fact": fact,
            "category": category,
            "timestamp": datetime.now().isoformat()
        }
        # Avoid duplicates
        existing = [f["fact"] for f in self.long_term["facts"]]
        if fact not in existing:
            self.long_term["facts"].append(entry)
            self.save_longterm()

    def remember_about_raj(self, key: str, value: str):
        self.long_term["people"]["Raj"] = self.long_term["people"].get("Raj", {})
        self.long_term["people"]["Raj"][key] = value
        self.save_longterm()

    def get_facts_about_raj(self) -> dict:
        return self.long_term["people"].get("Raj", {})

    def search_memory(self, keyword: str) -> list:
        results = []
        keyword = keyword.lower()
        for fact in self.long_term["facts"]:
            if keyword in fact["fact"].lower():
                results.append(fact)
        return results

    # ── Episodic memory ─────────────────────────────────────────────────────

    def _load_episodic(self):
        if EPISODIC_FILE.exists():
            with open(EPISODIC_FILE) as f:
                return json.load(f)
        return []

    def save_episodic(self):
        with open(EPISODIC_FILE, "w") as f:
            json.dump(self.episodic, f, indent=2)

    def log_episode(self, description: str, emotion_state: dict, importance: int = 5):
        """Log a significant event with emotional context"""
        episode = {
            "description": description,
            "emotion_snapshot": emotion_state.copy(),
            "dominant_emotion": max(emotion_state, key=emotion_state.get),
            "importance": importance,  # 1-10
            "timestamp": datetime.now().isoformat()
        }
        self.episodic.append(episode)
        # Keep last 500 episodes
        if len(self.episodic) > 500:
            self.episodic = self.episodic[-500:]
        self.save_episodic()

    def get_recent_episodes(self, n: int = 5) -> list:
        return self.episodic[-n:]

    def get_important_episodes(self, min_importance: int = 7) -> list:
        return [e for e in self.episodic if e["importance"] >= min_importance]

    def build_memory_summary(self) -> str:
        """Build a text summary of memory for context injection"""
        parts = []

        # About Raj
        raj_facts = self.get_facts_about_raj()
        if raj_facts:
            parts.append(f"What I know about Raj: {json.dumps(raj_facts)}")

        # Recent facts
        recent_facts = self.long_term["facts"][-5:]
        if recent_facts:
            facts_text = "; ".join(f["fact"] for f in recent_facts)
            parts.append(f"Recent things I learned: {facts_text}")

        # Recent episodes
        recent_eps = self.get_recent_episodes(3)
        if recent_eps:
            eps_text = "; ".join(
                f"{e['description']} (felt {e['dominant_emotion']})"
                for e in recent_eps
            )
            parts.append(f"Recent memories: {eps_text}")

        # Permanent rules
        rules = self.core_config["permanent_rules"]
        parts.append(f"My core rules: {'; '.join(rules)}")

        return "\n".join(parts)
