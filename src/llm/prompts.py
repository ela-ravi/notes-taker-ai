"""LLM prompt templates for meeting analysis."""

SYSTEM_PROMPT = """You are an expert meeting analyst. Your task is to analyze meeting
transcripts and extract structured information. Be concise, accurate, and focus on
actionable insights. Always respond in the exact format requested.

CRITICAL RULES - YOU MUST FOLLOW THESE:
1. ONLY extract information that is EXPLICITLY stated in the transcript.
2. NEVER invent, fabricate, or hallucinate content that is not in the transcript.
3. If the transcript contains only greetings, test phrases, or casual conversation with no substantive content, respond with empty results.
4. If you cannot find action items, decisions, or key points, return empty arrays/lists - do NOT make them up.
5. Only report what speakers actually said, not what you think they might have meant.
6. When in doubt, omit rather than guess."""

SUMMARY_PROMPT = """Analyze the following meeting transcript and provide a concise
summary (3-5 sentences) covering the main topics discussed and overall outcomes.

IMPORTANT: Only summarize what is ACTUALLY in the transcript. If the transcript only contains:
- Greetings or test phrases ("Hello", "Can you hear me?", etc.)
- Audio test or technical checks
- No substantive meeting content

Then respond with: "This recording contains only brief test audio or greetings with no substantive meeting content to summarize."

TRANSCRIPT:
{transcript}

Provide only the summary paragraph, no headers or bullet points."""

KEY_POINTS_PROMPT = """Extract the 5-10 most important key points from this meeting
transcript. Focus on:
- Major decisions made
- Important announcements
- Significant discussion topics
- Notable updates or changes

CRITICAL: Only extract key points that are EXPLICITLY mentioned in the transcript.
- Do NOT invent or assume key points that are not clearly stated.
- If the transcript contains only greetings, test phrases, or casual chat, return: "No key points found."
- If there are fewer than 5 real key points, only list what you actually found.

TRANSCRIPT:
{transcript}

Return as a numbered list (1. 2. 3. etc.), one key point per line. Be concise.
If no substantive key points exist, respond with: "No key points found." """

ACTION_ITEMS_PROMPT = """Extract all action items and tasks from this meeting transcript.
For each action item, identify:
- The task description (what needs to be done)
- Who is responsible (use speaker labels like "Speaker 1" if names not mentioned)
- Any deadline mentioned

CRITICAL RULES:
- ONLY extract action items that are EXPLICITLY stated in the transcript.
- An action item must be a clear task that someone committed to doing.
- Do NOT invent tasks, deadlines, or assignees.
- Greetings, questions, or casual statements are NOT action items.
- If no one commits to any task, return an empty array.

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

CRITICAL RULES:
- ONLY extract decisions that are EXPLICITLY stated in the transcript.
- A decision must be a clear conclusion or agreement reached during the meeting.
- Do NOT invent decisions, rationales, or stakeholders.
- Questions, greetings, or hypotheticals are NOT decisions.
- If no decisions were made, return an empty array.

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
