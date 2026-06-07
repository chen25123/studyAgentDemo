"""Bug / 需求 状态机白名单 —— 控制合法状态流转。"""

BUG_TRANSITIONS: dict[str, list[str]] = {
    "new": ["processing", "suspended", "rejected"],
    "processing": ["fixed", "suspended", "rejected"],
    "fixed": ["closed", "reopened"],
    "closed": ["reopened"],
    "reopened": ["processing", "fixed", "closed"],
    "suspended": ["processing"],
    "rejected": [],
}

REQUIREMENT_TRANSITIONS: dict[str, list[str]] = {
    "clarifying": ["clarified"],
    "clarified": ["pending_development"],
    "pending_development": ["developing"],
    "developing": ["development_done"],
    "development_done": ["pending_testing"],
    "pending_testing": ["testing"],
    "testing": ["testing_done"],
    "testing_done": ["released"],
    "released": [],
}


def is_valid_transition(entity_type: str, from_status: str, to_status: str) -> bool:
    if entity_type == "bug":
        allowed = BUG_TRANSITIONS.get(from_status, [])
    elif entity_type == "requirement":
        allowed = REQUIREMENT_TRANSITIONS.get(from_status, [])
    else:
        return False
    return to_status in allowed


def get_allowed_targets(entity_type: str, from_status: str) -> list[str]:
    if entity_type == "bug":
        return BUG_TRANSITIONS.get(from_status, [])
    elif entity_type == "requirement":
        return REQUIREMENT_TRANSITIONS.get(from_status, [])
    return []
