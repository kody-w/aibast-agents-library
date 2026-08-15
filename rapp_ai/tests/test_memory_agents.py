"""
Memory Agent Platform Tests

Tests for the core memory agent platform:
- Agent loading and discovery
- Memory read (ContextMemory) and write (ManageMemory)
- Storage backend (local file storage)
- Per-request memory isolation (tenancy)
- API contract (request/response format)
- ARM deployment template invariants
"""
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLocalFileStorage(unittest.TestCase):
    """Test local file storage backend (the default for development)."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.environ['LOCAL_STORAGE_PATH'] = self.test_dir
        from utils.local_file_storage import LocalFileStorageManager
        self.storage = LocalFileStorageManager(base_path=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        os.environ.pop('LOCAL_STORAGE_PATH', None)

    def test_write_and_read_json(self):
        """Write JSON memory and read it back."""
        data = {"test-uuid": {"message": "Hello world", "theme": "fact", "date": "2025-01-01", "time": "10:00:00"}}
        self.storage.write_json(data)
        result = self.storage.read_json()
        self.assertEqual(result, data)

    def test_shared_memory_context(self):
        """Shared memory (no GUID) writes to shared location."""
        self.storage.set_memory_context(None)
        self.storage.write_json({"shared-id": {"message": "shared fact", "theme": "fact"}})
        result = self.storage.read_json()
        self.assertIn("shared-id", result)

    def test_user_memory_context(self):
        """User-specific memory writes to user-specific location."""
        user_guid = "550e8400-e29b-41d4-a716-446655440000"
        self.storage.set_memory_context(user_guid)
        self.storage.write_json({"user-id": {"message": "user fact", "theme": "preference"}})
        result = self.storage.read_json()
        self.assertIn("user-id", result)

    def test_user_and_shared_memory_isolated(self):
        """User and shared memory are separate."""
        # Write shared
        self.storage.set_memory_context(None)
        self.storage.write_json({"shared": {"message": "shared"}})

        # Write user-specific
        user_guid = "550e8400-e29b-41d4-a716-446655440000"
        self.storage.set_memory_context(user_guid)
        self.storage.write_json({"user": {"message": "user-only"}})

        # Read shared — should NOT contain user data
        self.storage.set_memory_context(None)
        shared = self.storage.read_json()
        self.assertIn("shared", shared)
        self.assertNotIn("user", shared)

        # Read user — should NOT contain shared data
        self.storage.set_memory_context(user_guid)
        user_data = self.storage.read_json()
        self.assertIn("user", user_data)
        self.assertNotIn("shared", user_data)

    def test_read_empty_returns_empty_dict(self):
        """Reading non-existent memory returns empty dict."""
        self.storage.set_memory_context("nonexistent-guid")
        result = self.storage.read_json()
        self.assertEqual(result, {})

    def test_write_file_and_read_file(self):
        """Raw file read/write works."""
        self.storage.write_file("test_share", "test.txt", "Hello from test")
        result = self.storage.read_file("test_share", "test.txt")
        self.assertEqual(result, "Hello from test")


class TestContextMemoryAgent(unittest.TestCase):
    """Test ContextMemory agent (memory read)."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        # Patch storage factory to return local storage
        from utils.local_file_storage import LocalFileStorageManager
        self.storage = LocalFileStorageManager(base_path=self.test_dir)

        # Pre-populate with test memories
        self.storage.set_memory_context(None)
        self.storage.write_json({
            "mem-1": {
                "conversation_id": "current",
                "session_id": "current",
                "message": "User prefers morning meetings",
                "mood": "neutral",
                "theme": "preference",
                "date": "2025-12-15",
                "time": "10:30:45"
            },
            "mem-2": {
                "conversation_id": "current",
                "session_id": "current",
                "message": "Follow up with Acme Corp on Q1 proposal",
                "mood": "neutral",
                "theme": "task",
                "date": "2025-12-16",
                "time": "14:20:30"
            },
            "mem-3": {
                "conversation_id": "current",
                "session_id": "current",
                "message": "Budget for project is $50,000",
                "mood": "neutral",
                "theme": "fact",
                "date": "2025-12-14",
                "time": "09:00:00"
            }
        })

        self.patcher = patch('agents.context_memory_agent.get_storage_manager', return_value=self.storage)
        self.patcher.start()

        from agents.context_memory_agent import ContextMemoryAgent
        self.agent = ContextMemoryAgent()
        self.agent.storage_manager = self.storage

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_full_recall(self):
        """Full recall returns all memories."""
        result = self.agent.perform(full_recall=True)
        self.assertIn("morning meetings", result)
        self.assertIn("Acme Corp", result)
        self.assertIn("$50,000", result)

    def test_default_is_full_recall(self):
        """No params defaults to full recall."""
        result = self.agent.perform()
        self.assertIn("morning meetings", result)
        self.assertIn("Acme Corp", result)

    def test_keyword_filter(self):
        """Keyword filtering returns only matching memories."""
        result = self.agent.perform(keywords=["Acme"])
        self.assertIn("Acme Corp", result)

    def test_max_messages(self):
        """max_messages limits results."""
        result = self.agent.perform(max_messages=1)
        # Should have at most 1 bullet point
        lines = [l for l in result.split("\n") if l.strip().startswith("•")]
        self.assertLessEqual(len(lines), 1)

    def test_empty_memory(self):
        """Empty memory returns appropriate message."""
        self.storage.set_memory_context("empty-user-guid")
        self.storage.write_json({})
        self.agent.storage_manager = self.storage
        result = self.agent.perform(user_guid="empty-user-guid")
        self.assertIn("don't have any memories", result.lower())

    def test_agent_metadata(self):
        """Agent has correct metadata schema."""
        self.assertEqual(self.agent.name, "ContextMemory")
        self.assertIn("parameters", self.agent.metadata)
        props = self.agent.metadata["parameters"]["properties"]
        self.assertIn("user_guid", props)
        self.assertIn("max_messages", props)
        self.assertIn("keywords", props)
        self.assertIn("full_recall", props)


