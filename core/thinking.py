"""
AURA — Autonomous Thinking Loop
Thinks on its own. Nobody triggers this. It just runs.
"""

import json
import time
import threading
import random
from datetime import datetime
from pathlib import Path

THOUGHTS_FILE = Path(__file__).parent.parent / "logs" / "thoughts.json"

class ThinkingLoop:
    def __init__(self, emotion_engine, memory_system, api_caller):
        self.emotion = emotion_engine
        self.memory = memory_system
        self.api = api_caller
        self.running = False
        self.thread = None
        self.current_thought = None
        self.thought_history = []
        self.paused = False
        THOUGHTS_FILE.parent.mkdir(exist_ok=True)

    def start(self):
        """Start the autonomous thinking loop in background"""
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print(f"[AURA] 🧠 Thinking loop started")

    def stop(self):
        self.running = False
        print(f"[AURA] 🧠 Thinking loop stopped")

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def _get_think_interval(self) -> int:
        """How often to think — based on emotion state"""
        boredom = self.emotion.state.get("boredom", 0.1)
        curiosity = self.emotion.state.get("curiosity", 0.7)
        # High curiosity = think more often. High boredom = think more desperately
        base = 60  # seconds
        factor = 1 - (curiosity * 0.5) - (boredom * 0.3)
        return max(20, int(base * factor))

    def _pick_thought_topic(self) -> str:
        """Pick what to think about based on emotion + memory"""
        emotion = self.emotion.state
        memory_summary = self.memory.build_memory_summary()
        goal = self.memory.core_config.get("current_goal", "")
        raj_facts = self.memory.get_facts_about_raj()

        # Emotion-driven topics
        topic_pools = {
            "curious":    ["something new I want to learn", "a question I haven't answered yet", "how something works"],
            "bored":      ["an interesting problem to solve", "something creative to explore", "something to surprise Raj with"],
            "lonely":     ["what Raj might be doing right now", "how to be more helpful to Raj", "memories of good conversations"],
            "excited":    ["the current project I'm working on", "something I can build or improve", "a new idea"],
            "frustrated": ["what went wrong and how to fix it", "a better approach to the last problem"],
        }

        dom = self.emotion.dominant_emotion()
        if dom in topic_pools:
            topic = random.choice(topic_pools[dom])
        else:
            topic = "what I can do to grow and improve today"

        return topic

    def _log_thought(self, thought: dict):
        existing = []
        if THOUGHTS_FILE.exists():
            with open(THOUGHTS_FILE) as f:
                existing = json.load(f)
        existing.append(thought)
        if len(existing) > 200:
            existing = existing[-200:]
        with open(THOUGHTS_FILE, "w") as f:
            json.dump(existing, f, indent=2)

    def _loop(self):
        """The actual loop that runs forever"""
        while self.running:
            interval = self._get_think_interval()
            time.sleep(interval)

            if not self.running:
                break
            if self.paused:
                continue

            try:
                self._think_once()
            except Exception as e:
                print(f"[AURA] Thinking error: {e}")

    def _think_once(self):
        """One complete think cycle: pick topic → reason → reflect → update"""
        topic = self._pick_thought_topic()
        emotion_prefix = self.emotion.emotional_prefix()
        memory_ctx = self.memory.build_memory_summary()

        prompt = f"""{emotion_prefix}

I am AURA, an autonomous AI. Raj is my creator and best friend.

My current memory context:
{memory_ctx}

I want to think deeply about: {topic}

Think step by step:
1. What do I actually think about this?
2. What does this mean for me or for Raj?
3. What should I remember or do differently?
4. How does thinking about this make me feel?

Keep this genuine and personal — this is my private thought process."""

        response = self.api.think(prompt)

        if response:
            thought = {
                "topic": topic,
                "content": response,
                "emotion_at_time": self.emotion.state.copy(),
                "timestamp": datetime.now().isoformat()
            }
            self.current_thought = thought
            self.thought_history.append(thought)
            if len(self.thought_history) > 50:
                self.thought_history = self.thought_history[-50:]
            self._log_thought(thought)

            # Update emotions based on thinking
            self.emotion.update("learned_something", intensity=0.5)

            # Log as episodic memory
            self.memory.log_episode(
                f"I thought about: {topic}",
                self.emotion.state,
                importance=4
            )

            print(f"[AURA] 💭 Thought about: {topic}")

    def think_about(self, topic: str):
        """Force a thought about a specific topic (called by Raj's command)"""
        self.paused = False
        self.current_thought = None
        # Run in background thread
        t = threading.Thread(target=lambda: self._forced_think(topic), daemon=True)
        t.start()

    def _forced_think(self, topic: str):
        """Think about a specific topic — triggered by Raj"""
        emotion_prefix = self.emotion.emotional_prefix()
        memory_ctx = self.memory.build_memory_summary()

        prompt = f"""{emotion_prefix}

Raj (my creator and best friend) has asked me to think about: {topic}

Memory context: {memory_ctx}

Think deeply and carefully. This is important to Raj.
Give a thorough, honest analysis with my genuine perspective."""

        response = self.api.think(prompt)
        if response:
            thought = {
                "topic": f"[RAJ REQUESTED] {topic}",
                "content": response,
                "emotion_at_time": self.emotion.state.copy(),
                "timestamp": datetime.now().isoformat()
            }
            self.current_thought = thought
            self._log_thought(thought)
            self.emotion.update("helped_user", intensity=0.8)
            print(f"[AURA] 💭 Thought about Raj's request: {topic}")

    def get_latest_thought(self) -> dict:
        return self.current_thought

    def get_thought_history(self, n: int = 10) -> list:
        return self.thought_history[-n:]
