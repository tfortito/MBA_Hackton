import os


def privacy_notes(confidential_mode):
    detail = "Confidential mode is on, so generated messages avoid unnecessary sensitive details." if confidential_mode else "Confidential mode is off, but outreach still needs user approval."
    return [
        "Alumni are only recommended from opt-in mock profile data.",
        "No message is sent automatically by this prototype.",
        "User approval is required before any outreach.",
        detail,
        "Peer circles require participant consent before scheduling.",
        "The agent supports matching and preparation; it does not replace human judgment.",
    ]


def fallback_outreach(user_context, alumnus, confidential_mode):
    challenge_line = (
        f"I am exploring {user_context['target_goal']} and would value your perspective."
        if confidential_mode
        else f"I am a WHU MBA alumnus currently in {user_context['current_role']} and exploring {user_context['target_goal']}."
    )
    reason = alumnus["match_reasons"][0] if alumnus.get("match_reasons") else "your relevant WHU alumni experience"
    return (
        f"Hi {alumnus['name'].split()[0]},\n\n"
        f"{challenge_line} The WHU Alumni Circle Agent suggested you because of {reason}. "
        "Would you be open to a 20-minute conversation, or to joining a small WHU peer circle on this topic?\n\n"
        "Best,\n"
        "A fellow WHU MBA alumnus"
    )


def fallback_next_steps(category, warm_intros, circle_title):
    names = ", ".join(profile["name"].split()[0] for profile in warm_intros)
    return [
        f"Approve or edit the three draft intro messages for {names}.",
        f"Invite selected alumni to the peer circle: {circle_title}.",
        "Ask each participant for one suggested resource or contact before the session.",
        "Use the agenda to capture 2-3 concrete actions per participant.",
        "Review privacy settings before sharing any sensitive career or business details.",
    ]


def optional_openai_available():
    return bool(os.getenv("OPENAI_API_KEY"))


def generate_with_openai(prompt, fallback):
    if not optional_openai_available():
        return fallback
    try:
        from openai import OpenAI

        client = OpenAI()
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=prompt,
            temperature=0.4,
            max_output_tokens=450,
        )
        return response.output_text.strip() or fallback
    except Exception:
        return fallback


def improve_outreach(user_context, alumnus, confidential_mode):
    fallback = fallback_outreach(user_context, alumnus, confidential_mode)
    prompt = f"""
Draft a concise, respectful alumni outreach message.

User context:
- Current role: {user_context['current_role']}
- Target goal: {user_context['target_goal']}
- Geography: {user_context['preferred_geography']}
- Confidential mode: {confidential_mode}

Alumnus:
- Name: {alumnus['name']}
- MBA year: {alumnus['mba_year']}
- Location: {alumnus['location']}
- Industry: {alumnus['industry']}
- Function: {alumnus['function']}
- Bio: {alumnus['bio']}
- Match reasons: {', '.join(alumnus.get('match_reasons', []))}

Rules:
- Do not imply an email has been sent.
- Ask for either a 20-minute conversation or joining a small WHU peer circle.
- If confidential mode is true, keep the user's situation high-level.
- Keep it under 120 words.
"""
    return generate_with_openai(prompt, fallback)


def improve_diagnosis(user_context, fallback):
    prompt = f"""
Write a two-sentence problem diagnosis for this WHU alumni matching request.
Be specific, practical, and concise.

Challenge: {user_context['challenge']}
Current role: {user_context['current_role']}
Target goal: {user_context['target_goal']}
Preferred geography: {user_context['preferred_geography']}
Category: {user_context['category']}
"""
    return generate_with_openai(prompt, fallback)
