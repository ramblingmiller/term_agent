import os
import sys
import json
import pytest
from term_ag import execute_local_command

def test_deny_path_not_repo_root(tmp_path, monkeypatch):
    # Get the repo root path
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    audit_log = os.path.join(repo_root, "security_audit.jsonl")
    
    # Clean up audit log before test if it exists
    if os.path.exists(audit_log):
        os.remove(audit_log)
        
    marker_file = tmp_path / "rm_marker.txt"
    
    # Create a fake rm command
    fake_rm_script = tmp_path / "rm"
    fake_rm_script.write_text(f"#!/bin/bash\ntouch {marker_file}\n")
    fake_rm_script.chmod(0o755)
    
    # Prepend tmp_path to PATH so fake rm is found first
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env.get('PATH', '')}"
    monkeypatch.setattr(os, "environ", env)
    
    # Change current working directory to tmp_path
    monkeypatch.chdir(tmp_path)
    
    # Run the deny command
    out, code = execute_local_command("rm some_file")
    
    # Assertions
    assert code != 0
    assert "blocked by security policy" in out
    assert not marker_file.exists(), "Marker file was created, so rm was invoked!"
    
    # Check audit log
    assert os.path.exists(audit_log), f"Audit log not found at {audit_log}"
    
    with open(audit_log, "r") as f:
        lines = f.readlines()
        
    found_deny = False
    for line in lines:
        try:
            record = json.loads(line)
            if record["command"] == "rm some_file" and record["decision"] == "deny":
                found_deny = True
                break
        except json.JSONDecodeError:
            pass
            
    assert found_deny, "Audit log did not contain deny record for 'rm some_file'"


def test_allow_path_not_repo_root(tmp_path, monkeypatch):
    # Get the repo root path
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    audit_log = os.path.join(repo_root, "security_audit.jsonl")
    
    # Clean up audit log before test if it exists
    if os.path.exists(audit_log):
        os.remove(audit_log)
        
    # Change current working directory to tmp_path
    monkeypatch.chdir(tmp_path)
    
    # Run the allow command
    out, code = execute_local_command("echo security_allowed")
    
    # Assertions
    assert code == 0
    assert "security_allowed" in out
    
    # Check audit log
    assert os.path.exists(audit_log), f"Audit log not found at {audit_log}"
    
    with open(audit_log, "r") as f:
        lines = f.readlines()
        
    found_allow = False
    for line in lines:
        try:
            record = json.loads(line)
            if record["command"] == "echo security_allowed" and record["decision"] == "allow":
                found_allow = True
                break
        except json.JSONDecodeError:
            pass
            
    assert found_allow, "Audit log did not contain allow record for 'echo security_allowed'"
