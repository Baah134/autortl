def init():
    return dict(table=[131072, 77376, 40884, 20753, 10417, 5213, 2607, 1304, 652, 326, 163, 81, 41, 20, 10, 5])

def step(state, inputs):
    idx = int(inputs.get("idx", 0)) & 15
    outputs = dict(atan=state["table"][idx] & 1048575)
    return state, outputs