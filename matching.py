import csv
import json
import re
from pathlib import Path


CATEGORIES = [
    "career_transition",
    "entrepreneurship",
    "fundraising",
    "leadership",
    "industry_switch",
    "geographic_move",
    "functional_expertise",
    "board_or_advisory",
    "hiring",
    "peer_benchmarking",
    "general_advice",
]

CATEGORY_KEYWORDS = {
    "career_transition": ["career", "transition", "move", "switch", "leave", "join", "role", "next step"],
    "entrepreneurship": ["startup", "founder", "venture", "build", "launch", "co-founder", "entrepreneur"],
    "fundraising": ["fundraising", "raise", "investor", "seed", "series", "capital", "pitch"],
    "leadership": ["leadership", "lead", "executive", "team", "stakeholder", "manager", "conflict"],
    "industry_switch": ["industry", "sector", "climate", "mobility", "healthcare", "finance", "saas"],
    "geographic_move": ["geography", "relocate", "move to", "market", "germany", "us", "asia", "dubai"],
    "functional_expertise": ["skills", "expertise", "function", "operations", "product", "strategy", "sales"],
    "board_or_advisory": ["board", "advisory", "governance", "advisor"],
    "hiring": ["hiring", "recruit", "talent", "candidate", "team design"],
    "peer_benchmarking": ["benchmark", "compare", "peers", "best practice", "what others"],
}

STOPWORDS = {
    "about",
    "after",
    "alumni",
    "because",
    "currently",
    "from",
    "have",
    "into",
    "know",
    "need",
    "start",
    "that",
    "the",
    "this",
    "want",
    "whom",
    "with",
    "working",
}


