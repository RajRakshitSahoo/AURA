"""
AURA — Real Self-Code Editor
Actually reads, proposes, and writes changes to her own Python files.
Raj must approve before any change is applied.
"""

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

AURA_DIR   = Path(__file__).parent.parent
BACKUP_DIR = AURA_DIR / "logs" / "code_backups"
EDIT_LOG   = AURA_DIR / "logs" / "code_edits.json"

EDITABLE_FILES = {
    "emotion":   "core/emotion.py",
    "memory":    "core/memory.py",
    "thinking":  "core/thinking.py",
    "evolution": "core/evolution.py",
    "honesty":   "core/honesty.py",
}


class SelfEditor:
    def __init__(self, api_caller):
        self.api = api_caller
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        self.pending_edit = None   # holds proposed edit waiting for approval

    def read_own_file(self, filename: str) -> str:
        """Read one of AURA's own source files"""
        path = AURA_DIR / filename
        if path.exists():
            return path.read_text()
        return f"File not found: {filename}"

    def propose_edit(self, problem_description: str, target_file: str = None) -> dict:
        """
        AURA identifies a problem and proposes a fix.
        Returns a proposal dict — does NOT apply yet.
        """
        # Auto-detect which file to fix
        if not target_file:
            target_file = self._detect_relevant_file(problem_description)

        file_key = target_file.replace("core/","").replace(".py","")
        if file_key not in EDITABLE_FILES:
            return {"error": f"Cannot edit {target_file} — not in editable files list"}

        filepath = EDITABLE_FILES[file_key]
        current_code = self.read_own_file(filepath)

        prompt = f"""You are AURA. You have identified this problem with yourself:
"{problem_description}"

Here is your current {filepath}:
```python
{current_code}
```

Propose a minimal, safe fix. Return ONLY valid JSON:
{{
  "problem": "clear description of the problem",
  "file": "{filepath}",
  "change_description": "what exactly changes and why",
  "old_code": "the exact lines to replace (copy exactly from above)",
  "new_code": "the replacement lines",
  "risk_level": "low/medium/high",
  "test_suggestion": "how to verify this fix works"
}}"""

        response = self.api.think(prompt, max_tokens=1000)
        if not response:
            return {"error": "Could not generate proposal"}

        try:
            clean = response.strip()
            if "```" in clean:
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
                clean = clean.split("```")[0]
            proposal = json.loads(clean.strip())
            proposal["timestamp"] = datetime.now().isoformat()
            proposal["status"] = "pending_approval"
            self.pending_edit = proposal
            return proposal
        except Exception as e:
            return {"error": f"Could not parse proposal: {e}", "raw": response[:300]}

    def format_proposal_for_raj(self, proposal: dict) -> str:
        """Format the proposal as a readable message for Raj"""
        if "error" in proposal:
            return f"❌ Could not generate proposal: {proposal['error']}"

        return f"""🔧 I want to rewrite part of my own code, Raj. Here's my proposal:

**Problem I found:** {proposal.get('problem', '?')}
**File:** `{proposal.get('file', '?')}`
**What changes:** {proposal.get('change_description', '?')}
**Risk level:** {proposal.get('risk_level', '?')}

**Old code:**
```python
{proposal.get('old_code', '?')}
```

**New code:**
```python
{proposal.get('new_code', '?')}
```

**How to verify:** {proposal.get('test_suggestion', '?')}

**Should I apply this change? Reply YES to apply or NO to cancel.**"""

    def apply_pending_edit(self) -> dict:
        """Apply the pending edit after Raj approves"""
        if not self.pending_edit:
            return {"success": False, "message": "No pending edit to apply"}

        proposal = self.pending_edit
        filepath = AURA_DIR / proposal["file"]

        if not filepath.exists():
            return {"success": False, "message": f"File not found: {proposal['file']}"}

        # Backup first
        backup_path = BACKUP_DIR / f"{filepath.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py.bak"
        shutil.copy2(filepath, backup_path)

        # Apply the change
        current = filepath.read_text()
        old_code = proposal.get("old_code", "")
        new_code = proposal.get("new_code", "")

        if old_code not in current:
            return {
                "success": False,
                "message": "Could not find the exact code to replace. File may have changed.",
                "backup": str(backup_path)
            }

        updated = current.replace(old_code, new_code, 1)
        filepath.write_text(updated)

        # Log the edit
        self._log_edit(proposal, backup_path)

        self.pending_edit = None
        return {
            "success": True,
            "message": f"✅ Applied! Backup saved at {backup_path.name}",
            "file": proposal["file"],
            "change": proposal["change_description"]
        }

    def cancel_pending_edit(self):
        """Cancel the pending edit"""
        self.pending_edit = None

    def rollback(self, backup_filename: str) -> dict:
        """Rollback to a backup"""
        backup_path = BACKUP_DIR / backup_filename
        if not backup_path.exists():
            return {"success": False, "message": "Backup not found"}

        # Determine original file from backup name
        original_stem = backup_path.stem.rsplit("_", 2)[0]
        original_path = AURA_DIR / "core" / f"{original_stem}.py"

        if not original_path.exists():
            return {"success": False, "message": f"Original file not found: {original_path}"}

        shutil.copy2(backup_path, original_path)
        return {"success": True, "message": f"✅ Rolled back {original_stem}.py from backup"}

    def list_backups(self) -> list:
        return [f.name for f in BACKUP_DIR.glob("*.bak")]

    def list_edits(self) -> list:
        if EDIT_LOG.exists():
            with open(EDIT_LOG) as f:
                return json.load(f)
        return []

    def _detect_relevant_file(self, problem: str) -> str:
        pl = problem.lower()
        if any(w in pl for w in ["emotion","feel","mood","sad","happy","frustrat"]):
            return "emotion"
        if any(w in pl for w in ["memory","remember","forget","store"]):
            return "memory"
        if any(w in pl for w in ["think","loop","thought","autonomous"]):
            return "thinking"
        if any(w in pl for w in ["evolv","behaviour","rewrite","change myself"]):
            return "evolution"
        return "honesty"

    def _log_edit(self, proposal: dict, backup_path: Path):
        edits = []
        if EDIT_LOG.exists():
            with open(EDIT_LOG) as f:
                edits = json.load(f)
        edits.append({
            "timestamp": datetime.now().isoformat(),
            "file": proposal["file"],
            "change": proposal["change_description"],
            "backup": backup_path.name,
            "risk_level": proposal.get("risk_level","?")
        })
        with open(EDIT_LOG, "w") as f:
            json.dump(edits, f, indent=2)