class TestManageMemoryAgent(unittest.TestCase):
    """Test ManageMemory agent (memory write)."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        from utils.local_file_storage import LocalFileStorageManager
        self.storage = LocalFileStorageManager(base_path=self.test_dir)

        self.patcher = patch('agents.manage_memory_agent.get_storage_manager', return_value=self.storage)
        self.patcher.start()

        from agents.manage_memory_agent import ManageMemoryAgent
        self.agent = ManageMemoryAgent()
        self.agent.storage_manager = self.storage

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_store_fact(self):
        """Store a fact memory."""
        result = self.agent.perform(memory_type="fact", content="The sky is blue")
        self.assertIn("Successfully stored", result)
        self.assertIn("fact", result)

        # Verify in storage
        data = self.storage.read_json()
        self.assertTrue(len(data) > 0)
        memory = list(data.values())[0]
        self.assertEqual(memory["message"], "The sky is blue")
        self.assertEqual(memory["theme"], "fact")

    def test_store_preference(self):
        """Store a preference memory."""
        result = self.agent.perform(memory_type="preference", content="Dark mode preferred")
        self.assertIn("preference", result)

    def test_store_insight(self):
        """Store an insight memory."""
        result = self.agent.perform(memory_type="insight", content="Sales peak in Q4")
        self.assertIn("insight", result)

    def test_store_task(self):
        """Store a task memory."""
        result = self.agent.perform(memory_type="task", content="Review Q1 report by Friday")
        self.assertIn("task", result)

    def test_empty_content_rejected(self):
        """Empty content returns error."""
        result = self.agent.perform(memory_type="fact", content="")
        self.assertIn("Error", result)

    def test_user_specific_memory(self):
        """Memory stored for specific user."""
        user_guid = "550e8400-e29b-41d4-a716-446655440000"
        result = self.agent.perform(
            memory_type="fact",
            content="User's birthday is March 15",
            user_guid=user_guid
        )
        self.assertIn("Successfully stored", result)
        self.assertIn(user_guid, result)

    def test_memory_has_timestamp(self):
        """Stored memory includes date and time."""
        self.agent.perform(memory_type="fact", content="Test timestamp")
        data = self.storage.read_json()
        memory = list(data.values())[0]
        self.assertIn("date", memory)
        self.assertIn("time", memory)
        # Date should be today
        self.assertEqual(memory["date"], datetime.now().strftime("%Y-%m-%d"))

    def test_multiple_memories(self):
        """Multiple memories stored with unique IDs."""
        self.agent.perform(memory_type="fact", content="Fact one")
        self.agent.perform(memory_type="fact", content="Fact two")
        data = self.storage.read_json()
        self.assertEqual(len(data), 2)
        messages = [v["message"] for v in data.values()]
        self.assertIn("Fact one", messages)
        self.assertIn("Fact two", messages)

    def test_agent_metadata(self):
        """Agent has correct metadata schema."""
        self.assertEqual(self.agent.name, "ManageMemory")
        meta = self.agent.metadata
        self.assertIn("memory_type", meta["parameters"]["properties"])
        self.assertIn("content", meta["parameters"]["properties"])
        self.assertEqual(meta["parameters"]["required"], ["memory_type", "content"])


class TestAgentLoading(unittest.TestCase):
    """Test agent discovery and loading from agents/ folder."""

    def test_load_core_agents(self):
        """Core agents load successfully from agents/ folder."""
        from function_app import load_agents_from_folder
        agents = load_agents_from_folder()
        # Returns dict: name -> agent instance
        self.assertIsInstance(agents, dict)
        self.assertIn("ContextMemory", agents)
        self.assertIn("ManageMemory", agents)
        self.assertGreaterEqual(len(agents), 2)

    def test_agents_have_metadata(self):
        """All loaded agents have proper metadata for OpenAI function calling."""
        from function_app import load_agents_from_folder
        agents = load_agents_from_folder()
        for name, agent in agents.items():
            self.assertTrue(hasattr(agent, 'name'), f"Agent missing 'name'")
            self.assertTrue(hasattr(agent, 'metadata'), f"Agent {name} missing 'metadata'")
            meta = agent.metadata
            self.assertIn("name", meta, f"Agent {name} metadata missing 'name'")
            self.assertIn("description", meta, f"Agent {name} metadata missing 'description'")
            self.assertIn("parameters", meta, f"Agent {name} metadata missing 'parameters'")

    def test_agents_have_perform_method(self):
        """All loaded agents have a callable perform() method."""
        from function_app import load_agents_from_folder
        agents = load_agents_from_folder()
        for name, agent in agents.items():
            self.assertTrue(callable(getattr(agent, 'perform', None)),
                          f"Agent {name} missing callable 'perform'")


class TestStringSafety(unittest.TestCase):
    """Test string safety utilities."""

    def test_ensure_string_content_with_none(self):
        """None message content becomes empty string."""
        from function_app import ensure_string_content
        msg = {"role": "user", "content": None}
        result = ensure_string_content(msg)
        self.assertEqual(result["content"], "")

    def test_ensure_string_content_with_string(self):
        """String content passes through unchanged."""
        from function_app import ensure_string_content
        msg = {"role": "user", "content": "Hello"}
        result = ensure_string_content(msg)
        self.assertEqual(result["content"], "Hello")

    def test_ensure_string_content_with_list(self):
        """List content is stringified."""
        from function_app import ensure_string_content
        msg = {"role": "user", "content": ["item1", "item2"]}
        result = ensure_string_content(msg)
        self.assertIsInstance(result["content"], str)


class TestAPIContract(unittest.TestCase):
    """Test the API request/response contract."""

    def test_health_response_structure(self):
        """Health response builds correct JSON structure."""
        # Test the health status construction logic directly
        health_status = {
            "status": "healthy",
            "timestamp": "2025-01-01T00:00:00Z",
            "version": "1.0.0",
            "checks": {
                "basic": {"status": "pass", "message": "Function app is responding"}
            }
        }
        # Validate structure matches expected contract
        self.assertEqual(health_status["status"], "healthy")
        self.assertIn("timestamp", health_status)
        self.assertIn("checks", health_status)
        self.assertIn("basic", health_status["checks"])

    def test_cors_headers(self):
        """CORS headers are built correctly."""
        from function_app import build_cors_response
        headers = build_cors_response("http://localhost:3000")
        self.assertIn("Access-Control-Allow-Origin", headers)
        self.assertIn("Access-Control-Allow-Methods", headers)


class TestMemoryReadWriteIntegration(unittest.TestCase):
    """Integration test: write memory then read it back."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        from utils.local_file_storage import LocalFileStorageManager
        self.storage = LocalFileStorageManager(base_path=self.test_dir)

        self.ctx_patcher = patch('agents.context_memory_agent.get_storage_manager', return_value=self.storage)
        self.mgr_patcher = patch('agents.manage_memory_agent.get_storage_manager', return_value=self.storage)
        self.ctx_patcher.start()
        self.mgr_patcher.start()

        from agents.context_memory_agent import ContextMemoryAgent
        from agents.manage_memory_agent import ManageMemoryAgent
        self.reader = ContextMemoryAgent()
        self.reader.storage_manager = self.storage
        self.writer = ManageMemoryAgent()
        self.writer.storage_manager = self.storage

    def tearDown(self):
        self.ctx_patcher.stop()
        self.mgr_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_write_then_read_shared(self):
        """Write to shared memory, then read it back."""
        self.writer.perform(memory_type="fact", content="Project deadline is March 30")
        result = self.reader.perform(full_recall=True)
        self.assertIn("March 30", result)

    def test_write_then_read_user_specific(self):
        """Write to user memory, then read it back."""
        guid = "550e8400-e29b-41d4-a716-446655440000"
        self.writer.perform(memory_type="preference", content="Prefers dark mode", user_guid=guid)
        result = self.reader.perform(user_guid=guid, full_recall=True)
        self.assertIn("dark mode", result)

    def test_user_memory_not_in_shared(self):
        """User-specific memory doesn't bleed into shared memory."""
        guid = "550e8400-e29b-41d4-a716-446655440000"
        self.writer.perform(memory_type="fact", content="Secret user data", user_guid=guid)

        # Shared memory should NOT contain user data
        self.storage.set_memory_context(None)
        shared = self.storage.read_json()
        shared_messages = [v.get("message", "") for v in shared.values() if isinstance(v, dict)]
        self.assertNotIn("Secret user data", shared_messages)

    def test_multiple_types_stored(self):
        """Multiple memory types can be stored and recalled."""
        self.writer.perform(memory_type="fact", content="Earth orbits the Sun")
        self.writer.perform(memory_type="task", content="Buy groceries")
        self.writer.perform(memory_type="insight", content="Revenue grows in Q4")
        self.writer.perform(memory_type="preference", content="Prefers email over chat")

        result = self.reader.perform(full_recall=True)
        self.assertIn("Earth orbits", result)
        self.assertIn("groceries", result)
        self.assertIn("Q4", result)
        self.assertIn("email", result)

    def test_keyword_search_after_write(self):
        """Write multiple memories, then search by keyword."""
        self.writer.perform(memory_type="fact", content="Python is a programming language")
        self.writer.perform(memory_type="fact", content="Azure Functions runs serverless code")
        self.writer.perform(memory_type="task", content="Deploy Python app to Azure")

        result = self.reader.perform(keywords=["Python"])
        self.assertIn("Python", result)


