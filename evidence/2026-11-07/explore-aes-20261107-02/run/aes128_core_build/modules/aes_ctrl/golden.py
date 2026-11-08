def mul(a, b):
    result = 0
    while b:
        if b & 1:
            result = result ^ a
        a = a << 1
        if a & 256:
            a = a ^ 283
        b = b >> 1
    return result & 255


def make_sbox():
    sbox = []
    for value in range(256):
        inverse = 0
        if value != 0:
            inverse = 1
            power = 254
            base = value
            while power:
                if power & 1:
                    inverse = mul(inverse, base)
                base = mul(base, base)
                power = power >> 1
        transformed = inverse
        for shift in range(1, 5):
            transformed = transformed ^ (((inverse << shift) | (inverse >> (8 - shift))) & 255)
        sbox.append((transformed ^ 99) & 255)
    return sbox


def sub_word(word, sbox):
    return (
        (sbox[(word >> 24) & 255] << 24)
        | (sbox[(word >> 16) & 255] << 16)
        | (sbox[(word >> 8) & 255] << 8)
        | sbox[word & 255]
    )


def init():
    return {
        "busy": 0,
        "out_valid": 0,
        "rnd": 0,
        "ct": 0,
        "rk": 0,
        "sbox": make_sbox(),
    }


def step(state, inputs):
    if inputs.get("rst", 0):
        state["busy"] = 0
        state["out_valid"] = 0
        state["rnd"] = 0
        state["ct"] = 0
        state["rk"] = 0
    else:
        busy = state["busy"]
        out_valid = state["out_valid"]
        rnd = state["rnd"]
        ct = state["ct"]
        rk = state["rk"]
        last = int(rnd == 10)

        if busy:
            rk = inputs.get("key_next", 0) & ((1 << 128) - 1)
            if rnd == 0:
                rnd = 1
            else:
                ct = inputs.get("round_out", 0) & ((1 << 128) - 1)
                if rnd == 10:
                    busy = 0
                    out_valid = 1
                    rnd = 0
                else:
                    rnd = rnd + 1
        elif out_valid:
            if inputs.get("out_ready", 0):
                out_valid = 0
        elif inputs.get("in_valid", 0):
            key = inputs.get("key", 0) & ((1 << 128) - 1)
            pt = inputs.get("pt", 0) & ((1 << 128) - 1)
            ct = (pt ^ key) & ((1 << 128) - 1)
            rk = key
            rnd = 0
            busy = 1

        state["busy"] = busy
        state["out_valid"] = out_valid
        state["rnd"] = rnd
        state["ct"] = ct
        state["rk"] = rk

    rnd = state["rnd"]
    rcon_values = (1, 2, 4, 8, 16, 32, 64, 128, 27, 54)
    rcon = 0
    if rnd < 10:
        rcon = rcon_values[rnd]

    outputs = {
        "in_ready": int(not state["busy"] and not state["out_valid"]),
        "out_valid": state["out_valid"],
        "ct": state["ct"] & ((1 << 128) - 1),
        "rk": state["rk"] & ((1 << 128) - 1),
        "rcon": rcon,
        "last": int(rnd == 10),
    }
    return state, outputs