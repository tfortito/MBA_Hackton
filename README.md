# WHU Alumni Circle Agent

A hackathon MVP for a GenAI-powered WHU MBA alumni experience.

The app lets an alumnus describe a live career or business challenge, then recommends:

- 3 relevant alumni for 1:1 warm intros
- 1 peer problem-solving circle with 5-7 suggested members
- Personalized outreach drafts
- A 45-minute circle agenda
- Practical next steps
- Privacy and trust notes
- Markdown export

## Why It Exists

Most alumni platforms center on directories, events, and newsletters. WHU Alumni Circle Agent shows how the alumni network can become continuous, personalized professional support.

## Tech Stack

- Python
- Streamlit
- Local CSV and JSON mock data
- Deterministic fallback matching logic
- Optional OpenAI enhancement when `OPENAI_API_KEY` is available

No database, authentication, live WHU system, email sending, or LinkedIn scraping is required.

## Files

- `app.py`: Streamlit app and UI
- `matching.py`: classification, scoring, ranking, and circle selection
- `prompts.py`: deterministic messages and optional OpenAI generation helpers
- `alumni_profiles.csv`: mock WHU MBA alumni profiles
- `circle_templates.json`: category-specific circle templates
- `requirements.txt`: Python dependencies

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL shown by Streamlit.

## Optional OpenAI Integration

The app works without an API key. If available, set:

```bash
export OPENAI_API_KEY="your-key"
```

Optional generation improves the diagnosis wording and outreach messages. Matching remains deterministic and explainable.

## Demo Input

```text
I am a WHU MBA alumnus currently working in automotive strategy. I want to move into climate-tech venture capital in Germany, but I do not know which skills I need, whom to speak with, or how to start.
```

## Privacy And Trust Principles

- Alumni are only recommended from opt-in mock profile data.
- No message is sent automatically.
- User approval is required before outreach.
- Confidential mode avoids unnecessary sensitive details in generated messages.
- Peer circles require participant consent.
- The agent supports matching and preparation; it does not replace human judgment.
