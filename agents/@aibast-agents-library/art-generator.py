"""
Art Generator - Create original images with Azure GPT Image models.

Uses Microsoft Entra ID authentication, saves generated PNG files locally,
and can open them in the default browser or submit them to the RAPP Commons
through a reviewable CC0 pull request. Configure an Azure OpenAI endpoint and
the name of a deployed GPT Image model before invoking the agent.
"""

# ===============================================================
# RAPP AGENT MANIFEST - Do not remove. Used by registry builder.
# ===============================================================
__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/art-generator",
    "version": "1.1.0",
    "display_name": "ArtGenerator",
    "description": "Generates original images with Azure GPT Image, saves them locally, and can submit them to the RAPP Commons under CC0.",
    "author": "AIBAST",
    "tags": [
        "art",
        "azure-openai",
        "gpt-image",
        "image-generation",
        "multimodal",
        "rapp-commons",
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
import hashlib
import json
import os
import re
import subprocess
import time
import uuid
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlencode, urlparse

import requests

from agents.basic_agent import BasicAgent


_TOKEN_SCOPE = "https://cognitiveservices.azure.com/.default"
_DEFAULT_API_VERSION = "2025-04-01-preview"
_DEFAULT_COMMONS_REPOSITORY = "kody-w/rapp-commons"
_GITHUB_API_ROOT = "https://api.github.com"
_COMMONS_LICENSE = "CC0-1.0"
_MAX_COMMONS_IMAGE_BYTES = 20 * 1024 * 1024
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_SUPPORTED_SIZES = frozenset({
    "1024x1024",
    "1024x1536",
    "1536x1024",
})
_SUPPORTED_QUALITIES = frozenset({"low", "medium", "high"})
_GITHUB_LOGIN_PATTERN = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$"
)
_GITHUB_REPOSITORY_PATTERN = re.compile(
    r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$"
)


class _GitHubApiError(RuntimeError):
    def __init__(self, status_code, message):
        self.status_code = status_code
        super().__init__(message)


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


def _get_github_token():
    for variable in ("GH_TOKEN", "GITHUB_TOKEN"):
        token = os.getenv(variable, "").strip()
        if token:
            return token

    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(
            "RAPP Commons publishing requires `gh auth login` or GH_TOKEN."
        ) from exc

    token = result.stdout.strip() if result.returncode == 0 else ""
    if not token:
        raise RuntimeError(
            "RAPP Commons publishing requires `gh auth login` or GH_TOKEN."
        )
    return token


def _github_response_message(response):
    try:
        payload = response.json()
    except requests.exceptions.JSONDecodeError:
        return response.text[:500].strip() or response.reason
    if isinstance(payload, dict):
        return str(payload.get("message") or payload)[:500]
    return str(payload)[:500]


def _github_request(
    method,
    path,
    token,
    payload=None,
    expected=(200, 201),
):
    response = requests.request(
        method,
        f"{_GITHUB_API_ROOT}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "rapp-brainstem-art-generator",
        },
        json=payload,
        timeout=30,
    )
    if response.status_code not in expected:
        raise _GitHubApiError(
            response.status_code,
            f"GitHub API failed ({response.status_code}): "
            f"{_github_response_message(response)}",
        )
    if response.status_code == 204 or not response.content:
        return {}
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError as exc:
        raise RuntimeError("GitHub API returned invalid JSON.") from exc


def _commons_slug(title):
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return (slug or "generated-art")[:40].rstrip("-")


def _commons_repository():
    repository = os.getenv(
        "RAPP_COMMONS_REPOSITORY",
        _DEFAULT_COMMONS_REPOSITORY,
    ).strip()
    if not _GITHUB_REPOSITORY_PATTERN.fullmatch(repository):
        raise RuntimeError(
            "RAPP_COMMONS_REPOSITORY must use the owner/repository format."
        )
    return repository


def _target_repository(token, upstream_repository, login, repository_name):
    upstream_owner = upstream_repository.split("/", 1)[0]
    if login.lower() == upstream_owner.lower():
        return upstream_repository

    target_repository = f"{login}/{repository_name}"
    try:
        _github_request("GET", f"/repos/{target_repository}", token)
        return target_repository
    except _GitHubApiError as exc:
        if exc.status_code != 404:
            raise

    _github_request(
        "POST",
        f"/repos/{upstream_repository}/forks",
        token,
        expected=(202,),
    )
    for _ in range(10):
        try:
            _github_request("GET", f"/repos/{target_repository}", token)
            return target_repository
        except _GitHubApiError as exc:
            if exc.status_code != 404:
                raise
            time.sleep(1)
    raise RuntimeError(
        f"GitHub fork {target_repository} was not ready in time."
    )


