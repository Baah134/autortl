# Supervised qualification artifact, never supplied as a model answer.
def init():
    return {}
def step(state, inputs):
    if inputs['rst']:
        return {}, {'out_data': 0}
    return state, {'out_data': inputs['in_data']}