def load_profiles(path="alumni_profiles.csv"):
    with open(path, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def load_templates(path="circle_templates.json"):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize(text):
    return (text or "").lower()


def tokenize(text):
    words = re.findall(r"[a-zA-Z][a-zA-Z\-]+", normalize(text))
    return {word for word in words if len(word) > 2 and word not in STOPWORDS}


def classify_challenge(challenge, current_role="", target_goal=""):
    text = normalize(" ".join([challenge, current_role, target_goal]))
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        scores[category] = sum(1 for keyword in keywords if keyword in text)

    if any(word in text for word in ["move", "switch", "transition", "leave", "join"]):
        scores["career_transition"] = scores.get("career_transition", 0) + 2
    if any(word in text for word in ["climate", "mobility", "healthcare", "finance", "vc", "venture capital"]):
        scores["industry_switch"] = scores.get("industry_switch", 0) + 1
    if any(word in text for word in ["germany", "berlin", "munich", "frankfurt", "london", "singapore", "dubai", "new york"]):
        scores["geographic_move"] = scores.get("geographic_move", 0) + 1

    best_category = max(scores, key=scores.get)
    if scores[best_category] == 0:
        return "general_advice"
    return best_category


def extract_target_terms(challenge, current_role="", target_goal="", preferred_geography=""):
    text = normalize(" ".join([challenge, current_role, target_goal]))
    target_industries = []
    target_functions = []

    industry_terms = {
        "climate": "climate tech",
        "climate-tech": "climate tech",
        "mobility": "mobility",
        "automotive": "automotive",
        "healthcare": "healthcare",
        "finance": "finance",
        "private equity": "private equity",
        "saas": "B2B SaaS",
        "b2b": "B2B SaaS",
        "sustainability": "sustainability",
    }
    function_terms = {
        "vc": "venture capital",
        "venture capital": "venture capital",
        "investing": "venture capital",
        "investment": "investment",
        "strategy": "strategy",
        "product": "product management",
        "operations": "operations",
        "founder": "entrepreneurship",
        "fundraising": "fundraising",
        "leadership": "leadership",
        "board": "board advisory",
        "hiring": "hiring",
    }

    for needle, label in industry_terms.items():
        if needle in text and label not in target_industries:
            target_industries.append(label)
    for needle, label in function_terms.items():
        if needle in text and label not in target_functions:
            target_functions.append(label)

    return {
        "industries": target_industries,
        "functions": target_functions,
        "geography": preferred_geography.strip(),
        "keywords": tokenize(text),
    }


def profile_text(profile):
    fields = [
        profile.get("industry", ""),
        profile.get("function", ""),
        profile.get("expertise_tags", ""),
        profile.get("current_challenges", ""),
        profile.get("bio", ""),
    ]
    return normalize(" ".join(fields))


def score_profile(profile, category, target_terms, support_type, challenge):
    text = profile_text(profile)
    location = normalize(profile.get("location", ""))
    willingness = normalize(profile.get("willingness", ""))
    score = 0
    reasons = []

    for industry in target_terms["industries"]:
        if normalize(industry) in text:
            score += 3
            reasons.append(f"strong {industry} relevance")

    for function in target_terms["functions"]:
        if normalize(function) in text:
            score += 3
            reasons.append(f"matches target function: {function}")

    geography = normalize(target_terms["geography"])
    if geography and (geography in location or location in geography):
        score += 2
        reasons.append(f"based in {profile.get('location')}")

    category_words = category.replace("_", " ")
    if category_words in text or any(word in text for word in CATEGORY_KEYWORDS.get(category, [])):
        score += 2
        reasons.append(f"relevant to {category.replace('_', ' ')}")

    wants_warm_intro = support_type in ["1:1 warm intros", "Both"]
    wants_circle = support_type in ["Peer circle", "Both"]
    if wants_warm_intro and "mentor" in willingness:
        score += 2
        reasons.append("opted in for mentoring")
    if wants_circle and "circle" in willingness:
        score += 2
        reasons.append("open to peer circles")

    profile_keywords = tokenize(text)
    overlap = sorted(tokenize(challenge).intersection(profile_keywords))
    score += min(len(overlap), 6)
    if overlap:
        reasons.append("keyword overlap: " + ", ".join(overlap[:5]))

    if not reasons:
        reasons.append("broadly relevant WHU alumni profile")

    return score, reasons


def rank_profiles(profiles, category, target_terms, support_type, challenge):
    ranked = []
    for profile in profiles:
        score, reasons = score_profile(profile, category, target_terms, support_type, challenge)
        ranked.append({**profile, "score": score, "match_reasons": reasons})

    return sorted(ranked, key=lambda item: (item["score"], item["mba_year"]), reverse=True)[:7]


def select_warm_intros(ranked_profiles):
    mentor_profiles = [profile for profile in ranked_profiles if "mentor" in normalize(profile.get("willingness", ""))]
    return (mentor_profiles + ranked_profiles)[:3]


def select_circle_members(ranked_profiles):
    circle_profiles = [profile for profile in ranked_profiles if "circle" in normalize(profile.get("willingness", ""))]
    selected = circle_profiles[:7]
    if len(selected) < 5:
        for profile in ranked_profiles:
            if profile not in selected:
                selected.append(profile)
            if len(selected) == 5:
                break
    return selected[:7]


def build_circle_title(category, target_terms, target_goal):
    if target_terms["industries"] and target_terms["functions"]:
        return f"From {target_goal or 'Current Role'} to {target_terms['industries'][0].title()} {target_terms['functions'][0].title()}"
    if target_terms["industries"]:
        return f"Navigating {target_terms['industries'][0].title()} Opportunities"
    return category.replace("_", " ").title() + " Circle"


def diagnose_problem(category, target_terms, current_role, target_goal, preferred_geography):
    parts = [f"Category: {category.replace('_', ' ')}."]
    if current_role and target_goal:
        parts.append(f"The challenge appears to be moving from {current_role} toward {target_goal}.")
    elif target_goal:
        parts.append(f"The target goal is {target_goal}.")
    if target_terms["industries"]:
        parts.append("Relevant industry signals: " + ", ".join(target_terms["industries"]) + ".")
    if target_terms["functions"]:
        parts.append("Relevant function signals: " + ", ".join(target_terms["functions"]) + ".")
    if preferred_geography:
        parts.append(f"Preferred geography: {preferred_geography}.")
    return " ".join(parts)
