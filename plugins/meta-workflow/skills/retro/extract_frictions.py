#!/usr/bin/env python3
"""Extract "friction signals" from Claude Code session transcripts over a time window.

Emits a compact JSON (not the raw transcripts) for the retro skill's model to analyse.
Three signals:
  1. corrections  — messages where the user pushed back on / corrected Claude (the ore)
  2. tool_errors  — failed tool_results, aggregated by tool + signature
  3. rejections   — actions the user blocked, aggregated by tool

Stdlib only. Reads the main sessions (root/<project>/*.jsonl) and skips the agent
sub-transcripts (root/<project>/<session>/subagents/*), which carry no user friction.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from glob import glob

# --- Heuristique de détection des corrections ------------------------------
# Indices (lowercase, frontières de mots quand pertinent) qui trahissent une
# reprise / un désaccord / une frustration. Volontairement large : le modèle
# fait le tri ensuite. Mieux vaut un faux positif qu'un signal manqué.
CORRECTION_CUES = [
    r"\bnon\b", r"\bnon,", r"\bplut[oô]t\b", r"\bje t'?avais dit\b",
    r"\bje t'?ai dit\b", r"\bc'?est pas\b", r"\bce n'?est pas\b",
    r"\bne marche pas\b", r"\bmarche pas\b", r"\btoujours pas\b",
    r"\bpas comme [çc]a\b", r"\bpas ce que\b", r"\btu as oubli[ée]\b",
    r"\btu n'?as pas\b", r"\bil fallait\b", r"\bil faut\b", r"\bannule\b",
    r"\breviens\b", r"\bpourquoi (?:tu|ne|pas|avoir)\b", r"\bje voulais\b",
    r"\berreur\b", r"\bfaux\b", r"\bmauvais\b", r"\bencore une fois\b",
    r"\bnon pas\b", r"\barr[eê]te\b", r"\busine [aà] gaz\b",
    r"\btrop\b", r"\bredo\b", r"\bre-?fais\b", r"\bre-?refais\b",
    # English cues (the skill is advertised bilingual — keep recall up for EN-only users)
    r"\bno,? ", r"\bnope\b", r"\bnot what\b", r"\bnot quite\b", r"\binstead\b",
    r"\byou (?:forgot|didn'?t|missed|should|were supposed)\b", r"\bdon'?t\b",
    r"\bthat'?s (?:wrong|not)\b", r"\bnot right\b", r"\brevert\b", r"\bundo\b",
    r"\bwhy (?:did|are|not|would)\b", r"\bactually\b", r"\bstop\b", r"\bredo\b",
    r"\btoo (?:complex|complicated|much|many)\b", r"\bI (?:said|wanted|meant|asked)\b",
    r"\bmistake\b", r"\bwrong\b", r"\bagain\b",
]
CORRECTION_RE = re.compile("|".join(CORRECTION_CUES), re.IGNORECASE)

# Short approval/command messages to ignore (these are not friction). FR + EN.
APPROVALS = {
    "valide", "ok", "oui", "non", "go", "parfait", "merci", "yes", "y", "stop",
    "commit", "push", "merge", "continue", "continuer", "vas-y", "vasy", "ok merci",
    "thanks", "thx", "great", "perfect", "looks good", "lgtm", "do it", "sounds good",
    "sure", "yep", "yeah", "ok thanks", "nice", "good", "proceed", "ship it",
}

# Un tool_result en erreur qui matche ceci = Claude a tenté une action que
# l'utilisateur a refusée (signal de réglage : pré-autoriser, ou Claude a mal
# jugé). Le reste = vraie erreur technique. On sépare les deux.
REJECT_RE = re.compile(
    r"doesn'?t want to proceed|tool use was rejected|denied by your permission",
    re.IGNORECASE,
)

# Bruit à exclure des corrections : résumés de continuation de contexte et
# dumps de références de tâches/outils qui fuient dans le contenu user.
NOISE_PREFIXES = (
    "this session is being continued",
    "the summary below covers",
)
TASK_REF_RE = re.compile(r"\btoolu_[A-Za-z0-9]{6,}|/tasks/.*\.output", re.IGNORECASE)
HEX_ID_HEAD_RE = re.compile(r"^[0-9a-f]{12,}\s")
CODE_HEAD_RE = re.compile(r"^\s*(def |class |import |from |const |function |@\w+|\w+\s*=\s*\{|\w+\s*=\s*\[|<\?php|#include)")


def looks_like_code(text: str) -> bool:
    """A code block pasted by the user (not a natural-language correction)."""
    if CODE_HEAD_RE.match(text):
        return True
    # High code-punctuation density over the first lines. Threshold kept high on
    # purpose: this tool favours recall, so dropping a real correction is the
    # wrong-direction error — a genuine sentence quoting a path stays well under 18.
    head = text[:200]
    punct = sum(head.count(c) for c in "{};=()[]")
    return punct >= 18

# Nettoyage des wrappers harness injectés dans le contenu user.
TAG_RE = re.compile(r"<[^>]+>")
SYSTEM_REMINDER_RE = re.compile(r"<system-reminder>.*?</system-reminder>", re.DOTALL)
COMMAND_BLOCK_RE = re.compile(r"<command-[^>]+>.*?</command-[^>]+>", re.DOTALL)


def clean_user_text(text: str) -> str:
    """Retire les wrappers harness (system-reminder, command-name, caveats)."""
    text = SYSTEM_REMINDER_RE.sub("", text)
    text = COMMAND_BLOCK_RE.sub("", text)
    text = re.sub(r"<local-command-[^>]*>.*?</local-command-[^>]*>", "", text, flags=re.DOTALL)
    text = re.sub(r"Caveat:.*?explicitly asks you to\.", "", text, flags=re.DOTALL)
    text = TAG_RE.sub("", text)
    return text.strip()


def parse_ts(raw: str) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def first_line(s: str, n: int = 140) -> str:
    s = (s or "").strip().splitlines()
    line = s[0] if s else ""
    return line[:n]


def normalize_error(snippet: str) -> str:
    """Réduit un message d'erreur à une signature groupable."""
    snip = first_line(snippet, 200)
    snip = re.sub(r"\d+", "N", snip)            # numéros de ligne, codes
    snip = re.sub(r"/[^\s'\"]+", "/PATH", snip)  # chemins
    return snip[:120]


