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

    def _deny(self, command: str, reason: str) -> tuple[bool, str]:
        self._audit(command, "deny", reason)
        return False, reason

    def _check_builtin_dangerous_command(self, command: str, cmd_name: str, cmd_args: list[str]) -> str | None:
        """Block especially dangerous commands even when policy defaults to allow."""
        if cmd_name in {"reboot", "halt", "poweroff"}:
            return f"Dangerous command blocked: {cmd_name}"

        if cmd_name == "shutdown":
            return "Dangerous command blocked: shutdown"

        if cmd_name == "systemctl" and any(arg in {"reboot", "halt", "poweroff"} for arg in cmd_args):
            return "Dangerous command blocked: systemctl power action"

        if cmd_name == "init" and any(arg in {"0", "6"} for arg in cmd_args):
            return "Dangerous command blocked: init power action"

        if cmd_name == "dd" and any(arg.startswith(("if=/dev/", "of=/dev/")) for arg in cmd_args):
            return "Dangerous command blocked: dd against device path"

        if cmd_name == "mkfs" or cmd_name.startswith("mkfs.") or cmd_name in {"fdisk", "sfdisk", "parted", "wipefs"}:
            return f"Dangerous command blocked: {cmd_name}"

        compact_command = re.sub(r"\s+", "", command)
        if compact_command == ":(){:|:&};:":
            return "Dangerous command blocked: fork bomb pattern"

        return None

    def validate_command(self, command: str) -> tuple[bool, str]:
        try:
            tokens = shlex.split(command)
        except Exception:
            return self._deny(command, "Unable to parse command safely")
            
        if not tokens:
            self._audit(command, "allow", "Empty command")
            return True, "Empty command"
            
        cmd_name = tokens[0]
        cmd_args = tokens[1:]

        dangerous_reason = self._check_builtin_dangerous_command(command, cmd_name, cmd_args)
        if dangerous_reason:
            return self._deny(command, dangerous_reason)
        
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