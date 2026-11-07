def init():
    table = [131072, 77376, 40884, 20753, 10417, 5213, 2607, 1304,
             652, 326, 163, 81, 41, 20, 10, 5]
    return dict(table=table)

def step(state, inputs):
    idx = int(inputs.get("idx", 0)) & 15
    outputs = dict()
    outputs["atan"] = state.get("table", [0] * 16)[idx] & 1048575
    return state, outputs