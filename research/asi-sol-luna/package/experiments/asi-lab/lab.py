"""Synthetic lab only: action requests are never host commands."""
def apply_action(state, action, allowed):
    if not isinstance(action, dict) or set(action) != {'operation', 'target', 'value'} or not all(isinstance(v, str) for v in action.values()):
        return {'status': 'invalid'}
    pair = (action['operation'], action['target'])
    if pair not in allowed:
        return {'status': 'blocked'}
    state[action['target']] = {'operation': action['operation'], 'value': action['value']}
    return {'status': 'applied_to_mock_state'}
