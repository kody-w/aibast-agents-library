#!/usr/bin/env python3
"""Tests for the Azure-backed local art generator agent."""

import base64
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests


BRAINSTEM_DIR = os.path.dirname(os.path.abspath(__file__))
if BRAINSTEM_DIR not in sys.path:
    sys.path.insert(0, BRAINSTEM_DIR)

import agents.art_generator_agent as art_module  # noqa: E402
from agents.art_generator_agent import ArtGeneratorAgent  # noqa: E402


_ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0l"
    "EQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


class TestArtGeneratorAgent(unittest.TestCase):
    def setUp(self):
        self.agent = ArtGeneratorAgent()

    def test_preserves_original_function_call_name_and_updates_model(self):
        tool = self.agent.to_tool()["function"]

        self.assertEqual(tool["name"], "ArtGenerator")
        self.assertEqual(
            tool["parameters"]["required"],
            ["description"],
        )
        self.assertEqual(art_module._DEFAULT_DEPLOYMENT, "gpt-image-2")
        self.assertIn("art:", tool["description"])
        self.assertIn(
            "publish_to_commons",
            tool["parameters"]["properties"],
        )

    def test_requires_azure_endpoint(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                RuntimeError,
                "Set AZURE_OPENAI_ENDPOINT",
            ):
                art_module._get_api_config()

    def test_rejects_invalid_prompt_before_calling_azure(self):
        with patch.object(art_module, "_request_image") as request_image:
            with self.assertRaisesRegex(
                ValueError,
                "non-empty art description",
            ):
                self.agent.perform(description="   ")

        request_image.assert_not_called()

    def test_requires_cc0_confirmation_before_commons_submission(self):
        with patch.object(art_module, "_request_image") as request_image:
            with self.assertRaisesRegex(
                ValueError,
                "CC0",
            ):
                self.agent.perform(
                    description="An original geometric landscape",
                    publish_to_commons=True,
                    commons_title="Geometric Landscape",
                )

        request_image.assert_not_called()

    def test_rejects_multiline_commons_title_before_generation(self):
        with patch.object(art_module, "_request_image") as request_image:
            with self.assertRaisesRegex(ValueError, "single line"):
                self.agent.perform(
                    description="An original geometric landscape",
                    publish_to_commons=True,
                    commons_title="Landscape\nlicense: MIT",
                    cc0_confirmed=True,
                )

        request_image.assert_not_called()

    def test_commons_submission_creates_cc0_cubby_pull_request(self):
        calls = []

        def github_request(
            method,
            path,
            token,
            payload=None,
            expected=(200, 201),
        ):
            calls.append((method, path, payload, expected))
            self.assertEqual(token, "github-token")
            if method == "GET" and path == "/user":
                return {"login": "kody-w"}
            if method == "GET" and path == "/repos/kody-w/rapp-commons":
                return {"default_branch": "main"}
            if method == "GET" and "/contents/cubbies/kody-w/" in path:
                return {"path": "cubbies/kody-w/cubby.json"}
            if method == "GET" and "/git/ref/heads/main" in path:
                return {"object": {"sha": "base-commit"}}
            if method == "GET" and path.endswith("/git/commits/base-commit"):
                return {"tree": {"sha": "base-tree"}}
            if method == "POST" and path.endswith("/git/blobs"):
                content = base64.b64decode(payload["content"])
                return {
                    "sha": (
                        "image-blob"
                        if content.startswith(art_module._PNG_SIGNATURE)
                        else "metadata-blob"
                    )
                }
            if method == "POST" and path.endswith("/git/trees"):
                return {"sha": "new-tree"}
            if method == "POST" and path.endswith("/git/commits"):
                return {"sha": "new-commit"}
            if method == "POST" and path.endswith("/git/refs"):
                return {"ref": payload["ref"]}
            if method == "POST" and path.endswith("/pulls"):
                return {
                    "number": 42,
                    "html_url": (
                        "https://github.com/kody-w/rapp-commons/pull/42"
                    ),
                }
            self.fail(f"Unexpected GitHub request: {method} {path}")

        with (
            patch.object(
                art_module,
                "_get_github_token",
                return_value="github-token",
            ),
            patch.object(
                art_module,
                "_github_request",
                side_effect=github_request,
            ),
        ):
            result = art_module._publish_to_commons(
                image_bytes=_ONE_PIXEL_PNG,
                title="Geometric Landscape",
                artist_statement="A study in balance and negative space.",
                deployment="gpt-image-2",
                size="1024x1024",
                quality="low",
            )

        tree_payload = next(
            payload
            for method, path, payload, _ in calls
            if method == "POST" and path.endswith("/git/trees")
        )
        tree_paths = [entry["path"] for entry in tree_payload["tree"]]
        self.assertEqual(len(tree_paths), 2)
        self.assertTrue(all(
            path.startswith("cubbies/kody-w/show-and-tell/")
            for path in tree_paths
        ))
        self.assertTrue(any(path.endswith(".png") for path in tree_paths))
        self.assertTrue(any(path.endswith(".md") for path in tree_paths))

        metadata_payload = next(
            payload
            for method, path, payload, _ in calls
            if method == "POST"
            and path.endswith("/git/blobs")
            and not base64.b64decode(payload["content"]).startswith(
                art_module._PNG_SIGNATURE
            )
        )
        metadata = base64.b64decode(
            metadata_payload["content"]
        ).decode("utf-8")
        self.assertIn("CC0-1.0", metadata)
        self.assertIn("Geometric Landscape", metadata)
        self.assertIn("A study in balance", metadata)

        pull_payload = next(
            payload
            for method, path, payload, _ in calls
            if method == "POST" and path.endswith("/pulls")
        )
        self.assertEqual(pull_payload["base"], "main")
        self.assertTrue(pull_payload["head"].startswith("art/"))
        self.assertIn("CC0-1.0", pull_payload["body"])
        self.assertEqual(result["status"], "pr_opened")
        self.assertEqual(result["pull_request_number"], 42)
        self.assertEqual(result["license"], "CC0-1.0")

    def test_generated_image_is_retained_when_commons_pr_opens(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "generated.png"
            image_path.write_bytes(_ONE_PIXEL_PNG)
            with (
                patch.object(
                    art_module,
                    "_request_image",
                    return_value=(_ONE_PIXEL_PNG, "gpt-image-2"),
                ),
                patch.object(
                    art_module,
                    "_save_image",
                    return_value=image_path,
                ),
                patch.object(
                    art_module,
                    "_publish_to_commons",
                    return_value={
                        "status": "pr_opened",
                        "pull_request_url": (
                            "https://github.com/kody-w/rapp-commons/pull/42"
                        ),
                        "license": "CC0-1.0",
                    },
                ) as publish,
            ):
                result = json.loads(self.agent.perform(
                    description="An original geometric landscape",
                    quality="low",
                    open_in_browser=False,
                    publish_to_commons=True,
                    commons_title="Geometric Landscape",
                    commons_description="A study in balance.",
                    cc0_confirmed=True,
                ))

            self.assertTrue(image_path.is_file())

        self.assertEqual(result["status"], "saved")
        self.assertEqual(
            result["commons_submission"]["status"],
            "pr_opened",
        )
        publish.assert_called_once_with(
            image_bytes=_ONE_PIXEL_PNG,
            title="Geometric Landscape",
            artist_statement="A study in balance.",
            deployment="gpt-image-2",
            size="1024x1024",
            quality="low",
        )

    def test_generated_image_is_retained_when_commons_pr_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "generated.png"
            image_path.write_bytes(_ONE_PIXEL_PNG)
            with (
                patch.object(
                    art_module,
                    "_request_image",
                    return_value=(_ONE_PIXEL_PNG, "gpt-image-2"),
                ),
                patch.object(
                    art_module,
                    "_save_image",
                    return_value=image_path,
                ),
                patch.object(
                    art_module,
                    "_publish_to_commons",
                    side_effect=RuntimeError("GitHub unavailable"),
                ),
            ):
                result = json.loads(self.agent.perform(
                    description="An original geometric landscape",
                    open_in_browser=False,
                    publish_to_commons=True,
                    commons_title="Geometric Landscape",
                    cc0_confirmed=True,
                ))

            self.assertTrue(image_path.is_file())

        self.assertEqual(result["status"], "saved")
        self.assertEqual(
            result["commons_submission"]["status"],
            "error",
        )
        self.assertIn(
            "GitHub unavailable",
            result["commons_submission"]["message"],
        )

    def test_generates_saves_and_opens_png(self):
        response = MagicMock()
        response.json.return_value = {
            "data": [{
                "b64_json": base64.b64encode(_ONE_PIXEL_PNG).decode("ascii"),
            }],
        }

        env = {
            "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com",
            "AZURE_OPENAI_IMAGE_DEPLOYMENT": "gpt-image-2",
            "AZURE_OPENAI_IMAGE_API_VERSION": "2025-04-01-preview",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch.dict(os.environ, env, clear=False),
                patch.object(
                    art_module,
                    "_ART_DIR",
                    Path(temp_dir),
                ),
                patch.object(
                    art_module,
                    "_get_access_token",
                    return_value="test-token",
                ),
                patch.object(
                    art_module.requests,
                    "post",
                    return_value=response,
                ) as post,
                patch.object(
                    art_module.webbrowser,
                    "open_new_tab",
                    return_value=True,
                ) as open_new_tab,
            ):
                result = json.loads(self.agent.perform(
                    description="A watercolor fox reading under a tree",
                    quality="high",
                ))

            saved_path = Path(result["file_path"])
            self.assertEqual(saved_path.read_bytes(), _ONE_PIXEL_PNG)
            open_new_tab.assert_called_once_with(saved_path.as_uri())

        request = post.call_args
        self.assertIn(
            "/deployments/gpt-image-2/images/generations",
            request.args[0],
        )
        self.assertEqual(
            request.kwargs["headers"]["Authorization"],
            "Bearer test-token",
        )
        self.assertEqual(request.kwargs["json"]["quality"], "high")
        self.assertEqual(result["status"], "saved")
        self.assertTrue(result["browser_opened"])

    def test_surfaces_azure_service_error(self):
        response = MagicMock()
        response.status_code = 400
        response.json.return_value = {
            "error": {
                "code": "content_policy_violation",
                "message": "The prompt was rejected.",
            },
        }
        response.raise_for_status.side_effect = requests.HTTPError(
            response=response
        )

        with (
            patch.dict(
                os.environ,
                {
                    "AZURE_OPENAI_ENDPOINT": (
                        "https://example.openai.azure.com"
                    ),
                },
                clear=False,
            ),
            patch.object(
                art_module,
                "_get_access_token",
                return_value="test-token",
            ),
            patch.object(
                art_module.requests,
                "post",
                return_value=response,
            ),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "The prompt was rejected",
            ):
                self.agent.perform(description="test prompt")

    def test_brainstem_loader_discovers_agent_file(self):
        import brainstem

        filepath = os.path.join(
            BRAINSTEM_DIR,
            "agents",
            "art_generator_agent.py",
        )
        agents = brainstem._load_agent_from_file(filepath)

        self.assertIn("ArtGenerator", agents)

    def test_public_registry_agent_loads_and_handles_missing_config(self):
        import brainstem

        filepath = os.path.abspath(os.path.join(
            BRAINSTEM_DIR,
            "..",
            "agents",
            "@aibast-agents-library",
            "art-generator.py",
        ))
        agents = brainstem._load_agent_from_file(filepath)

        self.assertIn("ArtGenerator", agents)
        with patch.dict(os.environ, {}, clear=True):
            result = json.loads(
                agents["ArtGenerator"].perform(
                    description="A geometric landscape",
                    open_in_browser=False,
                )
            )
        self.assertEqual(result["status"], "error")
        self.assertIn("AZURE_OPENAI_ENDPOINT", result["message"])

    def test_public_registry_agent_returns_saved_image_result(self):
        import brainstem

        filepath = os.path.abspath(os.path.join(
            BRAINSTEM_DIR,
            "..",
            "agents",
            "@aibast-agents-library",
            "art-generator.py",
        ))
        agent = brainstem._load_agent_from_file(filepath)["ArtGenerator"]
        agent_globals = agent.perform.__globals__

        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "generated.png"
            image_path.write_bytes(_ONE_PIXEL_PNG)
            request_image = MagicMock(
                return_value=(_ONE_PIXEL_PNG, "gpt-image-2")
            )
            save_image = MagicMock(return_value=image_path)
            with (
                patch.dict(
                    agent_globals,
                    {
                        "_request_image": request_image,
                        "_save_image": save_image,
                    },
                ),
                patch.object(
                    agent_globals["webbrowser"],
                    "open_new_tab",
                    return_value=True,
                ),
            ):
                raw_result = agent.perform(
                    description="A luminous abstract brainstem",
                )

        self.assertIsInstance(raw_result, str)
        result = json.loads(raw_result)
        self.assertEqual(result["status"], "saved")
        self.assertEqual(result["deployment"], "gpt-image-2")
        self.assertTrue(result["browser_opened"])
        request_image.assert_called_once_with(
            "A luminous abstract brainstem",
            "1024x1024",
            "medium",
        )

    def test_public_registry_agent_returns_commons_pr(self):
        import brainstem

        filepath = os.path.abspath(os.path.join(
            BRAINSTEM_DIR,
            "..",
            "agents",
            "@aibast-agents-library",
            "art-generator.py",
        ))
        agent = brainstem._load_agent_from_file(filepath)["ArtGenerator"]
        agent_globals = agent.perform.__globals__

        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "generated.png"
            image_path.write_bytes(_ONE_PIXEL_PNG)
            publish = MagicMock(return_value={
                "status": "pr_opened",
                "pull_request_url": (
                    "https://github.com/kody-w/rapp-commons/pull/42"
                ),
                "license": "CC0-1.0",
            })
            with patch.dict(
                agent_globals,
                {
                    "_request_image": MagicMock(
                        return_value=(_ONE_PIXEL_PNG, "gpt-image-2")
                    ),
                    "_save_image": MagicMock(return_value=image_path),
                    "_publish_to_commons": publish,
                },
            ):
                result = json.loads(agent.perform(
                    description="A luminous abstract brainstem",
                    quality="low",
                    open_in_browser=False,
                    publish_to_commons=True,
                    commons_title="Luminous Brainstem",
                    commons_description="A study of local intelligence.",
                    cc0_confirmed=True,
                ))

        self.assertEqual(
            result["commons_submission"]["status"],
            "pr_opened",
        )
        publish.assert_called_once_with(
            image_bytes=_ONE_PIXEL_PNG,
            title="Luminous Brainstem",
            artist_statement="A study of local intelligence.",
            deployment="gpt-image-2",
            size="1024x1024",
            quality="low",
        )


if __name__ == "__main__":
    unittest.main()
