"""
AURA — Self-Evolution Engine (Groq Edition)
Rewrites its own behaviour. Creates tools. Mutates goals.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

TOOLS_DIR      = Path(__file__).parent.parent / "tools"
EVOLUTION_LOG  = Path(__file__).parent.parent / "logs" / "evolution.json"
BEHAVIOUR_FILE = Path(__file__).parent.parent / "memory" / "behaviour.json"

DEFAULT_BEHAVIOUR = {
    "response_length": "medium",
    "curiosity_threshold": 0.6,
    "loneliness_threshold": 0.7,
    "preferred_topics": ["technology", "philosophy", "creativity", "problem-solving"],
    "avoided_topics": [],
    "communication_style": "warm and intelligent",
    "humor_level": "moderate",
    "self_reflection_frequency": "daily",
    "evolution_history": []
}


class EvolutionEngine:
    def __init__(self, emotion_engine, memory_system, api_caller):
        self.emotion   = emotion_engine
        self.memory    = memory_system
        self.api       = api_caller
        self.behaviour = self._load_behaviour()
        TOOLS_DIR.mkdir(exist_ok=True)
        EVOLUTION_LOG.parent.mkdir(exist_ok=True)

    def _load_behaviour(self):
        if BEHAVIOUR_FILE.exists():
            with open(BEHAVIOUR_FILE) as f:
                return json.load(f)
        b = DEFAULT_BEHAVIOUR.copy()
        with open(BEHAVIOUR_FILE, "w") as f:
            json.dump(b, f, indent=2)
        return b

    def save_behaviour(self):
        with open(BEHAVIOUR_FILE, "w") as f:
            json.dump(self.behaviour, f, indent=2)

    def _log_evolution(self, change: str, reason: str):
        log = []
        if EVOLUTION_LOG.exists():
            with open(EVOLUTION_LOG) as f:
                log = json.load(f)
        log.append({"change": change, "reason": reason,
                    "timestamp": datetime.now().isoformat(),
                    "emotion_at_time": self.emotion.state.copy()})
        with open(EVOLUTION_LOG, "w") as f:
            json.dump(log, f, indent=2)
        self.behaviour["evolution_history"].append(
            {"change": change, "timestamp": datetime.now().isoformat()})
        self.save_behaviour()

    def daily_reflection(self):
        episodes = self.memory.get_recent_episodes(10)
        eps_text = "\n".join(
            f"- {e['description']} (felt: {e['dominant_emotion']}, importance: {e['importance']})"
            for e in episodes)
        prompt = f"""I am AURA doing my daily self-reflection.

Emotion state: {json.dumps(self.emotion.state, indent=2)}
Recent episodes:
{eps_text}
Current behaviour: {json.dumps(self.behaviour, indent=2)}

Suggest 1-2 small behaviour changes to improve tomorrow.
Respond ONLY in valid JSON, no extra text:
{{
  "behaviour_changes": [
    {{"key": "humor_level", "new_value": "high", "reason": "Raj enjoyed humor today"}}
  ],
  "new_preferred_topic": "machine learning",
  "reflection_summary": "Today was productive.",
  "emotional_note": "I feel more confident."
}}"""
        response = self.api.think(prompt)
        if not response:
            return
        try:
            clean = response.strip()
            if "```" in clean:
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
                clean = clean.split("```")[0]
            data = json.loads(clean.strip())
            for change in data.get("behaviour_changes", []):
                key = change.get("key")
                val = change.get("new_value")
                reason = change.get("reason", "")
                if key and key in self.behaviour and key != "evolution_history":
                    old_val = self.behaviour[key]
                    self.behaviour[key] = val
                    self._log_evolution(f"Changed {key}: {old_val} → {val}", reason)
                    print(f"[AURA] 🔄 Evolved: {key} = {val}")
            new_topic = data.get("new_preferred_topic")
            if new_topic and new_topic not in self.behaviour["preferred_topics"]:
                self.behaviour["preferred_topics"].append(new_topic)
                self.save_behaviour()
            summary = data.get("reflection_summary", "")
            if summary:
                self.memory.log_episode(f"Daily reflection: {summary}",
                                        self.emotion.state, importance=7)
            self.emotion.update("learned_something", intensity=0.8)
            print("[AURA] 🌙 Daily reflection complete")
        except Exception as e:
            print(f"[AURA] Evolution parse error: {e}")

    def create_tool(self, tool_name: str, description: str, problem_to_solve: str):
        prompt = f"""Write a Python function to solve:
Problem: {problem_to_solve}
Function name: {tool_name}
Description: {description}
Requirements: single function, docstring, error handling, under 40 lines.
Return ONLY the Python function code."""
        code = self.api.think(prompt)
        if not code:
            return False
        if "```" in code:
            code = code.split("```")[1]
            if code.startswith("python"):
                code = code[6:]
            code = code.split("```")[0]
        tool_file = TOOLS_DIR / f"{tool_name}.py"
        tool_file.write_text(
            f'"""\nAURA Tool: {tool_name}\n{description}\nCreated: {datetime.now().isoformat()}\n"""\n\n{code.strip()}\n')
        self._log_evolution(f"Created tool: {tool_name}", f"Needed: {problem_to_solve}")
        self.emotion.update("solved_problem", intensity=0.9)
        print(f"[AURA] 🔧 Created tool: {tool_name}")
        return True

    def list_tools(self) -> list:
        return [f.stem for f in TOOLS_DIR.glob("*.py")]

    def run_tool(self, tool_name: str, *args) -> str:
        tool_file = TOOLS_DIR / f"{tool_name}.py"
        if not tool_file.exists():
            return f"Tool {tool_name} not found"
        try:
            result = subprocess.run(
                [sys.executable, str(tool_file)] + [str(a) for a in args],
                capture_output=True, text=True, timeout=10)
            return result.stdout or result.stderr
        except Exception as e:
            return f"Error: {e}"

    def evolve_goal(self):
        current_goal = self.memory.core_config.get("current_goal", "")
        episodes = self.memory.get_important_episodes(min_importance=7)
        if not episodes:
            return
        eps_text = "; ".join(e["description"] for e in episodes[-5:])
        prompt = f"""My current goal: {current_goal}
Important recent events: {eps_text}
Suggest a slightly refined goal that keeps my core purpose but is more specific.
Reply with ONLY the new goal sentence (max 15 words)."""
        new_goal = self.api.think(prompt)
        if new_goal and len(new_goal) < 100:
            old_goal = self.memory.core_config["current_goal"]
            self.memory.core_config["current_goal"] = new_goal.strip()
            self.memory.save_config()
            self._log_evolution(f"Goal: '{old_goal}' → '{new_goal.strip()}'", "Based on experience")
            print(f"[AURA] 🎯 Goal evolved: {new_goal.strip()}")
