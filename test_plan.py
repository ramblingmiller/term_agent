from plan.ActionPlanManager import ActionPlanManager, StepStatus
pm = ActionPlanManager()
# It needs a valid ai_handler, wait, I can just mock steps:
from plan.ActionPlanManager import PlanStep
pm.steps = [PlanStep(number=1, description="d")]
try:
    pm.mark_step_status(1, "completed", "res")
    print(pm.steps[0].status, type(pm.steps[0].status))
except Exception as e:
    print(e)
try:
    pm.display_plan()
except Exception as e:
    print(e)
