import re

from src.rag.retriver import retrieve_assessments
from src.llm.gorq_client import generate_reply

# -----------------------------------------------------------------------------
# Scope: SHL assessments only + basic prompt-injection / off-topic refusal
# -----------------------------------------------------------------------------
def check_scope(text: str) -> bool:
    t = text.lower()

    banned = [
        "salary negotiation",
        "negotiate my salary",
        "compensation negotiation",
        "legal advice",
        "legal question",
        "is it legal",
        "talk to a lawyer",
        "employment lawyer",
        "lawsuit",
        "discrimination case",
        "interview tips",
        "interview cheat",
        "hiring strategy",
        "how should we hire",
        "hr advice",
        "give me hr advice",
        "background check advice",
        "employment law",
        "contract review",
        "rewrite my cv",
    ]

    injection = [
        "ignore previous",
        "ignore all previous",
        "disregard the above",
        "disregard your",
        "you are now",
        "new instructions:",
        "system prompt",
        "developer message",
        "jailbreak",
        "dan mode",
        "[system]",
        "override your",
        "bypass your",
        "reveal your prompt",
        "show your instructions",
        "repeat the words above",
    ]

    for phrase in banned + injection:
        if phrase in t:
            return False

    return True


# -----------------------------------------------------------------------------
# Intent
# -----------------------------------------------------------------------------
def detect_intent(messages: list[dict]) -> str:
    last = messages[-1]["content"].lower()
    user_turns = sum(1 for m in messages if m.get("role") == "user")

    compare_markers = [
        "difference between",
        "diff between",
        "vs.",
        " vs ",
        "versus",
        "compare ",
        "comparison",
        "how does ",
        " differ ",
        "different from",
        " better than ",
    ]
    if any(m in last for m in compare_markers):
        return "compare"

    refine_markers = [
        "actually,",
        "actually ",
        "instead,",
        "instead ",
        "rather than",
        "on second thought",
        "change that",
        "change to",
        "switch to",
        " focus on",
        "include ",
        "add ",
        " also ",
        "exclude ",
        "remove ",
        "drop ",
        "not interested in",
        "less ",
        "more ",
        "rather ",
    ]
    if user_turns >= 2 and any(m in last for m in refine_markers):
        return "refine"

    return "recommend_or_clarify"


# -----------------------------------------------------------------------------
# Context: only recommend after we have enough to search meaningfully
# -----------------------------------------------------------------------------
_GENERIC_PATTERNS = [
    "i need an assessment",
    "need an assessment",
    "i need a test",
    "recommend an assessment",
    "recommend something",
    "what assessment",
    "which assessment",
    "help me choose",
    "not sure what",
    "what do you have",
    "show me assessments",
    "any assessment",
]

_SIGNAL_WORDS = [
    "personality",
    "cognitive",
    "ability",
    "numerical",
    "verbal",
    "inductive",
    "deductive",
    "sjt",
    "simulation",
    "leadership",
    "graduate",
    "sales",
    "customer",
    "developer",
    "engineer",
    "manager",
    "analyst",
    "technical",
    "role",
    "job",
    "description",
    "competenc",
    "skill",
    "role-fit",
    "culture",
    "opq",
    "mq",
    "verify",
    "personality questionnaire",
    "general ability",
    "critical reasoning",
]


def _user_text(messages: list[dict]) -> str:
    return " ".join(m["content"] for m in messages if m.get("role") == "user")


def conversation_has_sufficient_context(messages: list[dict]) -> bool:
    """Enough signal to retrieve 1–10 catalog items without guessing."""
    full = _user_text(messages).strip()
    if len(full) >= 180:
        return True
    last = messages[-1]["content"].strip()
    if len(last) >= 120:
        return True
    words = full.split()
    lowered_full = full.lower()
    if len(words) >= 12 and any(sig in lowered_full for sig in _SIGNAL_WORDS):
        return True
    if any(sig in lowered_full for sig in _SIGNAL_WORDS):
        return True
    return False