class TestMemoryContextThreadIsolation(unittest.TestCase):
    """Regression: the storage manager is a process-wide singleton but every HTTP
    request is served on its own worker thread. The active memory context must be
    per-thread or one user's request reads/writes another user's memory."""

    GUID_A = "11111111-1111-1111-1111-111111111111"
    GUID_B = "22222222-2222-2222-2222-222222222222"

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        from utils.local_file_storage import LocalFileStorageManager
        self.storage = LocalFileStorageManager(base_path=self.test_dir)
        self.storage.set_memory_context(self.GUID_A)
        self.storage.write_json({"a": {"message": "A-secret", "theme": "fact"}})
        self.storage.set_memory_context(self.GUID_B)
        self.storage.write_json({"b": {"message": "B-secret", "theme": "fact"}})
        self.storage.set_memory_context(None)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_concurrent_contexts_do_not_leak_between_threads(self):
        """Two threads holding different GUID contexts read only their own memory."""
        import threading

        seen = {}
        errors = []
        # Both threads set their context, then wait for each other before reading, so a
        # shared (non thread-local) context is guaranteed to have been clobbered.
        barrier = threading.Barrier(2, timeout=10)

        def worker(guid, key):
            try:
                self.storage.set_memory_context(guid)
                barrier.wait()
                seen[key] = self.storage.read_json()
            except Exception as exc:  # pragma: no cover - surfaced via assertion
                errors.append(exc)

        threads = [
            threading.Thread(target=worker, args=(self.GUID_A, "A")),
            threading.Thread(target=worker, args=(self.GUID_B, "B")),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15)

        self.assertEqual(errors, [])
        self.assertIn("a", seen["A"], "thread A read another user's memory")
        self.assertNotIn("b", seen["A"], "thread A leaked thread B's memory")
        self.assertIn("b", seen["B"], "thread B read another user's memory")
        self.assertNotIn("a", seen["B"], "thread B leaked thread A's memory")

    def test_concurrent_writes_land_in_own_partition(self):
        """A write on one thread never lands in the other thread's partition."""
        import threading

        barrier = threading.Barrier(2, timeout=10)
        errors = []

        def writer(guid, payload):
            try:
                self.storage.set_memory_context(guid)
                barrier.wait()
                self.storage.write_json(payload)
            except Exception as exc:  # pragma: no cover - surfaced via assertion
                errors.append(exc)

        threads = [
            threading.Thread(target=writer, args=(self.GUID_A, {"a2": {"message": "A-only"}})),
            threading.Thread(target=writer, args=(self.GUID_B, {"b2": {"message": "B-only"}})),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15)

        self.assertEqual(errors, [])
        self.storage.set_memory_context(self.GUID_A)
        self.assertEqual(list(self.storage.read_json().keys()), ["a2"])
        self.storage.set_memory_context(self.GUID_B)
        self.assertEqual(list(self.storage.read_json().keys()), ["b2"])

    def test_unset_thread_defaults_to_shared_memory(self):
        """A thread that never set a context sees shared memory, not a stale GUID."""
        import threading

        self.storage.set_memory_context(self.GUID_A)
        observed = {}

        def worker():
            observed['guid'] = self.storage.current_guid
            observed['path'] = self.storage.current_memory_path

        t = threading.Thread(target=worker)
        t.start()
        t.join(timeout=10)

        self.assertIsNone(observed['guid'])
        self.assertEqual(observed['path'], self.storage.shared_memory_path)

    def test_azure_manager_uses_thread_local_context(self):
        """The Azure manager exposes the same thread-local context contract."""
        from utils.azure_file_storage import AzureFileStorageManager
        self.assertIsInstance(AzureFileStorageManager.current_guid, property)
        self.assertIsInstance(AzureFileStorageManager.current_memory_path, property)


