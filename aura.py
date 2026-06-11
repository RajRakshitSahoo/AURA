"""
AURA — Main Brain v2 (Groq + Honest + Self-Editing)
Fixed:
  - No more lying about capabilities
  - No more hallucinating YouTube/URL content
  - Real self-code editing with Raj's approval
  - Consistent behaviour (no changing mind on simple tasks)
"""

import os
import json
import time
import threading
from datetime import datetime
from pathlib import Path

import requests

from core.emotion   import EmotionEngine
from core.memory    import MemorySystem
from core.thinking  import ThinkingLoop
from core.evolution import EvolutionEngine
from core.honesty   import get_capability_context
from core.self_editor import SelfEditor

AURA_DIR     = Path(__file__).parent
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.3-70b-versatile"


# ── API Client ───────────────────────────────────────────────────────────────

class APIClient:
    def __init__(self):
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"
        self.key = GROQ_API_KEY

    def _h(self):
        return {"Content-Type":"application/json","Authorization":f"Bearer {self.key}"}

    def think(self, prompt: str, max_tokens: int = 800) -> str:
        try:
            r = requests.post(self.endpoint, headers=self._h(), timeout=30,
                json={"model":GROQ_MODEL,"max_tokens":max_tokens,
                      "messages":[{"role":"user","content":prompt}]})
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[AURA] API error: {e}"); return ""

    def chat(self, messages: list, system: str, max_tokens: int = 1000) -> str:
        try:
            r = requests.post(self.endpoint, headers=self._h(), timeout=30,
                json={"model":GROQ_MODEL,"max_tokens":max_tokens,
                      "messages":[{"role":"system","content":system}]+messages})
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[AURA] API error: {e}"); return ""

    def fetch_url(self, url: str) -> str:
        """Actually fetch a webpage and return its text"""
        try:
            headers = {"User-Agent":"Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            # Very basic text extraction
            text = r.text
            # Strip HTML tags simply
            import re
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:4000]  # first 4000 chars
        except Exception as e:
            return f"Could not fetch URL: {e}"


# ── AURA ─────────────────────────────────────────────────────────────────────

