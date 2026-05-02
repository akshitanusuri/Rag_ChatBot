from typing import Dict, Any

def routing_logic(state: Dict[str, Any]) -> str:
    """decides next node based on evaluation."""

    if state.get("escalate", False):
        return "escalate"

    return "respond"