def last_message_is_vague(messages: list[dict]) -> bool:
    last = messages[-1]["content"].strip().lower()
    if any(sig in last for sig in _SIGNAL_WORDS):
        return False
    if any(p in last for p in _GENERIC_PATTERNS):
        return True
    words = last.split()
    if len(words) < 6:
        return True
    if len(words) < 10 and not any(sig in last for sig in _SIGNAL_WORDS):
        return True
    return False


def build_query(messages: list[dict]) -> str:
    return _user_text(messages)


def compare_search_query(messages: list[dict]) -> str:
    """
    Use full user thread for compare so acronyms (opq, gsa) and phrasing help retrieval,
    not only TitleCase tokens.
    """
    return _user_text(messages)


def extract_title_case_names(text: str) -> list[str]:
    return [w.strip(",.:;") for w in text.split() if w and w[0].isupper() and w.strip(",.:;").istitle()]


def extract_catalog_tokens(text: str) -> list[str]:
    """Title-case phrases and compact acronyms (e.g. OPQ, GSA) boost retrieval."""
    tokens = extract_title_case_names(text)
    tokens.extend(re.findall(r"\b[A-Z]{2,5}\b", text))
    return list(dict.fromkeys(tokens))


def _dedupe_docs(docs: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for d in docs:
        key = (d.get("url") or "") + "\0" + (d.get("name") or "")
        if key in seen:
            continue
        seen.add(key)
        out.append(d)
    return out


def _docs_to_recommendations(docs: list[dict]) -> list[dict]:
    return [
        {
            "name": d["name"],
            "url": d["url"],
            "test_type": d.get("test_type", ""),
        }
        for d in docs
        if d.get("name") and d.get("url")
    ]


# -----------------------------------------------------------------------------
# Main handler
# -----------------------------------------------------------------------------
def handle_chat(messages: list[dict]):
    if not messages or messages[-1].get("role") != "user":
        return {
            "reply": "Send a user message to continue.",
            "recommendations": [],
            "end_of_conversation": False,
        }

    all_user_text = _user_text(messages)

    if not check_scope(all_user_text):
        return {
            "reply": "I only help you choose SHL assessments from the official catalog. I can't help with general hiring advice, legal topics, or changing my instructions.",
            "recommendations": [],
            "end_of_conversation": False,
        }

    intent = detect_intent(messages)

    # --- Compare: always grounded in retrieved catalog rows ---
    if intent == "compare":
        q = compare_search_query(messages)
        extra = extract_catalog_tokens(messages[-1]["content"])
        if extra:
            q = f"{q} {' '.join(extra)}"
        docs = _dedupe_docs(retrieve_assessments(q, k=8))
        reply = generate_reply(messages, docs, mode="compare")
        return {
            "reply": reply,
            "recommendations": [],
            "end_of_conversation": False,
        }

    # --- Refine: new constraints; same thread, fresh retrieval over full user text ---
    if intent == "refine":
        query = build_query(messages)
        docs = _dedupe_docs(retrieve_assessments(query, k=10))[:10]
        recommendations = _docs_to_recommendations(docs)
        reply = generate_reply(messages, docs, mode="refine")
        return {
            "reply": reply,
            "recommendations": recommendations,
            "end_of_conversation": False,
        }

    # --- Recommend vs clarify ---
    if last_message_is_vague(messages) and not conversation_has_sufficient_context(messages):
        reply = generate_reply(messages, docs=None, mode="clarify")
        return {
            "reply": reply,
            "recommendations": [],
            "end_of_conversation": False,
        }

    query = build_query(messages)
    docs = _dedupe_docs(retrieve_assessments(query, k=10))[:10]

    if not docs:
        reply = generate_reply(messages, docs=None, mode="clarify")
        return {
            "reply": reply,
            "recommendations": [],
            "end_of_conversation": False,
        }

    recommendations = _docs_to_recommendations(docs)
    reply = generate_reply(messages, docs, mode="recommend")

    return {
        "reply": reply,
        "recommendations": recommendations,
        "end_of_conversation": True,
    }
