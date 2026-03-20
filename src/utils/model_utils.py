def unwrap_dp_state_dict(state_dict):
    """Remove Opacus DP wrapper prefixes from state dict"""
    if not state_dict:
        return state_dict

    # Check if this is a DP-wrapped state dict
    if any(key.startswith("_module.") for key in state_dict.keys()):
        unwrapped = {}
        for key, value in state_dict.items():
            if key.startswith("_module."):
                new_key = key[8:]  # Remove '_module.' prefix
                unwrapped[new_key] = value
            else:
                unwrapped[key] = value
        return unwrapped
    return state_dict


def wrap_dp_state_dict(state_dict):
    """Add Opacus DP wrapper prefix to state dict"""
    wrapped = {}
    for key, value in state_dict.items():
        wrapped[f"_module.{key}"] = value
    return wrapped