def iter_session_files(root: str):
    """Sessions principales uniquement : root/<projet>/<uuid>.jsonl."""
    for path in glob(os.path.join(root, "*", "*.jsonl")):
        # ignore les sous-transcripts d'agents (.../<session>/subagents/*.jsonl)
        if os.sep + "subagents" + os.sep in path:
            continue
        yield path


def process_file(path: str, since: datetime, out: dict) -> None:
    project = os.path.basename(os.path.dirname(path))
    session = os.path.splitext(os.path.basename(path))[0][:8]
    tool_names: dict[str, str] = {}      # tool_use_id -> nom outil
    last_assistant_text = ""
    file_touched = False

    try:
        fh = open(path, encoding="utf-8")
    except OSError:
        return

    with fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                o = json.loads(raw)
            except json.JSONDecodeError:
                continue

            ts = parse_ts(o.get("timestamp", ""))
            if ts and ts < since:
                continue

            typ = o.get("type")
            msg = o.get("message", {})
            if not isinstance(msg, dict):
                continue
            content = msg.get("content")

            if typ == "assistant":
                # mémorise le mapping tool_use_id -> nom + le dernier texte assistant
                texts = []
                if isinstance(content, list):
                    for it in content:
                        if not isinstance(it, dict):
                            continue
                        if it.get("type") == "tool_use":
                            tool_names[it.get("id", "")] = it.get("name", "?")
                        elif it.get("type") == "text":
                            texts.append(it.get("text", ""))
                elif isinstance(content, str):
                    texts.append(content)
                if texts:
                    last_assistant_text = " ".join(texts)
                continue

            if typ != "user" or o.get("isMeta") or o.get("isSidechain"):
                continue

            # --- contenu user : texte + tool_results ---
            user_texts = []
            if isinstance(content, str):
                user_texts.append(content)
            elif isinstance(content, list):
                for it in content:
                    if not isinstance(it, dict):
                        continue
                    if it.get("type") == "text":
                        user_texts.append(it.get("text", ""))
                    elif it.get("type") == "tool_result":
                        body = it.get("content", "")
                        if isinstance(body, list):
                            body = " ".join(
                                b.get("text", "") for b in body if isinstance(b, dict)
                            )
                        body = str(body)
                        tool = tool_names.get(it.get("tool_use_id", ""), "?")
                        if it.get("is_error"):
                            bucket = "_rejections" if REJECT_RE.search(body) else "_tool_errors"
                            sig = "rejet utilisateur" if bucket == "_rejections" else normalize_error(body)
                            rec = out[bucket][(tool, sig)]
                            rec["count"] += 1
                            rec["tool"] = tool
                            rec["sig"] = sig
                            if not rec["example"]:
                                rec["example"] = first_line(body, 180)
                            rec["projects"].add(project)
                            file_touched = True

            text = clean_user_text(" ".join(user_texts))
            if not text:
                continue
            low = text.lower().strip()
            if low in APPROVALS or text.startswith("/") or len(low) < 4:
                continue
            # anti-bruit : résumés de continuation et dumps de références
            if low.startswith(NOISE_PREFIXES) or TASK_REF_RE.search(text) or HEX_ID_HEAD_RE.match(low):
                continue
            if looks_like_code(text):
                continue

            out["_user_msg_count"] += 1
            m = CORRECTION_RE.findall(text)
            if m:
                cues = sorted({c.lower() for c in (m if isinstance(m[0], str) else [x for t in m for x in t]) if c})
                out["corrections"].append({
                    "project": project,
                    "session": session,
                    "ts": ts.isoformat() if ts else None,
                    "cues": cues[:6],
                    "user_text": text[:450],
                    "prev_assistant": last_assistant_text[:320],
                })
                file_touched = True

    if file_touched:
        out["_sessions_touched"].add(f"{project}/{session}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7, help="window in days (default 7)")
    ap.add_argument("--root", default=os.path.expanduser("~/.claude/projects"),
                    help="transcripts root (default ~/.claude/projects)")
    ap.add_argument("--out", default="", help="output file (default stdout)")
    ap.add_argument("--max-corrections", type=int, default=80)
    args = ap.parse_args()

    since = datetime.now(timezone.utc) - timedelta(days=args.days)

    def err_rec():
        return {"count": 0, "tool": "", "sig": "", "example": "", "projects": set()}

    out = {
        "corrections": [],
        "_tool_errors": defaultdict(err_rec),
        "_rejections": defaultdict(err_rec),
        "_user_msg_count": 0,
        "_sessions_touched": set(),
    }

    files = list(iter_session_files(args.root))
    for path in files:
        process_file(path, since, out)

    # corrections: sort by cue-richness, then recency (the shown subset is the
    # richest, not chronological — surfaced via corrections_truncated in meta)
    out["corrections"].sort(key=lambda c: (len(c["cues"]), c["ts"] or ""), reverse=True)
    truncated = len(out["corrections"]) > args.max_corrections
    corrections = out["corrections"][:args.max_corrections]

    def flatten(bucket):
        return sorted(
            ({**v, "projects": sorted(v["projects"])} for v in bucket.values()),
            key=lambda r: r["count"], reverse=True,
        )

    tool_errors = flatten(out["_tool_errors"])
    rejections = flatten(out["_rejections"])

    report = {
        "meta": {
            "window_days": args.days,
            "since": since.isoformat(),
            "session_files_scanned": len(files),
            "sessions_with_signal": len(out["_sessions_touched"]),
            "user_msgs_considered": out["_user_msg_count"],
            "corrections_found": len(out["corrections"]),
            "corrections_shown": len(corrections),
            "corrections_truncated": truncated,
            "tool_error_groups": len(tool_errors),
            "rejection_groups": len(rejections),
        },
        "corrections": corrections,
        "tool_errors": tool_errors,
        "rejections": rejections,
    }

    blob = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(blob)
        print(f"Report written to {args.out}", file=sys.stderr)
        print(json.dumps(report["meta"], ensure_ascii=False, indent=2))
    else:
        print(blob)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