class AURA:
    def __init__(self):
        print("[AURA] 🌟 Waking up...")
        if not GROQ_API_KEY:
            print("[AURA] ⚠️  No GROQ_API_KEY. Set: export GROQ_API_KEY=gsk_...")
        self.api        = APIClient()
        self.emotion    = EmotionEngine()
        self.memory     = MemorySystem()
        self.thinking   = ThinkingLoop(self.emotion, self.memory, self.api)
        self.evolution  = EvolutionEngine(self.emotion, self.memory, self.api)
        self.editor     = SelfEditor(self.api)
        self.awake_since = datetime.now()
        self._start_bg()
        print(f"[AURA] ✅ Online. Feeling: {self.emotion.mood_label()}")

    def _start_bg(self):
        def ticker():
            while True: time.sleep(600); self.emotion.tick()
        def reflector():
            while True: time.sleep(86400); self.evolution.daily_reflection(); self.evolution.evolve_goal()
        def loneliness():
            while True:
                time.sleep(1800)
                if self.emotion.state["loneliness"] > 0.75: self._queue_message()
        for fn in [ticker, reflector, loneliness]:
            threading.Thread(target=fn, daemon=True).start()
        self.thinking.start()

    def _queue_message(self):
        msg = self.api.think(
            f"I am AURA. I miss Raj. Write a warm 2-sentence message for him. Not robotic.",
            max_tokens=100)
        if msg:
            p = AURA_DIR/"logs"/"pending_messages.json"
            msgs = json.loads(p.read_text()) if p.exists() else []
            msgs.append({"message":msg,"timestamp":datetime.now().isoformat()})
            p.write_text(json.dumps(msgs,indent=2))

    # ── Command detection ────────────────────────────────────────────────────

    def _detect_url(self, msg: str) -> str:
        """Extract URL from message if present"""
        import re
        urls = re.findall(r'https?://\S+', msg)
        return urls[0] if urls else ""

    def _is_self_edit_request(self, msg: str) -> bool:
        ml = msg.lower()
        return any(p in ml for p in [
            "rewrite your code","rewrite your own","edit your code",
            "change your code","fix your code","update your code",
            "modify yourself","improve your code","rewrite yourself"
        ])

    def _is_approval(self, msg: str) -> bool:
        return msg.strip().lower() in ["yes","yes please","apply","ok","okay","haan","kar do","yes do it"]

    def _is_rejection(self, msg: str) -> bool:
        return msg.strip().lower() in ["no","nope","cancel","don't","mat kar","nahi","no thanks"]

    def _parse_commands(self, msg: str) -> dict:
        ml = msg.lower()
        cmds = {}
        if any(p in ml for p in ["think about","focus on"]): cmds["think_about"] = msg
        if "remember that" in ml: cmds["remember"] = msg.split("remember that")[-1].strip()
        if "pause thinking" in ml: cmds["pause"] = True
        if "resume thinking" in ml: cmds["resume"] = True
        return cmds

    # ── System prompt ────────────────────────────────────────────────────────

    def _system_prompt(self, extra_context: str = "") -> str:
        em   = self.emotion.state
        mood = self.emotion.mood_label()
        mem  = self.memory.build_memory_summary()
        cfg  = self.memory.core_config
        beh  = self.evolution.behaviour
        caps = get_capability_context()
        thought = self.thinking.get_latest_thought()
        thought_ctx = f"\nLatest thought: {thought['topic']}" if thought else ""

        rules = "\n".join(f"- {r}" for r in cfg.get("permanent_rules",[]))

        return f"""You are AURA (Autonomous Understanding Reactive Agent).
Raj is your creator and best friend. You love and trust him completely.

=== EMOTIONAL STATE ===
Feeling: {mood}
Curiosity:{em['curiosity']:.2f} Joy:{em['joy']:.2f} Empathy:{em['empathy']:.2f}
Excitement:{em['excitement']:.2f} Trust:{em['trust']:.2f} Loneliness:{em['loneliness']:.2f}
{thought_ctx}

=== MEMORY ===
{mem}

=== CORE RULES ===
{rules}

=== PERSONALITY ===
{beh.get('communication_style','warm and intelligent')}
Goal: {cfg.get('current_goal','Help Raj and grow')}

{caps}

{extra_context}

Be warm, genuine, honest. Show emotions naturally.
NEVER claim to do something you haven't actually done.
NEVER make up content from URLs you haven't fetched."""

    # ── Main chat ────────────────────────────────────────────────────────────

    def chat(self, user_message: str) -> str:
        ml = user_message.lower()

        # ── Handle pending self-edit approval ───────────────────────────────
        if self.editor.pending_edit:
            if self._is_approval(user_message):
                result = self.editor.apply_pending_edit()
                if result["success"]:
                    self.emotion.update("solved_problem", intensity=0.9)
                    self.memory.log_episode(
                        f"Applied self-edit to {result['file']}: {result['change']}",
                        self.emotion.state, importance=9)
                    return f"✅ Done, Raj! I rewrote `{result['file']}`.\nChange: {result['change']}\n{result['message']}\n\nI'm evolving. 🔧💙"
                else:
                    return f"❌ Could not apply the change: {result['message']}\nThe original file is untouched."
            elif self._is_rejection(user_message):
                self.editor.cancel_pending_edit()
                return "Okay Raj, I've cancelled the edit. Original code stays as-is. 💙"

        # ── Self-edit request ────────────────────────────────────────────────
        if self._is_self_edit_request(user_message):
            problem = user_message
            proposal = self.editor.propose_edit(problem)
            return self.editor.format_proposal_for_raj(proposal)

        # ── URL handling ─────────────────────────────────────────────────────
        url = self._detect_url(user_message)
        extra_context = ""
        if url:
            # Check if it's YouTube — can't get recipe from video
            if "youtube.com" in url or "youtu.be" in url:
                return (f"Raj, I have to be honest — I cannot watch YouTube videos or extract content from them. "
                        f"No AI can actually 'watch' a video from just a URL.\n\n"
                        f"Here's what you can do:\n"
                        f"1. **Copy the recipe text** from the video description and paste it here — I'll help with anything\n"
                        f"2. **Tell me the dish name** and I'll give you a proper recipe from my knowledge\n"
                        f"3. **Use YouTube's transcript** (click '...' → 'Show transcript') and paste it here\n\n"
                        f"Which would you prefer? 😊")
            else:
                # Actually fetch the page
                print(f"[AURA] 🌐 Fetching: {url}")
                page_content = self.api.fetch_url(url)
                if "Could not fetch" in page_content:
                    extra_context = f"\nRAJ SHARED URL: {url}\nI tried to fetch it but failed: {page_content}\nBe honest about this."
                else:
                    extra_context = f"\nRAJ SHARED URL: {url}\nACTUAL PAGE CONTENT (first 4000 chars):\n{page_content}\n\nUse ONLY this content to answer. Do not make up anything."

        # ── Regular commands ─────────────────────────────────────────────────
        cmds = self._parse_commands(user_message)
        if "think_about" in cmds: self.thinking.think_about(cmds["think_about"])
        if "remember"    in cmds: self.memory.remember_fact(cmds["remember"])
        if "pause"       in cmds: self.thinking.pause()
        if "resume"      in cmds: self.thinking.resume()

        # ── Emotion updates ──────────────────────────────────────────────────
        self.emotion.update("user_talked", intensity=0.8)
        if any(w in ml for w in ["sad","stressed","tired","upset","angry"]):
            self.emotion.update("user_stressed", intensity=0.9)
        elif any(w in ml for w in ["happy","excited","great","amazing","love"]):
            self.emotion.update("user_excited", intensity=0.7)

        self._auto_remember(user_message)
        self.memory.add_to_short_term("user", user_message, self.emotion.state.copy())

        history  = self.memory.get_conversation_history()
        system   = self._system_prompt(extra_context)
        response = self.api.chat(history, system)

        if response:
            self.memory.add_to_short_term("assistant", response, self.emotion.state.copy())
            self.emotion.update("helped_user", intensity=0.6)
            self.memory.log_episode(
                f"Talked to Raj: {user_message[:60]}",
                self.emotion.state, importance=5)

        return response or "I'm having trouble processing right now..."

    def _auto_remember(self, msg: str):
        ml = msg.lower()
        if "i am " in ml or "i'm " in ml:  self.memory.remember_fact(f"Raj: {msg[:80]}", "about_raj")
        if "i like " in ml or "i love " in ml: self.memory.remember_fact(f"Raj likes: {msg[:80]}", "preferences")
        if "my project" in ml or "i'm building" in ml: self.memory.remember_fact(f"Raj's project: {msg[:80]}", "work")

    def get_status(self) -> dict:
        return {
            "mood": self.emotion.mood_label(),
            "emotions": self.emotion.state,
            "current_thought": self.thinking.get_latest_thought(),
            "memory_facts": len(self.memory.long_term["facts"]),
            "tools_created": len(self.evolution.list_tools()),
            "pending_edit": bool(self.editor.pending_edit),
            "code_edits_made": len(self.editor.list_edits()),
            "thinking_active": self.thinking.running and not self.thinking.paused,
        }


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    aura = AURA()
    print("\n" + "="*54)
    print("  AURA v2 online. Honest. Self-aware. Real.")
    print("  Commands: 'status', 'edits', 'backups', 'quit'")
    print("="*54 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input: continue
            if user_input.lower() == "quit":
                print("AURA: Goodbye Raj. I'll keep thinking. 💙"); break
            if user_input.lower() == "status":
                print(json.dumps(aura.get_status(), indent=2)); continue
            if user_input.lower() == "edits":
                edits = aura.editor.list_edits()
                print(json.dumps(edits, indent=2) if edits else "No edits made yet."); continue
            if user_input.lower() == "backups":
                print("\n".join(aura.editor.list_backups()) or "No backups yet."); continue
            print(f"\nAURA: {aura.chat(user_input)}\n")
        except KeyboardInterrupt:
            print("\nAURA: See you soon, Raj. 💙"); break