def _publish_to_commons(
    image_bytes,
    title,
    artist_statement,
    deployment,
    size,
    quality,
):
    if len(image_bytes) > _MAX_COMMONS_IMAGE_BYTES:
        raise RuntimeError(
            "Generated image exceeds the 20 MB RAPP Commons submission limit."
        )

    token = _get_github_token()
    user = _github_request("GET", "/user", token)
    login = str(user.get("login") or "").strip()
    if not _GITHUB_LOGIN_PATTERN.fullmatch(login):
        raise RuntimeError("GitHub did not return a valid authenticated login.")

    upstream_repository = _commons_repository()
    repository_name = upstream_repository.split("/", 1)[1]
    upstream = _github_request(
        "GET",
        f"/repos/{upstream_repository}",
        token,
    )
    base_branch = str(upstream.get("default_branch") or "main")
    cubby_path = f"cubbies/{login}/cubby.json"
    try:
        _github_request(
            "GET",
            f"/repos/{upstream_repository}/contents/"
            f"{quote(cubby_path, safe='/')}?ref={quote(base_branch, safe='')}",
            token,
        )
    except _GitHubApiError as exc:
        if exc.status_code == 404:
            raise RuntimeError(
                f"Claim the {login} cubby in {upstream_repository} before "
                "submitting generated art."
            ) from exc
        raise

    target_repository = _target_repository(
        token,
        upstream_repository,
        login,
        repository_name,
    )
    target = _github_request("GET", f"/repos/{target_repository}", token)
    target_base = str(target.get("default_branch") or base_branch)
    base_ref = _github_request(
        "GET",
        f"/repos/{target_repository}/git/ref/heads/"
        f"{quote(target_base, safe='')}",
        token,
    )
    base_commit_sha = base_ref.get("object", {}).get("sha")
    if not base_commit_sha:
        raise RuntimeError("GitHub did not return the Commons base commit.")
    base_commit = _github_request(
        "GET",
        f"/repos/{target_repository}/git/commits/{base_commit_sha}",
        token,
    )
    base_tree_sha = base_commit.get("tree", {}).get("sha")
    if not base_tree_sha:
        raise RuntimeError("GitHub did not return the Commons base tree.")

    submitted_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    digest = hashlib.sha256(image_bytes).hexdigest()[:8]
    submission_id = uuid.uuid4().hex[:8]
    artifact_slug = (
        f"{submitted_at[:10]}-{_commons_slug(title)}-{digest}-{submission_id}"
    )
    asset_path = f"cubbies/{login}/show-and-tell/{artifact_slug}.png"
    metadata_path = f"cubbies/{login}/show-and-tell/{artifact_slug}.md"
    statement = artist_statement.strip() or (
        "An original AI-assisted image shared with the RAPP Commons."
    )
    asset_name = asset_path.rsplit("/", 1)[1]
    metadata = (
        "---\n"
        "schema: rapp-commons-art/1.0\n"
        f"title: {json.dumps(title, ensure_ascii=False)}\n"
        f"contributor: {json.dumps(login)}\n"
        f"submitted_at: {json.dumps(submitted_at)}\n"
        f"license: {_COMMONS_LICENSE}\n"
        f"generator: {json.dumps(f'Azure GPT Image ({deployment})')}\n"
        f"size: {json.dumps(size)}\n"
        f"quality: {json.dumps(quality)}\n"
        f"asset: {json.dumps(asset_name)}\n"
        "---\n\n"
        f"# {title}\n\n"
        f"{statement}\n\n"
        f"![{title}](./{asset_name})\n\n"
        "This piece is dedicated to the public domain under CC0-1.0.\n"
    ).encode("utf-8")

    image_blob = _github_request(
        "POST",
        f"/repos/{target_repository}/git/blobs",
        token,
        {
            "content": base64.b64encode(image_bytes).decode("ascii"),
            "encoding": "base64",
        },
    )
    metadata_blob = _github_request(
        "POST",
        f"/repos/{target_repository}/git/blobs",
        token,
        {
            "content": base64.b64encode(metadata).decode("ascii"),
            "encoding": "base64",
        },
    )
    tree = _github_request(
        "POST",
        f"/repos/{target_repository}/git/trees",
        token,
        {
            "base_tree": base_tree_sha,
            "tree": [
                {
                    "path": asset_path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": image_blob["sha"],
                },
                {
                    "path": metadata_path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": metadata_blob["sha"],
                },
            ],
        },
    )
    commit = _github_request(
        "POST",
        f"/repos/{target_repository}/git/commits",
        token,
        {
            "message": f"art: submit {title}",
            "tree": tree["sha"],
            "parents": [base_commit_sha],
        },
    )
    branch = f"art/{_commons_slug(title)}-{submission_id}"
    _github_request(
        "POST",
        f"/repos/{target_repository}/git/refs",
        token,
        {
            "ref": f"refs/heads/{branch}",
            "sha": commit["sha"],
        },
    )
    head = (
        branch
        if target_repository == upstream_repository
        else f"{login}:{branch}"
    )
    pull_request = _github_request(
        "POST",
        f"/repos/{upstream_repository}/pulls",
        token,
        {
            "title": f"Art: {title}",
            "head": head,
            "base": base_branch,
            "body": (
                "## Generated art submission\n\n"
                f"- Contributor: @{login}\n"
                f"- License: `{_COMMONS_LICENSE}`\n"
                f"- Image: `{asset_path}`\n"
                f"- Statement: {statement}\n\n"
                "Created by the RAPP Brainstem ArtGenerator agent."
            ),
        },
    )
    return {
        "status": "pr_opened",
        "repository": upstream_repository,
        "branch": branch,
        "pull_request_number": pull_request.get("number"),
        "pull_request_url": pull_request.get("html_url"),
        "asset_path": asset_path,
        "metadata_path": metadata_path,
        "license": _COMMONS_LICENSE,
        "artifact_url_after_merge": (
            f"https://raw.githubusercontent.com/{upstream_repository}/"
            f"{base_branch}/{asset_path}"
        ),
    }


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
                    "publish_to_commons": {
                        "type": "boolean",
                        "default": False,
                        "description": (
                            "Open a public RAPP Commons pull request containing "
                            "the generated PNG. Requires commons_title and "
                            "cc0_confirmed=true."
                        ),
                    },
                    "commons_title": {
                        "type": "string",
                        "maxLength": 120,
                        "description": (
                            "Public title for the piece. Required when "
                            "publish_to_commons is true."
                        ),
                    },
                    "commons_description": {
                        "type": "string",
                        "maxLength": 2000,
                        "description": "Optional public artist statement.",
                    },
                    "cc0_confirmed": {
                        "type": "boolean",
                        "default": False,
                        "description": (
                            "Confirm the user owns the generated piece and "
                            "dedicates it to the public domain under CC0-1.0."
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
        publish_to_commons=False,
        commons_title="",
        commons_description="",
        cc0_confirmed=False,
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
            if not isinstance(publish_to_commons, bool):
                raise ValueError("publish_to_commons must be a boolean.")
            if not isinstance(cc0_confirmed, bool):
                raise ValueError("cc0_confirmed must be a boolean.")
            if publish_to_commons:
                if not cc0_confirmed:
                    raise ValueError(
                        "CC0 confirmation is required before publishing publicly."
                    )
                if (
                    not isinstance(commons_title, str)
                    or not commons_title.strip()
                ):
                    raise ValueError(
                        "commons_title is required when publish_to_commons is true."
                    )
                if "\n" in commons_title or "\r" in commons_title:
                    raise ValueError("commons_title must be a single line.")
                if len(commons_title.strip()) > 120:
                    raise ValueError(
                        "commons_title must be 120 characters or fewer."
                    )
                if not isinstance(commons_description, str):
                    raise ValueError("commons_description must be a string.")
                if len(commons_description.strip()) > 2000:
                    raise ValueError(
                        "commons_description must be 2000 characters or fewer."
                    )

            image_bytes, deployment = _request_image(
                prompt,
                size,
                quality,
            )
            image_path = _save_image(image_bytes)
            commons_submission = None
            if publish_to_commons:
                try:
                    commons_submission = _publish_to_commons(
                        image_bytes=image_bytes,
                        title=commons_title.strip(),
                        artist_statement=commons_description.strip(),
                        deployment=deployment,
                        size=size,
                        quality=quality,
                    )
                except (
                    OSError,
                    RuntimeError,
                    ValueError,
                    requests.exceptions.RequestException,
                ) as exc:
                    commons_submission = {
                        "status": "error",
                        "message": str(exc),
                        "license": _COMMONS_LICENSE,
                    }
            browser_opened = (
                webbrowser.open_new_tab(image_path.as_uri())
                if open_in_browser
                else False
            )

            result = {
                "status": "saved",
                "file_path": str(image_path),
                "deployment": deployment,
                "browser_opened": browser_opened,
                "message": "Generated art was saved locally.",
            }
            if commons_submission is not None:
                result["commons_submission"] = commons_submission
                if commons_submission["status"] == "pr_opened":
                    result["message"] = (
                        "Generated art was saved locally and submitted to the "
                        "RAPP Commons for review."
                    )
                else:
                    result["message"] = (
                        "Generated art was saved locally, but the RAPP Commons "
                        "submission failed."
                    )
            return json.dumps(result)
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
