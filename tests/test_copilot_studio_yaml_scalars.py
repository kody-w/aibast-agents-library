import importlib.util
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "beta/resources/copilot-studio/rar_kody_w_copilot_studio_parity_deploy_agent.py"


def test_pac_yaml_scalars_are_unwrapped_and_multiline_content_is_literal():
    spec = importlib.util.spec_from_file_location("pac_scalar_deployer", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    description = "Preserve the complete native skill and every supporting resource. " * 40
    content = "---\nname: scalar-test\n---\n" + ("Run the native code, not a simulated answer.\n" * 20)
    payload = {
        "mcs.metadata": {"componentName": "rapp_scalar_test", "description": description},
        "kind": "InlineAgentSkill",
        "content": content,
        "resources": [{"path": "scripts/run.py", "contentBase64": "cHJpbnQoMSkK"}],
    }
    rendered = module._yaml_dump(payload)
    assert yaml.safe_load(rendered) == payload
    lines = rendered.splitlines()
    description_line = next(i for i, line in enumerate(lines) if line.startswith("  description:"))
    assert lines[description_line + 1] == "kind: InlineAgentSkill"
    assert "content: |\n" in rendered
    assert "\\\n" not in rendered
    assert rendered.startswith("mcs.metadata:\n")