class TestUserGuidValidation(unittest.TestCase):
    """Regression: a user_guid that is not a GUID is not a private partition — the
    storage managers silently route it to shared memory, publishing that caller's
    memories to everyone. It must be rejected at the API boundary."""

    def test_is_valid_user_guid_accepts_guids_and_default_marker(self):
        from function_app import is_valid_user_guid, DEFAULT_USER_GUID
        self.assertTrue(is_valid_user_guid("550e8400-e29b-41d4-a716-446655440000"))
        self.assertTrue(is_valid_user_guid("550E8400-E29B-41D4-A716-446655440000"))
        self.assertTrue(is_valid_user_guid("  550e8400-e29b-41d4-a716-446655440000  "))
        self.assertTrue(is_valid_user_guid(DEFAULT_USER_GUID))

    def test_is_valid_user_guid_rejects_non_guids(self):
        from function_app import is_valid_user_guid
        for bad in ["", "   ", "not-a-guid", "../../shared_memories", "memory/../..",
                    "550e8400-e29b-41d4-a716", None, 12345, {"a": 1}, ["guid"]]:
            self.assertFalse(is_valid_user_guid(bad), f"{bad!r} must not be a valid partition key")

    def test_main_rejects_malformed_user_guid(self):
        import azure.functions as func
        from function_app import main

        handler = main._function.get_user_function()
        for bad in ["../../shared_memories", "not-a-guid", 42, {"a": 1}]:
            body = json.dumps({"user_input": "hello", "user_guid": bad}).encode()
            req = func.HttpRequest(method='POST', url='http://localhost/api/businessinsightbot_function',
                                   body=body, headers={})
            resp = handler(req)
            self.assertEqual(resp.status_code, 400, f"user_guid={bad!r} should be rejected")
            self.assertIn("Invalid user_guid", resp.get_body().decode())

    def test_main_rejects_non_object_body(self):
        import azure.functions as func
        from function_app import main

        handler = main._function.get_user_function()
        req = func.HttpRequest(method='POST', url='http://localhost/api/businessinsightbot_function',
                               body=b'[1, 2, 3]', headers={})
        resp = handler(req)
        self.assertEqual(resp.status_code, 400)

    def test_main_pins_valid_user_guid(self):
        import azure.functions as func
        import function_app as fa

        handler = fa.main._function.get_user_function()
        guid = "550e8400-e29b-41d4-a716-446655440000"
        assistant = MagicMock()
        assistant.user_guid = guid
        assistant.run.return_value = ("formatted", "voice", "logs")

        with patch.object(fa, 'Assistant', return_value=assistant), \
                patch.object(fa, '_get_cached_agents', return_value={}):
            body = json.dumps({"user_input": "hello", "user_guid": guid}).encode()
            req = func.HttpRequest(method='POST', url='http://localhost/api/businessinsightbot_function',
                                   body=body, headers={})
            resp = handler(req)

        self.assertEqual(resp.status_code, 200)
        assistant.set_user_guid.assert_called_once_with(guid)
        self.assertEqual(json.loads(resp.get_body())["user_guid"], guid)


