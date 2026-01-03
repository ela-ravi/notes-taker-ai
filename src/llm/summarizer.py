"""Meeting summarization using LLM (Ollama or HuggingFace)."""

from dataclasses import dataclass, field
from typing import Optional

from ..utils.logging_config import get_logger
from .base import LLMClient
from .factory import create_llm_client
from .prompts import (
    ACTION_ITEMS_PROMPT,
    DECISIONS_PROMPT,
    KEY_POINTS_PROMPT,
    MEETING_TYPE_PROMPT,
    SUMMARY_PROMPT,
    SYSTEM_PROMPT,
)

logger = get_logger("llm.summarizer")


@dataclass
class ActionItem:
    """An action item from the meeting."""

    task: str
    assignee: Optional[str] = None
    deadline: Optional[str] = None


@dataclass
class Decision:
    """A decision made during the meeting."""

    decision: str
    rationale: Optional[str] = None
    stakeholders: list[str] = field(default_factory=list)


@dataclass
class MeetingSummary:
    """Complete meeting summary from LLM analysis."""

    summary: str = ""
    key_points: list[str] = field(default_factory=list)
    action_items: list[ActionItem] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    meeting_type: str = "other"


class MeetingSummarizer:
    """
    Summarizes meeting transcripts using LLM.

    This class orchestrates multiple LLM calls to extract different
    types of information from a meeting transcript. Supports both
    Ollama (local) and HuggingFace (cloud) providers.
    """

    def __init__(self, client: Optional[LLMClient] = None):
        """
        Initialize the summarizer.

        Args:
            client: LLMClient instance (created from config if not provided)
        """
        self.client = client or create_llm_client()

    def summarize(self, transcript: str, custom_context: Optional[str] = None) -> MeetingSummary:
        """
        Generate a complete meeting summary.

        Args:
            transcript: The meeting transcript text
            custom_context: Optional user-provided context/instructions for the summary

        Returns:
            MeetingSummary with all extracted information
        """
        logger.info("Starting meeting summarization...")
        if custom_context:
            logger.info(f"Using custom context: {custom_context[:100]}...")

        if not transcript or len(transcript.strip()) < 50:
            logger.warning("Transcript too short for meaningful analysis")
            return MeetingSummary(
                summary="Transcript too short for analysis.",
                meeting_type="other",
            )

        # Check if transcript is mostly test/greeting content
        if self._is_minimal_content(transcript):
            logger.warning("Transcript contains minimal substantive content")
            return MeetingSummary(
                summary="This recording contains only brief test audio or greetings with no substantive meeting content.",
                meeting_type="other",
            )

        summary = MeetingSummary()

        # Build system prompt with custom context
        system_prompt = SYSTEM_PROMPT
        if custom_context:
            system_prompt += f"\n\nAdditional context from user:\n{custom_context}"

        # Generate summary
        try:
            summary.summary = self._generate_summary(transcript, system_prompt)
            logger.info("Generated summary")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating summary: {error_msg}")
            summary.summary = f"Error generating summary: {error_msg}"

        # Extract key points
        try:
            summary.key_points = self._extract_key_points(transcript)
            logger.info(f"Extracted {len(summary.key_points)} key points")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error extracting key points: {error_msg}")
            summary.key_points = [f"Error: {error_msg}"]

        # Extract action items
        try:
            summary.action_items = self._extract_action_items(transcript)
            logger.info(f"Extracted {len(summary.action_items)} action items")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error extracting action items: {error_msg}")
            summary.action_items = [ActionItem(task=f"Error: {error_msg}")]

        # Extract decisions
        try:
            summary.decisions = self._extract_decisions(transcript)
            logger.info(f"Extracted {len(summary.decisions)} decisions")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error extracting decisions: {error_msg}")
            summary.decisions = [Decision(decision=f"Error: {error_msg}")]

        # Detect meeting type
        try:
            summary.meeting_type = self._detect_meeting_type(transcript)
            logger.info(f"Meeting type: {summary.meeting_type}")
        except Exception as e:
            logger.error(f"Error detecting meeting type: {e}")
            summary.meeting_type = "other"

        return summary

    def _generate_summary(self, transcript: str, system_prompt: Optional[str] = None) -> str:
        """Generate a concise summary of the meeting."""
        prompt = SUMMARY_PROMPT.format(transcript=self._truncate(transcript, 8000))
        response = self.client.generate(prompt, system=system_prompt or SYSTEM_PROMPT)
        return response.strip()

    def _extract_key_points(self, transcript: str) -> list[str]:
        """Extract key points from the transcript."""
        prompt = KEY_POINTS_PROMPT.format(transcript=self._truncate(transcript, 8000))
        response = self.client.generate(prompt, system=SYSTEM_PROMPT)

        # Check for "no key points" response
        response_lower = response.lower().strip()
        if "no key points" in response_lower or "no substantive" in response_lower:
            return []

        # Parse numbered list
        points = []
        for line in response.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            # Skip lines that indicate no content
            line_lower = line.lower()
            if "no key points" in line_lower or "no substantive" in line_lower:
                continue
            # Remove numbering
            if line[0].isdigit():
                # Remove "1." or "1)" style numbering
                parts = line.split(".", 1)
                if len(parts) > 1 and parts[0].strip().isdigit():
                    line = parts[1].strip()
                else:
                    parts = line.split(")", 1)
                    if len(parts) > 1 and parts[0].strip().isdigit():
                        line = parts[1].strip()
            # Remove bullet points
            line = line.lstrip("-•* ")
            if line:
                points.append(line)

        return points[:10]  # Limit to 10 points

    def _extract_action_items(self, transcript: str) -> list[ActionItem]:
        """Extract action items from the transcript."""
        prompt = ACTION_ITEMS_PROMPT.format(transcript=self._truncate(transcript, 8000))
        result = self.client.generate_json(prompt, system=SYSTEM_PROMPT)

        if not result or not isinstance(result, list):
            return []

        action_items = []
        for item in result:
            if isinstance(item, dict) and "task" in item:
                action_items.append(
                    ActionItem(
                        task=item.get("task", ""),
                        assignee=item.get("assignee"),
                        deadline=item.get("deadline"),
                    )
                )

        return action_items

    def _extract_decisions(self, transcript: str) -> list[Decision]:
        """Extract decisions from the transcript."""
        prompt = DECISIONS_PROMPT.format(transcript=self._truncate(transcript, 8000))
        result = self.client.generate_json(prompt, system=SYSTEM_PROMPT)

        if not result or not isinstance(result, list):
            return []

        decisions = []
        for item in result:
            if isinstance(item, dict) and "decision" in item:
                decisions.append(
                    Decision(
                        decision=item.get("decision", ""),
                        rationale=item.get("rationale"),
                        stakeholders=item.get("stakeholders", []),
                    )
                )

        return decisions

    def _detect_meeting_type(self, transcript: str) -> str:
        """Detect the type of meeting."""
        prompt = MEETING_TYPE_PROMPT.format(transcript=transcript[:500])
        response = self.client.generate(prompt, system=SYSTEM_PROMPT)

        # Clean and validate response
        meeting_type = response.strip().lower()
        valid_types = {
            "standup",
            "planning",
            "retrospective",
            "review",
            "brainstorm",
            "one-on-one",
            "all-hands",
            "other",
        }

        if meeting_type in valid_types:
            return meeting_type

        # Try to match partial
        for valid in valid_types:
            if valid in meeting_type:
                return valid

        return "other"

    def _truncate(self, text: str, max_chars: int) -> str:
        """Truncate text to maximum characters."""
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n\n[Transcript truncated for analysis...]"

    def _is_minimal_content(self, transcript: str) -> bool:
        """
        Check if transcript contains minimal/non-substantive content.

        Returns True if the transcript is mostly greetings, test phrases,
        or other non-meeting content.
        """
        # Normalize text
        text = transcript.lower().strip()
        words = text.split()

        # If very few words, check for common test/greeting patterns
        if len(words) < 20:
            test_patterns = [
                "hello", "hi", "hey", "can you hear", "hear me",
                "am i speaking", "testing", "test", "check", "is this working",
                "can you see", "good morning", "good afternoon", "good evening",
                "how are you", "nice to meet", "thanks for joining",
            ]
            text_lower = text
            matches = sum(1 for pattern in test_patterns if pattern in text_lower)
            # If most of the short transcript is test/greeting patterns
            if matches >= 1 and len(words) < 15:
                return True

        # Count unique substantive words (excluding common words)
        stop_words = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been",
            "i", "you", "we", "they", "it", "my", "your", "our", "their",
            "this", "that", "these", "those", "and", "or", "but", "so",
            "to", "for", "of", "in", "on", "at", "by", "with", "from",
            "yes", "no", "ok", "okay", "um", "uh", "hmm", "yeah", "yep",
            "hello", "hi", "hey", "thanks", "thank", "please", "can", "will",
            "just", "like", "know", "think", "going", "gonna", "want",
        }
        substantive_words = [w for w in words if w not in stop_words and len(w) > 2]

        # If very few substantive words, it's minimal content
        if len(substantive_words) < 5:
            return True

        return False

    def generate_quick_summary(self, transcript: str) -> str:
        """
        Generate only a quick summary (faster).

        Args:
            transcript: Meeting transcript

        Returns:
            Summary text
        """
        return self._generate_summary(transcript)
