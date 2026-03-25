import json
import re
import shlex
import time
import os

class SecurityValidator:
    def __init__(self, policy_file=None, audit_log=None):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.policy_file = policy_file if policy_file is not None else os.path.join(repo_root, "security_policy.json")
        self.audit_log = audit_log if audit_log is not None else os.path.join(repo_root, "security_audit.jsonl")
        self.policy = self._load_policy()

    def _load_policy(self):
        if not os.path.exists(self.policy_file):
            return {"default_action": "allow", "rules": []}
        try:
            with open(self.policy_file, "r") as f:
                return json.load(f)
        except Exception:
            return {"default_action": "allow", "rules": []}

    def validate_command(self, command: str) -> tuple[bool, str]:
        try:
            tokens = shlex.split(command)
        except Exception:
            # If we can't parse it, default to allowed or denied based on policy
            tokens = command.split()
            
        if not tokens:
            self._audit(command, "allow", "Empty command")
            return True, "Empty command"
            
        cmd_name = tokens[0]
        cmd_args = tokens[1:]
        
        rules = self.policy.get("rules", [])
        for rule in rules:
            if rule.get("command") == cmd_name:
                rule_args = rule.get("args", [])
                
                if not rule_args:
                    decision = rule.get("action", "allow")
                    self._audit(command, decision, f"Matched rule for {cmd_name}")
                    return (decision == "allow"), f"Matched rule for {cmd_name}"
                    
                # A simple structural matching:
                # for each regex in rule_args, it must match at least one argument
                all_matched = True
                for rx in rule_args:
                    try:
                        pattern = re.compile(rx)
                        if not any(pattern.search(arg) for arg in cmd_args):
                            all_matched = False
                            break
                    except:
                        all_matched = False
                        break
                        
                if all_matched:
                    decision = rule.get("action", "allow")
                    self._audit(command, decision, f"Matched rule args for {cmd_name}")
                    return (decision == "allow"), f"Matched rule args for {cmd_name}"

        default_action = self.policy.get("default_action", "allow")
        self._audit(command, default_action, "Default policy action")
        return (default_action == "allow"), "Default policy action"

    def _audit(self, command, decision, reason):
        record = {
            "timestamp": time.time(),
            "command": command,
            "decision": decision,
            "reason": reason
        }
        try:
            with open(self.audit_log, "a") as f:
                f.write(json.dumps(record) + "\n")
        except Exception:
            pass