def init():
    return {}
def step(state, inputs):
    a = inputs['a']
    b = inputs['b']
    sa = a if a < 128 else a - 256
    sb = b if b < 128 else b - 256
    return state, {'less': int(sa < sb)}
