def gf_mul(a, b):
    result = 0
    x = a
    y = b
    for i in range(8):
        if y & 1:
            result = result ^ x
        high = x & 128
        x = (x << 1) & 255
        if high:
            x = x ^ 27
        y = y >> 1
    return result


def make_sbox():
    sbox = []
    for value in range(256):
        inverse = 0
        if value != 0:
            inverse = 1
            base = value
            exponent = 254
            while exponent:
                if exponent & 1:
                    inverse = gf_mul(inverse, base)
                base = gf_mul(base, base)
                exponent = exponent >> 1
        x = inverse
        y = x ^ ((x << 1) | (x >> 7))
        y = y ^ ((x << 2) | (x >> 6))
        y = y ^ ((x << 3) | (x >> 5))
        y = y ^ ((x << 4) | (x >> 4))
        sbox.append((y ^ 99) & 255)
    return sbox


def unpack_bytes(value):
    result = []
    for index in range(16):
        shift = 120 - 8 * index
        result.append((value >> shift) & 255)
    return result


def pack_bytes(values):
    result = 0
    for value in values:
        result = (result << 8) | (value & 255)
    return result


def aes_round(state_bytes, key_bytes, final_round, sbox):
    substituted = []
    for index in range(16):
        substituted.append(sbox[state_bytes[index]])

    shifted = [0] * 16
    for row in range(4):
        for column in range(4):
            shifted[row + 4 * column] = substituted[row + 4 * ((column + row) % 4)]

    mixed = [0] * 16
    for column in range(4):
        base = 4 * column
        a0 = shifted[base]
        a1 = shifted[base + 1]
        a2 = shifted[base + 2]
        a3 = shifted[base + 3]
        if final_round:
            mixed[base] = a0
            mixed[base + 1] = a1
            mixed[base + 2] = a2
            mixed[base + 3] = a3
        else:
            mixed[base] = gf_mul(a0, 2) ^ gf_mul(a1, 3) ^ a2 ^ a3
            mixed[base + 1] = a0 ^ gf_mul(a1, 2) ^ gf_mul(a2, 3) ^ a3
            mixed[base + 2] = a0 ^ a1 ^ gf_mul(a2, 2) ^ gf_mul(a3, 3)
            mixed[base + 3] = gf_mul(a0, 3) ^ a1 ^ a2 ^ gf_mul(a3, 2)

    result = []
    for index in range(16):
        result.append(mixed[index] ^ key_bytes[index])
    return result


def schedule_step(key_bytes, rcon, sbox):
    rotated = [key_bytes[13], key_bytes[14], key_bytes[15], key_bytes[12]]
    transformed = []
    for value in rotated:
        transformed.append(sbox[value])
    transformed[0] = transformed[0] ^ rcon

    result = [0] * 16
    for index in range(4):
        result[index] = key_bytes[index] ^ transformed[index]
    for index in range(4, 16):
        result[index] = key_bytes[index] ^ result[index - 4]
    return result


def init():
    return {
        "busy": 0,
        "out_valid": 0,
        "rnd": 0,
        "ct": 0,
        "rk": 0,
        "sbox": make_sbox(),
        "rcons": [1, 2, 4, 8, 16, 32, 64, 128, 27, 54, 0]
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
        sbox = state["sbox"]
        rcons = state["rcons"]

        if busy:
            next_rk = schedule_step(unpack_bytes(rk), rcons[rnd], sbox)
            state["rk"] = pack_bytes(next_rk)
            if rnd == 0:
                state["rnd"] = 1
            else:
                next_ct = aes_round(
                    unpack_bytes(ct),
                    unpack_bytes(rk),
                    rnd == 10,
                    sbox
                )
                state["ct"] = pack_bytes(next_ct)
                if rnd == 10:
                    state["busy"] = 0
                    state["out_valid"] = 1
                    state["rnd"] = 0
                else:
                    state["rnd"] = rnd + 1
        elif out_valid:
            if inputs.get("out_ready", 0):
                state["out_valid"] = 0
        elif inputs.get("in_valid", 0):
            state["ct"] = (inputs.get("pt", 0) ^ inputs.get("key", 0)) & ((1 << 128) - 1)
            state["rk"] = inputs.get("key", 0) & ((1 << 128) - 1)
            state["rnd"] = 0
            state["busy"] = 1

    rnd_now = state["rnd"]
    outputs = {
        "in_ready": int(not state["busy"] and not state["out_valid"]),
        "out_valid": state["out_valid"],
        "ct": state["ct"],
        "rk": state["rk"],
        "rcon": state["rcons"][rnd_now],
        "last": int(rnd_now == 10)
    }
    return state, outputs