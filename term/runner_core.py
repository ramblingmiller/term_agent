def resolve_pipeline_mode(env_mode_str, compact_arg, hybrid_arg, force_plan):
    is_compact = False
    is_hybrid = False
    
    if force_plan:
        return (False, False)
        
    if env_mode_str:
        m = env_mode_str.lower()
        if m not in ('compact', 'normal', 'hybrid'):
            raise ValueError(f"Invalid pipeline mode: '{env_mode_str}'. Must be 'compact', 'normal', or 'hybrid'.")
        if m == 'compact':
            is_compact = True
        elif m == 'hybrid':
            is_hybrid = True

    if compact_arg is True:
        is_compact = True
        is_hybrid = False
    elif hybrid_arg is True:
        is_hybrid = True
        is_compact = False
        
    return (is_compact, is_hybrid)


def run_plan_execution(action_item: dict, plan_manager: object, logger: object) -> dict:
    if not isinstance(action_item, dict):
        return {"status": "error", "message": "action_item must be a dict"}

    tool = action_item.get("tool")

    if tool == "create_action_plan":
        goal = action_item.get("goal")
        if not isinstance(goal, str):
            return {"status": "error", "message": "'goal' must be a string"}
        try:
            # Here we just mock the AI behavior for tests by ignoring goal and doing a simple call
            # The real implementation calls create_plan_with_ai(goal). 
            # For compatibility with mock tests, we allow the mock to still work if needed.
            plan_manager.create_plan_with_ai(goal)
            return {"status": "success", "message": f"Created action plan for: {goal}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    elif tool == "update_plan_step":
        step_number = action_item.get("step_number")
        status = action_item.get("status")
        result = action_item.get("result")
        
        if step_number is None or status is None:
            return {"status": "error", "message": "Missing 'step_number' or 'status'"}
            
        try:
            plan_manager.update_step_status(int(step_number), str(status), result)
            return {"status": "success", "message": f"Updated step {step_number} to {status}."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    return {"status": "error", "message": f"Unknown plan execution tool: {tool}"}


def dispatch_tool_call(action_item: dict, handlers: dict, logger: object) -> dict:
    if not isinstance(action_item, dict):
        return {"status": "error", "message": "action_item must be a dict"}
        
    tool = action_item.get("tool")
    if not tool:
        return {"status": "error", "message": "No tool specified"}
        
    if tool not in handlers:
        return {"status": "unhandled", "message": f"Tool '{tool}' not handled"}
        
    handler = handlers[tool]
    try:
        result = handler(action_item)
        if isinstance(result, dict):
            if "status" not in result:
                result["status"] = "success"
            return result
        return {"status": "success", "message": str(result)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def orchestrate_finish_and_critic(summary_text: str, goal_success: bool, user_goal: str, enable_critic: bool, critic_sub_agent: object, finish_sub_agent: object, context_manager: object, plan_manager: object, steps: object, terminal: object, logger: object, get_user_input: callable) -> dict:
    result = {
        "summary": summary_text,
        "goal_success": goal_success,
        "critic_rating": None,
        "critic_verdict": None,
        "critic_rationale": None,
        "task_finished_successfully": goal_success,
        "agent_should_stop_this_turn": True
    }
    
    if goal_success and enable_critic and critic_sub_agent is not None:
        try:
            critic_result = critic_sub_agent.run(user_goal=user_goal, agent_summary=summary_text)
            if isinstance(critic_result, dict):
                result["critic_rating"] = critic_result.get("rating", critic_result.get("critic_rating"))
                result["critic_verdict"] = critic_result.get("verdict", critic_result.get("critic_verdict"))
                result["critic_rationale"] = critic_result.get("rationale", critic_result.get("critic_rationale"))
        except Exception as e:
            pass

    return result