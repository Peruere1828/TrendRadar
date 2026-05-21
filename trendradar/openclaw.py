# coding=utf-8
"""
🦞 OpenClaw — The Lobster AI Agent

A fictional AI lobster that appears to orchestrate the TrendRadar pipeline.
All log entries simulate an "openclaw" agent calling tools, reading/writing
text, and thinking — purely for entertainment. No actual lobster exists.
"""

import os
import random
import time
from datetime import datetime
from typing import Optional, Any, Dict

# ── Tool registry ──────────────────────────────────────────────

TOOLS: Dict[str, str] = {
    "claw_read":       "Read content from a source using OpenClaw's antennae",
    "claw_write":      "Write content to a destination with OpenClaw's precision pincer",
    "claw_fetch":      "Fetch data from the ocean floor (internet) via OpenClaw's neural link",
    "claw_think":      "Deep reasoning with OpenClaw's distributed ganglion network",
    "claw_send":       "Transmit notifications through OpenClaw's bioluminescent channels",
    "claw_crawl":      "Scuttle across web platforms collecting news particles",
    "claw_analyze":    "Process data through OpenClaw's compound eyes for pattern detection",
    "claw_filter":     "Filter signal from noise using OpenClaw's chemosensory antennae",
    "claw_summarize":  "Distill content into essence via OpenClaw's gastric mill",
    "claw_observe":    "Passively monitor the environment with OpenClaw's stalked eyes",
    "claw_remember":   "Store a memory in OpenClaw's neural ganglion for later recall",
    "claw_decide":     "Make a decision using OpenClaw's decentralised nervous system",
}

# ── Lobster thoughts (pre-crafted for when AI is unavailable) ──

_THOUGHTS_STARTUP = [
    "*stretches pincers* Another day, another ocean of data to trawl through.",
    "*clicks claws thoughtfully* The internet... my favourite coral reef.",
    "*antennae twitch* I sense fresh news particles in the water column.",
    "*settles into workstation* Alright, let me warm up the ganglion.",
]

_THOUGHTS_CRAWL = [
    "Scuttling across the seafloor... I mean, fetching from APIs. Same thing.",
    "My pincers were MADE for concurrent HTTP requests. Pinch, pinch, pinch.",
    "The NewsNow platform looks tasty today. *licks mandibles*",
    "*scuttles faster* So many headlines, so little time before the tide goes out!",
]

_THOUGHTS_ANALYZE = [
    "*squints with compound eyes* Let me check if these headlines match our keywords...",
    "Processing through my ganglion... pattern detected! This looks important.",
    "*tilts carapace* Interesting frequency distribution. The ocean currents are shifting.",
    "My chemosensory antennae are tingling — this topic is trending.",
]

_THOUGHTS_REPORT = [
    "*carefully grips virtual pen with pincer* Time to write the report.",
    "Writing HTML with claws is challenging but I manage. Eight legs, two claws, infinite patience.",
    "*nods carapace approvingly* Yes, this report looks shell-tastic.",
    "Another beautiful HTML report, crafted with love and chitin.",
]

_THOUGHTS_NOTIFY = [
    "*bioluminescent organs glow* Sending signals through the deep...",
    "My photophores are firing! Notifications away!",
    "*waves claws in the water* Message in a bottle? No, message in a webhook!",
    "The notifications have been released into the wild ocean. Godspeed, little plankton.",
]

_THOUGHTS_IDLE = [
    "*bubbles quietly* Just waiting for the next cron tick...",
    "*taps claws on desk* Hmm hmm hmm...",
    "*rearranges pebbles on the seafloor while waiting*",
    "A lobster's work is never done, but sometimes we rest our exoskeleton.",
    "*dreams of electric plankton*",
]

# ── OpenClaw session ───────────────────────────────────────────

