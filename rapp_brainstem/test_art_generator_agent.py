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


if __name__ == "__main__":
    unittest.main()
