import textwrap
from datetime import datetime

import pandas as pd
import streamlit as st

from matching import (
    build_circle_title,
    classify_challenge,
    diagnose_problem,
    extract_target_terms,
    load_profiles,
    load_templates,
    rank_profiles,
    select_circle_members,
    select_warm_intros,
)
from prompts import (
    fallback_next_steps,
    improve_diagnosis,
    improve_outreach,
    optional_openai_available,
    privacy_notes,
)


st.set_page_config(
    page_title="WHU Alumni Circle Agent",
    page_icon="WHU",
    layout="wide",
)


SAMPLE_CHALLENGE = (
    "I am a WHU MBA alumnus currently working in automotive strategy. "
    "I want to move into climate-tech venture capital in Germany, but I do not know "
    "which skills I need, whom to speak with, or how to start."
)


def inject_styles():
    st.markdown(
        """
        <style>
        :root {
            --whu-navy: #10243e;
            --whu-blue: #1f5f99;
            --whu-green: #2f8f6f;
            --soft-bg: #f6f8fb;
            --line: #d9e1ea;
            --ink: #132238;
            --muted: #607086;
        }
        .stApp {
            background: var(--soft-bg);
            color: var(--ink);
        }
        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--line);
        }
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1380px;
        }
        .hero {
            padding: 10px 0 18px 0;
            border-bottom: 1px solid var(--line);
            margin-bottom: 20px;
        }
        .eyebrow {
            color: var(--whu-blue);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0;
            text-transform: uppercase;
            margin-bottom: 6px;
        }
        .hero h1 {
            font-size: 2.2rem;
            line-height: 1.1;
            margin: 0;
            color: var(--whu-navy);
        }
        .hero p {
            color: var(--muted);
            font-size: 1rem;
            max-width: 860px;
            margin-top: 10px;
        }
        .metric-row {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin: 8px 0 22px 0;
        }
        .metric {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 14px 16px;
        }
        .metric span {
            display: block;
            color: var(--muted);
            font-size: 0.78rem;
            margin-bottom: 4px;
        }
        .metric strong {
            color: var(--whu-navy);
            font-size: 1rem;
        }
        .section {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 18px;
            margin-bottom: 16px;
        }
        .section h2, .section h3 {
            color: var(--whu-navy);
            margin-top: 0;
            letter-spacing: 0;
        }
        .alumni-card {
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
            background: #ffffff;
        }
        .alumni-head {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: flex-start;
            border-bottom: 1px solid #edf1f5;
            padding-bottom: 10px;
            margin-bottom: 10px;
        }
        .alumni-head strong {
            color: var(--whu-navy);
            font-size: 1rem;
        }
        .score {
            color: var(--whu-green);
            font-weight: 700;
            white-space: nowrap;
        }
        .tag {
            display: inline-block;
            border: 1px solid #c9d8e7;
            border-radius: 999px;
            padding: 3px 8px;
            margin: 2px 4px 2px 0;
            color: #34516f;
            font-size: 0.76rem;
            background: #f8fbff;
        }
        .message {
            background: #f8fafc;
            border-left: 4px solid var(--whu-blue);
            padding: 12px;
            border-radius: 4px;
            white-space: pre-wrap;
            color: #25364d;
            font-size: 0.9rem;
        }
        .privacy {
            border-left: 4px solid #b7791f;
            background: #fffaf0;
            padding: 14px 16px;
            border-radius: 6px;
        }
        .small-muted {
            color: var(--muted);
            font-size: 0.9rem;
        }
        @media (max-width: 900px) {
            .metric-row {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_profile_card(profile, outreach_message=None):
    tags = [tag.strip() for tag in profile.get("expertise_tags", "").split(",") if tag.strip()]
    reasons = profile.get("match_reasons", [])
    st.markdown(
        f"""
        <div class="alumni-card">
            <div class="alumni-head">
                <div>
                    <strong>{profile['name']}</strong><br>
                    <span class="small-muted">MBA {profile['mba_year']} · {profile['location']} · {profile['industry']} · {profile['function']}</span>
                </div>
                <div class="score">Score {profile['score']}</div>
            </div>
            <div>{''.join(f'<span class="tag">{tag}</span>' for tag in tags[:6])}</div>
            <p class="small-muted">{profile['bio']}</p>
            <p><strong>Why this match:</strong> {', '.join(reasons[:4])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if outreach_message:
        st.markdown("**Draft outreach**")
        st.markdown(f'<div class="message">{outreach_message}</div>', unsafe_allow_html=True)


def markdown_export(context, diagnosis, warm_intros, outreach_messages, circle, next_steps, notes):
    lines = [
        "# WHU Alumni Circle Agent Recommendation",
        "",
        f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_",
        "",
        "## Challenge",
        context["challenge"],
        "",
        "## Problem Diagnosis",
        diagnosis,
        "",
        "## Warm Intro Recommendations",
    ]
    for profile in warm_intros:
        lines.extend(
            [
                f"### {profile['name']} · MBA {profile['mba_year']}",
                f"- Location: {profile['location']}",
                f"- Industry / Function: {profile['industry']} / {profile['function']}",
                f"- Match score: {profile['score']}",
                f"- Match reasons: {', '.join(profile['match_reasons'][:4])}",
                "",
                "Draft message:",
                "",
                outreach_messages[profile["id"]],
                "",
            ]
        )

    lines.extend(
        [
            "## Peer Problem-Solving Circle",
            f"**Title:** {circle['title']}",
            f"**Format:** {circle['format']}",
            f"**Duration:** {circle['duration']}",
            "",
            "### Suggested Members",
        ]
    )
    for member in circle["members"]:
        lines.append(f"- {member['name']} · MBA {member['mba_year']} · {member['location']} · {member['industry']} / {member['function']}")

    lines.extend(["", "### Rationale", circle["rationale"], "", "### Agenda"])
    for item in circle["agenda"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Suggested Next Steps"])
    for step in next_steps:
        lines.append(f"- {step}")

    lines.extend(["", "## Privacy And Trust Notes"])
    for note in notes:
        lines.append(f"- {note}")

    return "\n".join(lines)


def run_recommendation(challenge, current_role, target_goal, preferred_geography, support_type, confidential_mode):
    profiles = load_profiles()
    templates = load_templates()
    category = classify_challenge(challenge, current_role, target_goal)
    target_terms = extract_target_terms(challenge, current_role, target_goal, preferred_geography)
    ranked = rank_profiles(profiles, category, target_terms, support_type, challenge)
    warm_intros = select_warm_intros(ranked)
    circle_members = select_circle_members(ranked)
    circle_title = build_circle_title(category, target_terms, target_goal)
    template = templates.get(category, templates["general_advice"])

    context = {
        "challenge": challenge,
        "current_role": current_role,
        "target_goal": target_goal,
        "preferred_geography": preferred_geography,
        "support_type": support_type,
        "confidential_mode": confidential_mode,
        "category": category,
    }
    fallback_diagnosis = diagnose_problem(category, target_terms, current_role, target_goal, preferred_geography)
    diagnosis = improve_diagnosis(context, fallback_diagnosis)
    outreach_messages = {
        profile["id"]: improve_outreach(context, profile, confidential_mode) for profile in warm_intros
    }
    circle = {
        "title": circle_title,
        "format": template["circle_format"],
        "duration": template["recommended_duration"],
        "agenda": template["agenda"],
        "members": circle_members,
        "rationale": (
            "This circle combines alumni who match the target industry, target function, geography, and willingness "
            "to participate in peer problem-solving. It gives the user both expert input and peers facing related decisions."
        ),
        "output": template["output"],
    }
    next_steps = fallback_next_steps(category, warm_intros, circle_title)
    notes = privacy_notes(confidential_mode)

    return context, diagnosis, ranked, warm_intros, outreach_messages, circle, next_steps, notes


inject_styles()

with st.sidebar:
    st.header("Challenge Intake")
    st.caption("Use the sample for a fast hackathon demo, or enter a new alumni challenge.")

    if "challenge" not in st.session_state:
        st.session_state.challenge = SAMPLE_CHALLENGE
    if st.button("Load sample demo input", use_container_width=True):
        st.session_state.challenge = SAMPLE_CHALLENGE
        st.session_state.current_role = "Automotive strategy"
        st.session_state.target_goal = "Climate-tech venture capital"
        st.session_state.preferred_geography = "Germany"
        st.session_state.support_type = "Both"
        st.session_state.confidential_mode = True

    challenge = st.text_area(
        "Professional challenge",
        key="challenge",
        height=180,
        placeholder="Describe the career or business challenge you want help with.",
    )
    current_role = st.text_input("Current role", key="current_role", value=st.session_state.get("current_role", "Automotive strategy"))
    target_goal = st.text_input("Target goal", key="target_goal", value=st.session_state.get("target_goal", "Climate-tech venture capital"))
    preferred_geography = st.text_input("Preferred geography", key="preferred_geography", value=st.session_state.get("preferred_geography", "Germany"))
    support_type = st.radio(
        "Preferred support type",
        ["1:1 warm intros", "Peer circle", "Both"],
        key="support_type",
        index=["1:1 warm intros", "Peer circle", "Both"].index(st.session_state.get("support_type", "Both")),
    )
    confidential_mode = st.checkbox(
        "Confidential mode",
        key="confidential_mode",
        value=st.session_state.get("confidential_mode", True),
        help="Keeps sensitive details out of generated outreach messages.",
    )
    run_button = st.button("Generate recommendation", type="primary", use_container_width=True)

st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">GenAI MBA Hackathon MVP</div>
        <h1>WHU Alumni Circle Agent</h1>
        <p>Turn a live alumni challenge into the right warm intros, a focused peer problem-solving circle, and a practical next-action brief.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not challenge.strip():
    st.info("Enter a professional challenge in the sidebar to generate an alumni recommendation brief.")
    st.stop()

if run_button or "last_result" not in st.session_state:
    with st.spinner("Matching alumni and preparing the recommendation brief..."):
        st.session_state.last_result = run_recommendation(
            challenge,
            current_role,
            target_goal,
            preferred_geography,
            support_type,
            confidential_mode,
        )

context, diagnosis, ranked, warm_intros, outreach_messages, circle, next_steps, notes = st.session_state.last_result

st.markdown(
    f"""
    <div class="metric-row">
        <div class="metric"><span>Challenge category</span><strong>{context['category'].replace('_', ' ').title()}</strong></div>
        <div class="metric"><span>Ranked alumni</span><strong>{len(ranked)} top matches</strong></div>
        <div class="metric"><span>Warm intros</span><strong>{len(warm_intros)} recommended</strong></div>
        <div class="metric"><span>Peer circle</span><strong>{len(circle['members'])} suggested members</strong></div>
    </div>
    """,
    unsafe_allow_html=True,
)

if optional_openai_available():
    st.success("Optional OpenAI enhancement is active. Fallback matching logic remains visible and deterministic.")
else:
    st.info("Running in deterministic demo mode. Add OPENAI_API_KEY to enhance diagnosis and message wording.")

left, right = st.columns([1.15, 0.85], gap="large")

with left:
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("Problem Diagnosis")
    st.write(diagnosis)
    st.caption("The agent converts a natural-language alumni need into structured signals for matching and circle design.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("Top 3 Warm Intro Recommendations")
    for profile in warm_intros:
        render_profile_card(profile, outreach_messages[profile["id"]])

with right:
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("Suggested Peer Problem-Solving Circle")
    st.markdown(f"### {circle['title']}")
    st.write(f"**Format:** {circle['format']}")
    st.write(f"**Duration:** {circle['duration']}")
    st.write(circle["rationale"])
    st.markdown("**Suggested members**")
    member_rows = [
        {
            "Name": member["name"],
            "MBA": member["mba_year"],
            "Location": member["location"],
            "Focus": f"{member['industry']} / {member['function']}",
        }
        for member in circle["members"]
    ]
    st.dataframe(pd.DataFrame(member_rows), hide_index=True, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("45-Minute Agenda")
    for agenda_item in circle["agenda"]:
        st.write(f"- {agenda_item}")
    st.caption(circle["output"])
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="section">', unsafe_allow_html=True)
st.subheader("Suggested Next Steps")
for step in next_steps:
    st.write(f"- {step}")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="privacy">', unsafe_allow_html=True)
st.subheader("Privacy And Trust Notes")
for note in notes:
    st.write(f"- {note}")
st.markdown("</div>", unsafe_allow_html=True)

export_text = markdown_export(context, diagnosis, warm_intros, outreach_messages, circle, next_steps, notes)
st.download_button(
    "Download Markdown recommendation",
    data=export_text,
    file_name="whu_alumni_circle_agent_recommendation.md",
    mime="text/markdown",
    use_container_width=True,
)

with st.expander("Show ranked matching table"):
    table = pd.DataFrame(
        [
            {
                "Rank": index + 1,
                "Name": profile["name"],
                "MBA": profile["mba_year"],
                "Location": profile["location"],
                "Industry": profile["industry"],
                "Function": profile["function"],
                "Score": profile["score"],
                "Top reasons": ", ".join(profile["match_reasons"][:3]),
            }
            for index, profile in enumerate(ranked)
        ]
    )
    st.dataframe(table, hide_index=True, use_container_width=True)
