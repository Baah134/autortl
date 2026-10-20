def init():
    return 0


def step(state, inputs: dict) -> (object, dict):
    count = int(state) & 0xFF
    rst = int(inputs.get("rst", 0)) & 1
    enable = int(inputs.get("enable", 0)) & 1

    if rst:
        count = 0
    elif enable:
        count = (count + 1) & 0xFF

    return count, {"count": count}