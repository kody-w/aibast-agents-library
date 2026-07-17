"""
Art Generator - Create original images with Azure GPT Image models.

Uses Microsoft Entra ID authentication, saves generated PNG files locally,
and can open them in the default browser. Configure an Azure OpenAI endpoint
and the name of a deployed GPT Image model before invoking the agent.
"""

# ===============================================================
# RAPP AGENT MANIFEST - Do not remove. Used by registry builder.
# ===============================================================
__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/art-generator",
    "version": "1.0.0",
    "display_name": "ArtGenerator",
    "description": "Generates original images with an Azure GPT Image deployment and saves them locally.",
    "author": "AIBAST",
    "tags": [
        "art",
        "azure-openai",
        "gpt-image",
        "image-generation",
        "multimodal",
    ],
    "category": "general",
    "quality_tier": "community",
    "requires_env": [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_IMAGE_DEPLOYMENT",
    ],
    "dependencies": ["@rapp/basic-agent"],
}
# ===============================================================

import base64
import json
import os
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlencode, urlparse

import requests

from agents.basic_agent import BasicAgent


_TOKEN_SCOPE = "https://cognitiveservices.azure.com/.default"
_DEFAULT_API_VERSION = "2025-04-01-preview"
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_SUPPORTED_SIZES = frozenset({
    "1024x1024",
    "1024x1536",
    "1536x1024",
})
_SUPPORTED_QUALITIES = frozenset({"low", "medium", "high"})


def _art_directory():
    configured = os.getenv("RAPP_ART_OUTPUT_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (
        Path(__file__).resolve().parents[1]
        / ".brainstem_data"
        / "art"
    )


def _get_access_token():
    try:
        from azure.core.exceptions import ClientAuthenticationError
        from azure.identity import (
            AzureCliCredential,
            CredentialUnavailableError,
            ManagedIdentityCredential,
        )
    except ImportError as exc:
        raise RuntimeError(
            "Azure authentication requires the azure-identity package."
        ) from exc

    managed_identity_available = any(
        os.getenv(name)
        for name in ("WEBSITE_INSTANCE_ID", "IDENTITY_ENDPOINT", "MSI_ENDPOINT")
    )
    credential = (
        ManagedIdentityCredential()
        if managed_identity_available
        else AzureCliCredential()
    )
    try:
        return credential.get_token(_TOKEN_SCOPE).token
    except (ClientAuthenticationError, CredentialUnavailableError) as exc:
        raise RuntimeError(
            "Azure authentication failed. Run `az login` locally or configure "
            "a managed identity with Cognitive Services OpenAI User access."
        ) from exc


def _get_api_config():
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip().rstrip("/")
    if not endpoint:
        raise RuntimeError(
            "Set AZURE_OPENAI_ENDPOINT before using ArtGenerator."
        )

    parsed = urlparse(endpoint)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError(
            "AZURE_OPENAI_ENDPOINT must be a valid HTTPS endpoint."
        )

    deployment = os.getenv(
        "AZURE_OPENAI_IMAGE_DEPLOYMENT",
        "",
    ).strip()
    if not deployment:
        raise RuntimeError(
            "Set AZURE_OPENAI_IMAGE_DEPLOYMENT to a deployed GPT Image model."
        )

    api_version = (
        os.getenv("AZURE_OPENAI_IMAGE_API_VERSION")
        or os.getenv("AZURE_OPENAI_API_VERSION")
        or _DEFAULT_API_VERSION
    ).strip()
    if not api_version:
        raise RuntimeError(
            "AZURE_OPENAI_IMAGE_API_VERSION cannot be empty."
        )

    return endpoint, deployment, api_version


def _azure_error_message(response):
    try:
        payload = response.json()
    except requests.exceptions.JSONDecodeError:
        return response.text[:500].strip() or response.reason

    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict):
        return str(error.get("message") or error.get("code") or error)
    return str(error or payload)[:500]


