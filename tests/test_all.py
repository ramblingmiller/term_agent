import subprocess
import pytest
import os
import json
import sys

def test_runner_core():
    from term.runner_core import resolve_pipeline_mode, run_plan_execution, dispatch_tool_call, orchestrate_finish_and_critic
    
    # test resolve_pipeline_mode
    assert resolve_pipeline_mode(None, False, False, True) == (False, False)
    assert resolve_pipeline_mode("compact", None, None, False) == (True, False)
    assert resolve_pipeline_mode(None, True, False, False) == (True, False)
    assert resolve_pipeline_mode("compact", False, True, False) == (False, True)
    
    # test dispatch_tool_call
    def my_handler(action):
        if action["tool"] == "fail":
            raise Exception("boom")
        return {"status": "success", "result": 42}
    
    handlers = {"my_tool": my_handler, "fail": my_handler}
    res = dispatch_tool_call({"tool": "unknown"}, handlers, None)
    assert res["status"] == "unhandled"
    
    res = dispatch_tool_call({"tool": "my_tool"}, handlers, None)
    assert res["status"] == "success"
    
    res = dispatch_tool_call({"tool": "fail"}, handlers, None)
    assert res["status"] == "error"
    
    # test run_plan_execution
    class MockPlanManager:
        def __init__(self):
            self.steps = []
            self.updates = []
        def create_plan_with_ai(self, goal):
            self.steps = [{"description": goal}]
        def update_step_status(self, step, status, reason):
            self.updates.append((step, status, reason))
            
    pm = MockPlanManager()
    res = run_plan_execution({"tool": "create_action_plan", "goal": "my goal"}, pm, None)
    assert res["status"] == "success"
    assert len(pm.steps) == 1
    
    res = run_plan_execution({"tool": "update_plan_step", "step_number": 1, "status": "DONE", "result": "done"}, pm, None)
    assert res["status"] == "success"
    assert len(pm.updates) == 1
    
    # test orchestrate_finish_and_critic
    class MockCritic:
        def run(self, user_goal, agent_summary):
            return {"rating": 8, "verdict": "good", "rationale": "nice"}
            
    res = orchestrate_finish_and_critic("summary", True, "goal", True, MockCritic(), None, None, None, None, None, None, None)
    assert res["critic_rating"] == 8