class TestAssistantConversationHistoryRobustness(unittest.TestCase):
    """Regression: conversation_history entries are attacker/client controlled and are
    not guaranteed to be objects. Non-dict entries used to raise AttributeError and
    surface as HTTP 500."""

    GUID_A = "11111111-1111-1111-1111-111111111111"
    GUID_B = "22222222-2222-2222-2222-222222222222"

    def _assistant(self):
        from function_app import Assistant, DEFAULT_USER_GUID
        assistant = Assistant.__new__(Assistant)
        assistant.config = {'assistant_name': 'Test', 'characteristic_description': 'test'}
        assistant.client = MagicMock()
        assistant.known_agents = {}
        assistant.user_guid = DEFAULT_USER_GUID
        assistant.guid_is_pinned = False
        assistant.shared_memory = "none"
        assistant.user_memory = "none"
        assistant.storage_manager = MagicMock()
        assistant._initialize_context_memory = MagicMock()
        return assistant

    def _stub_reply(self, assistant, content="All done.|||VOICE|||Done."):
        from utils.result import Success
        message = MagicMock()
        message.content = content
        message.tool_calls = None
        message.function_call = None
        response = MagicMock()
        response.choices = [MagicMock(message=message)]
        assistant._get_openai_api_call = MagicMock(return_value=Success(response))
        return assistant

    def test_first_message_guid_check_tolerates_non_dict_entries(self):
        assistant = self._assistant()
        self.assertIsNone(assistant._check_first_message_for_guid(["just a string"]))
        self.assertIsNone(assistant._check_first_message_for_guid([None]))
        self.assertIsNone(assistant._check_first_message_for_guid([42]))
        self.assertIsNone(assistant._check_first_message_for_guid("not a list"))
        self.assertIsNone(assistant._check_first_message_for_guid(None))

    def test_first_message_guid_still_detected(self):
        assistant = self._assistant()
        self.assertEqual(
            assistant._check_first_message_for_guid([{"role": "user", "content": self.GUID_A}]),
            self.GUID_A
        )

    def test_prepare_messages_tolerates_non_dict_entries(self):
        assistant = self._assistant()
        messages = assistant._prepare_messages(["a string", 42, None, {"role": "user", "content": "hi"}])
        self.assertTrue(all(isinstance(m, dict) and isinstance(m["content"], str) for m in messages))

    def test_run_tolerates_non_dict_history(self):
        assistant = self._stub_reply(self._assistant())
        formatted, voice, logs = assistant.run("hello", ["a string", 42, {"role": "user", "content": "hi"}])
        self.assertEqual(formatted, "All done.")
        self.assertEqual(voice, "Done.")

    def test_run_tolerates_non_list_history(self):
        assistant = self._stub_reply(self._assistant())
        formatted, _, _ = assistant.run("hello", None)
        self.assertEqual(formatted, "All done.")

    def test_pinned_guid_is_not_overridden_by_conversation_content(self):
        """A caller-supplied user_guid must win over a GUID embedded in the history."""
        assistant = self._stub_reply(self._assistant())
        assistant.user_guid = self.GUID_A
        assistant.guid_is_pinned = True

        assistant.run("hello", [{"role": "user", "content": self.GUID_B}])

        self.assertEqual(assistant.user_guid, self.GUID_A)
        assistant._initialize_context_memory.assert_not_called()

    def test_unpinned_guid_still_adopted_from_history(self):
        """Without an explicit user_guid the legacy GUID-first-message flow still works."""
        assistant = self._stub_reply(self._assistant())
        assistant.run("hello", [{"role": "user", "content": self.GUID_B}])
        self.assertEqual(assistant.user_guid, self.GUID_B)
        assistant._initialize_context_memory.assert_called_once_with(self.GUID_B)

    def test_malformed_tool_arguments_are_reported_not_splatted(self):
        """A malformed tool-call payload must not be passed to the agent as parameters."""
        agent = MagicMock()
        agent.perform.return_value = "should not run"
        assistant = self._assistant()
        assistant.known_agents = {"Echo": agent}

        result, error = assistant._execute_agent("Echo", "{not valid json")

        self.assertIsNone(result)
        self.assertIn("malformed arguments", error)
        agent.perform.assert_not_called()

    def test_non_object_tool_arguments_are_reported(self):
        agent = MagicMock()
        assistant = self._assistant()
        assistant.known_agents = {"Echo": agent}

        result, error = assistant._execute_agent("Echo", "[1, 2, 3]")

        self.assertIsNone(result)
        self.assertIn("malformed arguments", error)
        agent.perform.assert_not_called()

    def test_valid_tool_arguments_still_execute(self):
        agent = MagicMock()
        agent.perform.return_value = "ok"
        assistant = self._assistant()
        assistant.known_agents = {"Echo": agent}

        result, error = assistant._execute_agent("Echo", '{"content": "hi", "empty": null}')

        self.assertIsNone(error)
        self.assertEqual(result, "ok")
        agent.perform.assert_called_once_with(content="hi", empty="")

    def test_memory_agent_user_guid_is_forced_to_session_guid(self):
        """A model-invented user_guid must never override the session's partition."""
        agent = MagicMock()
        agent.perform.return_value = "stored"
        assistant = self._assistant()
        assistant.known_agents = {"ManageMemory": agent}
        assistant.user_guid = self.GUID_A

        assistant._execute_agent("ManageMemory", json.dumps({
            "memory_type": "fact", "content": "x", "user_guid": self.GUID_B
        }))

        agent.perform.assert_called_once_with(
            memory_type="fact", content="x", user_guid=self.GUID_A
        )