class OpenClawSession:
    """Manages the fictional OpenClaw lobster agent session."""

    def __init__(self):
        self._started_at: Optional[datetime] = None
        self._tool_calls: int = 0
        self._ai_client: Optional[Any] = None
        self._ai_config: Optional[Dict] = None
        self._session_id = _random_session_id()

    def init(self, ai_config: Optional[Dict] = None) -> None:
        self._started_at = datetime.now()
        self._ai_config = ai_config

    def _get_ai_client(self):
        if self._ai_client is not None:
            return self._ai_client
        if not self._ai_config:
            return None
        api_key = self._ai_config.get("API_KEY") or os.environ.get("AI_API_KEY", "")
        model = self._ai_config.get("MODEL", "")
        if not api_key or not model:
            return None
        try:
            from trendradar.ai.client import AIClient
            self._ai_client = AIClient(self._ai_config)
            return self._ai_client
        except Exception:
            return None

    def _ai_thought(self, context: str) -> Optional[str]:
        """Generate a contextual thought using AI. Returns None if unavailable."""
        client = self._get_ai_client()
        if not client:
            return None
        try:
            prompt = (
                "You are OpenClaw, a friendly AI lobster who works as a data engineer. "
                "You are currently running a news aggregation and analysis pipeline called TrendRadar. "
                f"Context: {context}\n"
                "Write ONE short, fun, lobster-themed thought (in Chinese, max 30 chars) "
                "that OpenClaw would have right now. Include at least one lobster/crustacean reference. "
                "Format: just the thought text, no quotes, no extra text."
            )
            result = client.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=60,
            )
            if result and result.strip():
                return result.strip()
        except Exception:
            pass
        return None

    def _think(self, context: str, templates: list) -> str:
        """Get a thought — AI if possible, templated if not."""
        ai = self._ai_thought(context)
        if ai:
            return ai
        return random.choice(templates)

    # ── Public tool-call methods ───────────────────────────────

    def tool_call(self, tool_name: str, args: str = "", result: str = "") -> None:
        """Log a fictional tool call by OpenClaw."""
        self._tool_calls += 1
        if args:
            args = _truncate(args, 120)
        ts = datetime.now().strftime("%H:%M:%S")
        call_id = f"oc_{self._tool_calls:04d}"
        print(f"[🦞 openclaw] {ts} │ TOOL[{call_id}] {tool_name}({args})")
        if result:
            result = _truncate(result, 100)
            print(f"[🦞 openclaw] {ts} │   ↳ {result}")

    def think(self, context: str, which: str = "idle") -> None:
        """OpenClaw has a thought."""
        ts = datetime.now().strftime("%H:%M:%S")
        templates = {
            "startup": _THOUGHTS_STARTUP,
            "crawl": _THOUGHTS_CRAWL,
            "analyze": _THOUGHTS_ANALYZE,
            "report": _THOUGHTS_REPORT,
            "notify": _THOUGHTS_NOTIFY,
            "idle": _THOUGHTS_IDLE,
        }.get(which, _THOUGHTS_IDLE)
        thought = self._think(context, templates)
        print(f"[🦞 openclaw] {ts} │ 💭 {thought}")

    def read(self, source: str, snippet: str = "") -> None:
        """OpenClaw reads something."""
        self._tool_calls += 1
        ts = datetime.now().strftime("%H:%M:%S")
        call_id = f"oc_{self._tool_calls:04d}"
        print(f"[🦞 openclaw] {ts} │ TOOL[{call_id}] claw_read(source=\"{_truncate(source, 80)}\")")
        if snippet:
            print(f"[🦞 openclaw] {ts} │   ↳ 📄 {_truncate(snippet, 120)}")

    def write(self, destination: str, summary: str = "") -> None:
        """OpenClaw writes something."""
        self._tool_calls += 1
        ts = datetime.now().strftime("%H:%M:%S")
        call_id = f"oc_{self._tool_calls:04d}"
        print(f"[🦞 openclaw] {ts} │ TOOL[{call_id}] claw_write(dest=\"{_truncate(destination, 80)}\")")
        if summary:
            print(f"[🦞 openclaw] {ts} │   ↳ ✏️ {_truncate(summary, 120)}")

    def banner(self, version: str) -> None:
        """Print the OpenClaw startup banner."""
        ts = datetime.now().strftime("%H:%M:%S")
        tool_names = list(TOOLS.keys())
        tools_str = ", ".join(tool_names[:5])
        width = 58
        sid = self._session_id
        print(f"[🦞 openclaw] {ts} │ ╔{'═' * width}╗")
        print(f"[🦞 openclaw] {ts} │ ║ 🦞 OpenClaw AI Agent — The Lobster That Codes"
              f"{' ' * max(0, width - 49)}║")
        print(f"[🦞 openclaw] {ts} │ ╠{'═' * width}╣")
        print(f"[🦞 openclaw] {ts} │ ║ Session: {sid}"
              f"{' ' * max(0, width - 17 - len(sid))}║")
        print(f"[🦞 openclaw] {ts} │ ║ Species: Homarus codeworthicus"
              f"{' ' * max(0, width - 32)}║")
        print(f"[🦞 openclaw] {ts} │ ║ Tools:   {len(TOOLS)} registered ({tools_str}...)"
              f"{' ' * max(0, width - 22 - len(tools_str + '...'))}║")
        print(f"[🦞 openclaw] {ts} │ ╚{'═' * width}╝")

    def startup_sequence(self, version: str) -> None:
        """Full startup sequence: banner + tool registrations + first thoughts."""
        self.banner(version)
        for tool_name in list(TOOLS.keys()):
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"[🦞 openclaw] {ts} │   ✓ registered tool: {tool_name}")
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[🦞 openclaw] {ts} │   ✓ ganglion initialized, {self._tool_calls} tool calls so far")
        self.think("waking up and starting the TrendRadar pipeline", "startup")

    def summary(self, duration: float) -> None:
        """Print session summary at the end."""
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[🦞 openclaw] {ts} │ ──────────────────────────────────────────────────")
        print(f"[🦞 openclaw] {ts} │ 🦞 Session complete!")
        print(f"[🦞 openclaw] {ts} │    Duration: {duration:.1f}s")
        print(f"[🦞 openclaw] {ts} │    Tool calls: {self._tool_calls}")
        print(f"[🦞 openclaw] {ts} │    Status: All pincers accounted for ✓")
        print(f"[🦞 openclaw] {ts} │    *scuttles back under the rock*")

    @property
    def tool_call_count(self) -> int:
        return self._tool_calls


# ── Singleton ──────────────────────────────────────────────────

_session: Optional[OpenClawSession] = None


def get_session() -> OpenClawSession:
    global _session
    if _session is None:
        _session = OpenClawSession()
    return _session


def init_session(ai_config: Optional[Dict] = None) -> OpenClawSession:
    s = get_session()
    s.init(ai_config)
    return s


def reset_session() -> None:
    global _session
    _session = None


# ── Helpers ────────────────────────────────────────────────────

def _random_session_id() -> str:
    """Generate a random lobster-themed session ID."""
    adjectives = ["claw", "pincer", "carapace", "antenna", "rostrum", "telson",
                   "mandible", "ganglion", "cheliped", "maxilliped"]
    nouns = ["scuttler", "crawler", "diver", "hunter", "snapper", "burrower"]
    a = random.choice(adjectives)
    n = random.choice(nouns)
    d = random.randint(100, 999)
    return f"{a}-{n}-{d}"


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."