def _request_image(prompt, size, quality):
    endpoint, deployment, api_version = _get_api_config()
    url = (
        f"{endpoint}/openai/deployments/{quote(deployment, safe='')}"
        f"/images/generations?{urlencode({'api-version': api_version})}"
    )
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {_get_access_token()}",
            "Content-Type": "application/json",
        },
        json={
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": quality,
            "output_format": "png",
        },
        timeout=180,
    )

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(
            f"Azure image generation failed ({response.status_code}): "
            f"{_azure_error_message(response)}"
        ) from exc

    try:
        payload = response.json()
    except requests.exceptions.JSONDecodeError as exc:
        raise RuntimeError(
            "Azure image generation returned invalid JSON."
        ) from exc

    data = payload.get("data") if isinstance(payload, dict) else None
    encoded_image = (
        data[0].get("b64_json")
        if isinstance(data, list)
        and data
        and isinstance(data[0], dict)
        else None
    )
    if not encoded_image:
        raise RuntimeError(
            "Azure image generation returned no image data."
        )

    try:
        image_bytes = base64.b64decode(encoded_image, validate=True)
    except (ValueError, TypeError) as exc:
        raise RuntimeError(
            "Azure image generation returned invalid base64 image data."
        ) from exc
    if not image_bytes.startswith(_PNG_SIGNATURE):
        raise RuntimeError(
            "Azure image generation returned an unexpected image format."
        )

    return image_bytes, deployment


def _save_image(image_bytes):
    art_dir = _art_directory()
    art_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    image_path = art_dir / f"generated_art_{timestamp}.png"
    temp_path = image_path.with_name(
        f".{image_path.name}.{os.getpid()}.tmp"
    )

    try:
        with temp_path.open("wb") as output:
            output.write(image_bytes)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temp_path, image_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    return image_path


class ArtGeneratorAgent(BasicAgent):
    def __init__(self):
        self.name = __manifest__["display_name"]
        self.metadata = {
            "name": self.name,
            "description": (
                f"{__manifest__['description']} Use this tool when the user "
                "asks to create, draw, illustrate, or generate an image. A "
                "message beginning with 'art:' is an explicit trigger."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "maxLength": 4000,
                        "description": (
                            "A detailed text prompt describing the original "
                            "image to generate."
                        ),
                    },
                    "size": {
                        "type": "string",
                        "enum": sorted(_SUPPORTED_SIZES),
                        "default": "1024x1024",
                        "description": "Dimensions of the generated image.",
                    },
                    "quality": {
                        "type": "string",
                        "enum": sorted(_SUPPORTED_QUALITIES),
                        "default": "medium",
                        "description": "Generation quality and cost level.",
                    },
                    "open_in_browser": {
                        "type": "boolean",
                        "default": True,
                        "description": (
                            "Open the saved image in the local default browser."
                        ),
                    },
                },
                "required": ["description"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(
        self,
        description="",
        size="1024x1024",
        quality="medium",
        open_in_browser=True,
        **kwargs,
    ):
        try:
            if not isinstance(description, str) or not description.strip():
                raise ValueError("A non-empty art description is required.")
            prompt = description.strip()
            if len(prompt) > 4000:
                raise ValueError(
                    "The art description must be 4000 characters or fewer."
                )
            if size not in _SUPPORTED_SIZES:
                raise ValueError(f"Unsupported image size: {size}")
            if quality not in _SUPPORTED_QUALITIES:
                raise ValueError(f"Unsupported image quality: {quality}")
            if not isinstance(open_in_browser, bool):
                raise ValueError("open_in_browser must be a boolean.")

            image_bytes, deployment = _request_image(
                prompt,
                size,
                quality,
            )
            image_path = _save_image(image_bytes)
            browser_opened = (
                webbrowser.open_new_tab(image_path.as_uri())
                if open_in_browser
                else False
            )

            return json.dumps({
                "status": "saved",
                "file_path": str(image_path),
                "deployment": deployment,
                "browser_opened": browser_opened,
                "message": "Generated art was saved locally.",
            })
        except (
            OSError,
            RuntimeError,
            ValueError,
            requests.exceptions.RequestException,
            webbrowser.Error,
        ) as exc:
            return json.dumps({
                "status": "error",
                "message": str(exc),
            })
