"""
Langfuse Tracer for Observability
"""

import time
from typing import Any

from langfuse import Langfuse

from verxlite_api.config import settings
from verxlite_api.utils.logger import get_logger

logger = get_logger("langfuse")


class LangfuseTracer:
    """
    Wrapper for Langfuse tracing and observability.
    """

    def __init__(self):
        if not settings.LANGFUSE_SECRET_KEY or not settings.LANGFUSE_PUBLIC_KEY:
            logger.warning("Langfuse keys not configured, tracing disabled")
            self.langfuse = None
        else:
            self.langfuse = Langfuse(
                secret_key=settings.LANGFUSE_SECRET_KEY,
                public_key=settings.LANGFUSE_PUBLIC_KEY,
                host=settings.LANGFUSE_HOST,
            )

    def trace_workflow_run(
        self,
        run_id: str,
        workflow_id: str,
        workflow_type: str,
        tenant_id: str,
        user_id: str,
        status: str,
        total_tokens: int = 0,
        total_duration_ms: int = 0,
        error_message: str | None = None,
    ):
        """
        Trace a workflow run.
        """
        if not self.langfuse:
            return

        self.langfuse.trace(
            id=run_id,
            name=f"workflow_{workflow_type}",
            input={
                "workflow_id": workflow_id,
                "workflow_type": workflow_type,
                "tenant_id": tenant_id,
                "user_id": user_id,
            },
            output={
                "status": status,
                "total_tokens": total_tokens,
                "total_duration_ms": total_duration_ms,
                "error_message": error_message,
            },
            metadata={
                "workflow_id": workflow_id,
                "workflow_type": workflow_type,
                "tenant_id": tenant_id,
                "user_id": user_id,
            },
        )

        logger.info(f"Traced workflow run: {run_id}")

    def trace_workflow_step(
        self,
        step_id: str,
        run_id: str,
        step_type: str,
        step_name: str,
        tool_name: str | None = None,
        input_data: dict[str, Any] | None = None,
        output_data: dict[str, Any] | None = None,
        status: str = "completed",
        latency_ms: int = 0,
        tokens_used: int = 0,
        error_message: str | None = None,
    ):
        """
        Trace a workflow step.
        """
        if not self.langfuse:
            return

        # Sanitize input/output (remove PII)
        sanitized_input = self._sanitize_data(input_data)
        sanitized_output = self._sanitize_data(output_data)

        self.langfuse.observation(
            id=step_id,
            trace_id=run_id,
            name=f"{step_type}_{step_name}",
            input=sanitized_input,
            output=sanitized_output,
            metadata={
                "step_type": step_type,
                "step_name": step_name,
                "tool_name": tool_name,
                "status": status,
                "latency_ms": latency_ms,
                "tokens_used": tokens_used,
                "error_message": error_message,
            },
        )

        logger.debug(f"Traced workflow step: {step_id}")

    def _sanitize_data(self, data: dict[str, Any] | None) -> dict[str, Any] | None:
        """
        Sanitize data by removing PII.
        """
        if not data:
            return None

        # Create a copy to avoid modifying the original
        sanitized = data.copy()

        # Remove common PII fields
        pii_fields = [
            "email",
            "email_address",
            "email_addresses",
            "phone",
            "phone_number",
            "address",
            "street",
            "city",
            "state",
            "zip",
            "country",
            "name",
            "first_name",
            "last_name",
            "full_name",
            "access_token",
            "refresh_token",
            "token",
            "password",
            "secret",
            "api_key",
        ]

        for field in pii_fields:
            if field in sanitized:
                sanitized[field] = "[REDACTED]"

            # Also check nested dictionaries
            for key, value in sanitized.items():
                if isinstance(value, dict):
                    if field in value:
                        value[field] = "[REDACTED]"

        return sanitized

    def trace_llm_call(
        self,
        trace_id: str,
        model: str,
        prompt: str,
        response: str,
        tokens_used: int = 0,
        latency_ms: int = 0,
    ):
        """
        Trace an LLM call.
        """
        if not self.langfuse:
            return

        # Sanitize prompt and response
        sanitized_prompt = self._sanitize_prompt(prompt)
        sanitized_response = self._sanitize_prompt(response)

        self.langfuse.generation(
            id=f"llm_{int(time.time() * 1000)}",
            trace_id=trace_id,
            name=model,
            input=sanitized_prompt,
            output=sanitized_response,
            metadata={
                "model": model,
                "tokens_used": tokens_used,
                "latency_ms": latency_ms,
            },
        )

        logger.debug(f"Traced LLM call: {model}")

    def _sanitize_prompt(self, text: str) -> str:
        """
        Sanitize prompt/response text by removing PII.
        """
        import re

        # Remove email addresses
        text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]", text)

        # Remove phone numbers
        text = re.sub(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE]", text)

        # Remove addresses (simplified)
        text = re.sub(
            r"\b\d{1,5}\s[\w\s]{1,20}(?:street|st|avenue|ave|road|rd|highway|hwy|square|sq|trail|trl|drive|dr|court|ct|parkway|pkwy|circle|cir|boulevard|blvd)\b",
            "[ADDRESS]",
            text,
            flags=re.IGNORECASE,
        )

        return text