def test_unified_cli_help():
    res = subprocess.run([sys.executable, "-m", "term", "--help"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "agent" in res.stdout
    assert "chat" in res.stdout
    assert "prompt" in res.stdout
    assert "api" in res.stdout

def test_subcommands_help():
    for cmd in ["agent", "chat", "prompt", "api"]:
        res = subprocess.run([sys.executable, "-m", "term", cmd, "--help"], capture_output=True, text=True)
        assert res.returncode == 0

def test_legacy_scripts_help():
    for script in ["term_ag.py", "term_ask.py", "term_api.py", "PromptCreator.py"]:
        res = subprocess.run([sys.executable, script, "--help"], capture_output=True, text=True)
        assert res.returncode == 0

def test_prompt_flag():
    res1 = subprocess.run([sys.executable, "term_ag.py", "-p", "--help"], capture_output=True, text=True)
    assert res1.returncode == 0
    assert "ModuleNotFoundError" not in res1.stderr
    assert "ImportError" not in res1.stderr

    res2 = subprocess.run([sys.executable, "term_ag.py", "--prompt", "--help"], capture_output=True, text=True)
    assert res2.returncode == 0
    assert "ModuleNotFoundError" not in res2.stderr
    assert "ImportError" not in res2.stderr

def test_term_ask_extra_arg():
    res = subprocess.run([sys.executable, "term_ask.py", "extra_arg"], capture_output=True, text=True)
    assert res.returncode != 0
    assert "Traceback" not in res.stderr
    assert "AttributeError" not in res.stderr

def test_branding():
    with open("VaultAiAgentRunner.py", "r") as f:
        content = f.read()
    assert "VaultAI>" in content
    assert "ValutAI>" not in content

def test_agents_md():
    with open("AGENTS.md", "r") as f:
        content = f.read()
    assert os.path.exists("term/runner_core.py")

def test_ml_deps_optional():
    with open("requirements.txt", "r") as f:
        content = f.read()
    assert "huggingface_hub" not in content
    assert "sentence-transformers" not in content
    assert "scikit-learn" not in content
    assert "numpy" not in content

    script = """
import sys
sys.modules['sentence_transformers'] = None
from ai.LogCompressor import DynamicLogCompressor
try:
    DynamicLogCompressor()
except SystemExit:
    sys.exit(2)
"""
    res = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
    assert res.returncode == 2
    assert "Missing optional ML dependencies" in res.stderr
    assert "Traceback" not in res.stderr

def test_security_policy():
    from security.SecurityValidator import SecurityValidator
    import term_ag
    
    val = SecurityValidator()
    assert val.validate_command("echo hello")[0] == True
    assert val.validate_command("rm -rf /")[0] == False
    
    out, code = term_ag.execute_local_command("rm -rf /")
    assert code != 0
    assert "blocked by security policy" in out
    
    out, code = term_ag.execute_local_command("echo hello")
    assert code == 0
    assert "hello" in out
    
    assert os.path.exists("security_audit.jsonl")
    with open("security_audit.jsonl", "r") as f:
        lines = f.readlines()
    
    found_rm = False
    found_echo = False
    for line in lines:
        try:
            record = json.loads(line)
            if record["command"] == "rm -rf /" and record["decision"] == "deny":
                found_rm = True
            if record["command"] == "echo hello" and record["decision"] == "allow":
                found_echo = True
        except:
            pass
            
    assert found_rm
    assert found_echo

def test_security_validator_blocks_builtin_dangerous_commands():
    from security.SecurityValidator import SecurityValidator

    val = SecurityValidator()
    assert val.validate_command("reboot")[0] == False
    assert val.validate_command("dd if=/dev/zero of=/dev/sda bs=1M")[0] == False
    assert val.validate_command("echo 'unterminated")[0] == False

def test_get_progress_includes_skipped():
    from plan.ActionPlanManager import ActionPlanManager, PlanStep, StepStatus

    manager = ActionPlanManager()
    manager.steps = [
        PlanStep(number=1, description="done", status=StepStatus.COMPLETED),
        PlanStep(number=2, description="skip", status=StepStatus.SKIPPED),
        PlanStep(number=3, description="pending", status=StepStatus.PENDING),
    ]

    progress = manager.get_progress()

    assert progress["completed"] == 1
    assert progress["skipped"] == 1
    assert progress["pending"] == 1

def test_chatgpt_and_openrouter_default_to_json_object(monkeypatch):
    import term_ag

    captured_calls = []

    class DummyLogger:
        def info(self, *_args, **_kwargs):
            pass

        def debug(self, *_args, **_kwargs):
            pass

        def error(self, *_args, **_kwargs):
            pass

    class FakeResponse:
        def __init__(self, content):
            self.choices = [type("Choice", (), {"message": type("Message", (), {"content": content})()})()]

    class FakeCompletions:
        def create(self, **kwargs):
            captured_calls.append(kwargs)
            return FakeResponse("{}")

    class FakeOpenAI:
        def __init__(self, **_kwargs):
            self.chat = type("Chat", (), {"completions": FakeCompletions()})()

    monkeypatch.setattr(term_ag, "OpenAI", FakeOpenAI)

    agent = term_ag.term_agent.__new__(term_ag.term_agent)
    agent.api_key = "test-key"
    agent.default_model = "gpt-test"
    agent.default_max_tokens = 32
    agent.default_temperature = 0.1
    agent.openrouter_model = "router-test"
    agent.openrouter_max_tokens = 64
    agent.openrouter_temperature = 0.2
    agent.logger = DummyLogger()
    agent.print_console = lambda *_args, **_kwargs: None

    assert term_ag.term_agent.connect_to_chatgpt(agent, "sys", "prompt") == "{}"
    assert captured_calls[-1]["response_format"] == {"type": "json_object"}

    assert term_ag.term_agent.connect_to_openrouter(agent, "sys", "prompt") == "{}"
    assert captured_calls[-1]["response_format"] == {"type": "json_object"}

def test_security_policy_file_exists():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    policy_file = os.path.join(repo_root, "security_policy.json")
    assert os.path.exists(policy_file), f"Expected {policy_file} to exist"