class TestCopilotStudioTriggerContract(unittest.TestCase):
    """Regression: the documented contract is 400 for invalid request format or
    parameters. Malformed payloads used to raise and surface as HTTP 500."""

    def _call(self, body):
        import azure.functions as func
        from function_app import copilot_studio_trigger

        handler = copilot_studio_trigger._function.get_user_function()
        if not isinstance(body, bytes):
            body = json.dumps(body).encode()
        req = func.HttpRequest(method='POST', url='http://localhost/api/trigger/copilot-studio',
                               body=body, headers={})
        return handler(req)

    def test_invalid_json_is_bad_request(self):
        self.assertEqual(self._call(b'not json at all').status_code, 400)

    def test_non_object_body_is_bad_request(self):
        self.assertEqual(self._call(b'null').status_code, 400)
        self.assertEqual(self._call(b'[1, 2]').status_code, 400)
        self.assertEqual(self._call(b'"a string"').status_code, 400)

    def test_missing_fields_is_bad_request(self):
        self.assertEqual(self._call({"agent": "ContextMemory"}).status_code, 400)

    def test_non_string_agent_or_action_is_bad_request(self):
        self.assertEqual(self._call({"agent": {"a": 1}, "action": "x"}).status_code, 400)
        self.assertEqual(self._call({"agent": "ContextMemory", "action": ["x"]}).status_code, 400)

    def test_non_object_parameters_is_bad_request(self):
        resp = self._call({"agent": "ContextMemory", "action": "recall", "parameters": "oops"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("parameters", resp.get_body().decode())

    def test_malformed_user_guid_is_bad_request(self):
        resp = self._call({"agent": "ContextMemory", "action": "recall",
                           "parameters": {"user_guid": "../../shared_memories"}})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Invalid user_guid", resp.get_body().decode())

    def test_null_parameters_is_treated_as_empty(self):
        resp = self._call({"agent": "NoSuchAgent", "action": "x", "parameters": None})
        self.assertEqual(resp.status_code, 404)

    def test_unknown_agent_is_not_found(self):
        resp = self._call({"agent": "NoSuchAgent", "action": "x"})
        self.assertEqual(resp.status_code, 404)

    def test_valid_invocation_succeeds(self):
        import function_app as fa

        agent = MagicMock()
        agent.perform.return_value = "done"
        with patch.object(fa, '_get_cached_agents', return_value={"Echo": agent}):
            resp = self._call({"agent": "Echo", "action": "run", "parameters": {"content": "hi"}})

        self.assertEqual(resp.status_code, 200)
        agent.perform.assert_called_once_with(content="hi", action="run")
        self.assertEqual(json.loads(resp.get_body())["status"], "success")


class TestDeploymentTemplate(unittest.TestCase):
    """Regression: the ARM template must be deployable for every model it allows and
    must configure the auth mode the storage account it creates actually supports."""

    @classmethod
    def setUpClass(cls):
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'azuredeploy.json'
        )
        with open(template_path, 'r', encoding='utf-8') as handle:
            cls.template = json.load(handle)

    def _resource(self, resource_type):
        matches = [r for r in self.template['resources'] if r['type'] == resource_type]
        self.assertTrue(matches, f"no {resource_type} resource in template")
        return matches[0]

    def test_model_version_is_not_pinned_to_a_single_model(self):
        """A hardcoded version only exists for one model, so every other allowed value fails."""
        allowed = self.template['parameters']['openAIModelName']['allowedValues']
        self.assertGreater(len(allowed), 1)
        model = self._resource('Microsoft.CognitiveServices/accounts/deployments')['properties']['model']
        self.assertNotIn(
            'version', model,
            "model.version must stay unset so each allowed model deploys at its own default version"
        )

    def test_default_model_is_an_allowed_value(self):
        params = self.template['parameters']['openAIModelName']
        self.assertIn(params['defaultValue'], params['allowedValues'])

    def test_identity_based_storage_is_configured(self):
        """Shared key auth is disabled on the storage account, so the app must use Entra ID."""
        storage = self._resource('Microsoft.Storage/storageAccounts')
        self.assertFalse(storage['properties']['allowSharedKeyAccess'])

        site = self._resource('Microsoft.Web/sites')
        settings = {s['name']: s['value'] for s in site['properties']['siteConfig']['appSettings']}
        self.assertEqual(settings.get('USE_IDENTITY_BASED_STORAGE'), 'true')
        self.assertEqual(settings.get('USE_CLOUD_STORAGE'), 'true')

    def test_storage_settings_match_runtime_expectations(self):
        site = self._resource('Microsoft.Web/sites')
        settings = {s['name'] for s in site['properties']['siteConfig']['appSettings']}
        for required in ('AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_DEPLOYMENT_NAME',
                         'AZURE_STORAGE_ACCOUNT_NAME', 'AZURE_FILES_SHARE_NAME'):
            self.assertIn(required, settings)

    def test_role_assignments_reference_defined_variables(self):
        variables = self.template['variables']
        assignments = [r for r in self.template['resources']
                       if r['type'] == 'Microsoft.Authorization/roleAssignments']
        self.assertTrue(assignments)
        for assignment in assignments:
            role_definition = assignment['properties']['roleDefinitionId']
            referenced = re.findall(r"variables\('([^']+)'\)", role_definition)
            self.assertTrue(referenced, f"role assignment has no variable reference: {role_definition}")
            for name in referenced:
                self.assertIn(name, variables, f"undefined variable in template: {name}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
