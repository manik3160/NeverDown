"""Reasoner agent - LLM-powered root cause analysis for NeverDown."""

from dataclasses import dataclass
from typing import Any, Dict, Optional
from uuid import UUID
import httpx

from agents.base_agent import AgentResult, BaseAgent
from agents.agent_2_reasoner.patch_generator import PatchGenerator
from agents.agent_2_reasoner.prompt_builder import PromptBuilder
from config.logging_config import get_logger
from config.settings import get_settings
from core.exceptions import InvalidPatchError, LLMError, LowConfidenceError
from models.analysis import DetectiveReport
from models.patch import FileChange, Patch, ReasonerOutput

logger = get_logger(__name__)


@dataclass
class ReasonerInput:
    """Input for the Reasoner agent."""
    incident_id: UUID
    sanitized_repo_path: str
    detective_report: DetectiveReport


@dataclass
class ReasonerOutputData:
    """Output from the Reasoner agent."""
    output: ReasonerOutput


class ReasonerAgent(BaseAgent[ReasonerInput, ReasonerOutputData]):
    """Agent 2: LLM-powered root cause analyst.
    
    Responsibilities:
    - Build LLM prompt from Detective's report and sanitized code
    - Call LLM API for root cause analysis
    - Parse and validate generated patch
    - Ensure confidence threshold is met
    
    CRITICAL: This agent receives ONLY sanitized code. It never
    sees real secrets.
    """
    
    name = "reasoner"
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
    
    async def execute(
        self,
        input_data: ReasonerInput,
        incident_id: Optional[UUID] = None,
    ) -> AgentResult[ReasonerOutputData]:
        """Generate root cause analysis and patch using LLM.
        
        Args:
            input_data: Reasoner input with detective report
            incident_id: Incident ID for logging
            
        Returns:
            AgentResult with patch and analysis
        """
        incident_id = incident_id or input_data.incident_id
        
        # Build prompt
        prompt_builder = PromptBuilder(input_data.sanitized_repo_path)
        analysis_prompt = prompt_builder.build_analysis_prompt(input_data.detective_report)
        system_prompt = prompt_builder.get_system_prompt()
        
        # Initialize patch generator
        patch_generator = PatchGenerator(input_data.sanitized_repo_path)
        
        # Attempt LLM call with retries
        max_retries = self.settings.MAX_RETRIES
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Call LLM
                response = await self._call_llm(system_prompt, analysis_prompt)
                
                # Parse response
                parsed = patch_generator.parse_llm_response(response["content"])
                
                if parsed.parse_errors:
                    self.logger.warning(
                        "LLM response parse errors",
                        errors=parsed.parse_errors,
                        attempt=attempt + 1,
                    )
                    # Retry with feedback
                    analysis_prompt = prompt_builder.build_retry_prompt(
                        analysis_prompt,
                        response["content"],
                        f"Parse errors: {', '.join(parsed.parse_errors)}",
                    )
                    continue
                
                # Validate diff
                if not parsed.diff:
                    analysis_prompt = prompt_builder.build_retry_prompt(
                        analysis_prompt,
                        response["content"],
                        "No diff/patch provided in response",
                    )
                    continue
                
                patch_result = patch_generator.validate_diff(parsed.diff)
                
                if not patch_result.is_valid:
                    self.logger.warning(
                        "Invalid patch generated",
                        errors=patch_result.validation_errors,
                        attempt=attempt + 1,
                    )
                    analysis_prompt = prompt_builder.build_retry_prompt(
                        analysis_prompt,
                        response["content"],
                        f"Invalid diff: {', '.join(patch_result.validation_errors)}",
                    )
                    continue
                
                # Check confidence threshold
                confidence_threshold = self.settings.REASONER_CONFIDENCE_THRESHOLD
                if parsed.confidence < confidence_threshold:
                    self.logger.warning(
                        "Low confidence fix",
                        confidence=parsed.confidence,
                        threshold=confidence_threshold,
                    )
                    # Don't retry for low confidence - it's a valid response
                    return AgentResult.fail(
                        f"Confidence {parsed.confidence:.2f} below threshold {confidence_threshold:.2f}",
                        metadata={
                            "confidence": parsed.confidence,
                            "threshold": confidence_threshold,
                            "root_cause": parsed.root_cause_summary,
                        },
                    )
                
                # Success! Build output
                normalized_diff = patch_generator.normalize_diff(parsed.diff)
                
                patch = Patch(
                    incident_id=incident_id,
                    diff=normalized_diff,
                    reasoning=parsed.explanation,
                    confidence=parsed.confidence,
                    assumptions=parsed.assumptions,
                    files_changed=patch_result.files,
                    token_usage=response.get("usage"),
                )
                
                output = ReasonerOutput(
                    incident_id=incident_id,
                    patch=patch,
                    root_cause_summary=parsed.root_cause_summary,
                    detailed_explanation=parsed.explanation,
                    confidence=parsed.confidence,
                    assumptions=parsed.assumptions,
                    risk_assessment=parsed.risks,
                    token_usage=response.get("usage", {}),
                    llm_model=self.settings.LLM_MODEL,
                )
                
                return AgentResult.ok(
                    ReasonerOutputData(output=output),
                    metadata={
                        "confidence": parsed.confidence,
                        "files_changed": len(patch_result.files),
                        "token_usage": response.get("usage"),
                    },
                )
            
            except LLMError as e:
                last_error = e
                self.logger.error(
                    "LLM call failed",
                    error=str(e),
                    attempt=attempt + 1,
                )
                continue
            
            except Exception as e:
                last_error = e
                self.logger.exception("Unexpected error in Reasoner", error=str(e))
                continue
        
        return AgentResult.fail(
            f"Failed after {max_retries} attempts: {str(last_error)}",
            metadata={"attempts": max_retries},
        )
    
    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> Dict[str, Any]:
        """Call the configured LLM API.
        
        Args:
            system_prompt: System instructions
            user_prompt: User message with analysis context
            
        Returns:
            Dict with 'content' and 'usage' keys
            
        Raises:
            LLMError: If API call fails
        """
        provider = self.settings.LLM_PROVIDER.lower()
        
        if not self.settings.LLM_API_KEY:
            raise LLMError("LLM API key not configured", provider)
        
        api_key = self.settings.LLM_API_KEY.get_secret_value()
        
        if provider == "anthropic":
            return await self._call_anthropic(api_key, system_prompt, user_prompt)
        elif provider == "openai":
            return await self._call_openai(api_key, system_prompt, user_prompt)
        else:
            raise LLMError(f"Unsupported LLM provider: {provider}", provider)
    
    async def _call_anthropic(
        self,
        api_key: str,
        system_prompt: str,
        user_prompt: str,
    ) -> Dict[str, Any]:
        """Call Anthropic Claude API."""
        url = "https://api.anthropic.com/v1/messages"
        
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        
        payload = {
            "model": self.settings.LLM_MODEL,
            "max_tokens": self.settings.LLM_MAX_TOKENS,
            "temperature": self.settings.LLM_TEMPERATURE,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt},
            ],
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                
                content = ""
                if data.get("content"):
                    for block in data["content"]:
                        if block.get("type") == "text":
                            content += block.get("text", "")
                
                return {
                    "content": content,
                    "usage": {
                        "input_tokens": data.get("usage", {}).get("input_tokens", 0),
                        "output_tokens": data.get("usage", {}).get("output_tokens", 0),
                    },
                }
            
            except httpx.HTTPStatusError as e:
                raise LLMError(f"Anthropic API error: {e.response.text}", "anthropic")
            except Exception as e:
                raise LLMError(f"Anthropic API call failed: {str(e)}", "anthropic")
    
    async def _call_openai(
        self,
        api_key: str,
        system_prompt: str,
        user_prompt: str,
    ) -> Dict[str, Any]:
        """Call OpenAI API."""
        url = "https://api.openai.com/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.settings.LLM_MODEL,
            "max_tokens": self.settings.LLM_MAX_TOKENS,
            "temperature": self.settings.LLM_TEMPERATURE,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                return {
                    "content": content,
                    "usage": {
                        "input_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                        "output_tokens": data.get("usage", {}).get("completion_tokens", 0),
                    },
                }
            
            except httpx.HTTPStatusError as e:
                raise LLMError(f"OpenAI API error: {e.response.text}", "openai")
            except Exception as e:
                raise LLMError(f"OpenAI API call failed: {str(e)}", "openai")
