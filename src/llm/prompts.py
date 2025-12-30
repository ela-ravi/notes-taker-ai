"""LLM prompt templates for meeting analysis."""

SYSTEM_PROMPT = """You are an expert meeting analyst. Your task is to analyze meeting
transcripts and extract structured information. Be concise, accurate, and focus on
actionable insights. Always respond in the exact format requested."""

SUMMARY_PROMPT = """Analyze the following meeting transcript and provide a concise
summary (3-5 sentences) covering the main topics discussed and overall outcomes.

TRANSCRIPT:
{transcript}

Provide only the summary paragraph, no headers or bullet points."""

KEY_POINTS_PROMPT = """Extract the 5-10 most important key points from this meeting
transcript. Focus on:
- Major decisions made
- Important announcements
- Significant discussion topics
- Notable updates or changes

TRANSCRIPT:
{transcript}

Return as a numbered list (1. 2. 3. etc.), one key point per line. Be concise."""

ACTION_ITEMS_PROMPT = """Extract all action items and tasks from this meeting transcript.
For each action item, identify:
- The task description (what needs to be done)
- Who is responsible (use speaker labels like "Speaker 1" if names not mentioned)
- Any deadline mentioned

TRANSCRIPT:
{transcript}

Return ONLY a valid JSON array with this exact format, no other text:
[
  {{"task": "description of the task", "assignee": "Speaker X or name", "deadline": "date or null"}}
]

If no action items found, return: []"""

DECISIONS_PROMPT = """Identify all decisions made during this meeting. For each decision:
- What was decided
- The reasoning (if discussed)
- Who was involved (use speaker labels)

TRANSCRIPT:
{transcript}

Return ONLY a valid JSON array with this exact format, no other text:
[
  {{"decision": "what was decided", "rationale": "reasoning or null", "stakeholders": ["Speaker 1", "Speaker 2"]}}
]

If no decisions found, return: []"""

SPEAKER_ANALYSIS_PROMPT = """Analyze the speaking patterns in this meeting transcript.
For each speaker, provide:
- Their main contributions or topics
- Their apparent role (facilitator, technical expert, etc.)
- Key statements they made

TRANSCRIPT:
{transcript}

Return as a brief analysis for each speaker mentioned."""

MEETING_TYPE_PROMPT = """Based on this transcript, classify the meeting type.
Options: standup, planning, retrospective, review, brainstorm, one-on-one, all-hands, other

TRANSCRIPT (first 500 chars):
{transcript}

Return only the meeting type, single word."""
