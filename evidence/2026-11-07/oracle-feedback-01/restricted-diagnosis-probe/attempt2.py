def init():
    sbox = [0] * 256
    log = [0] * 256
    alog = [0] * 510

    value = 1
    for i in range(255):
        alog[i] = value
        log[value] = i
        value = value << 1
        if value & 256:
            value = value ^ 283

    for i in range(255, 510):
        alog[i] = alog[i - 255]

    for i in range(256):
        if i == 0:
            inverse = 0
        else:
            inverse = alog[255 - log[i]]
        result = inverse
        result = result ^ (((inverse << 1) | (inverse >> 7)) & 255)
        result = result ^ (((inverse << 2) | (inverse >> 6)) & 255)
        result = result ^ (((inverse << 3) | (inverse >> 5)) & 255)
        result = result ^ (((inverse << 4) | (inverse >> 4)) & 255)
        sbox[i] = result ^ 99

    return dict(
        busy=0,
        out_valid=0,
        rnd=0,
        ct=0,
        rk=0,
        sbox=sbox,
        rcon=[1, 2, 4, 8, 16, 32, 64, 128, 27, 54, 0, 0, 0, 0, 0, 0],
    )


def step(state, inputs):
    mask = 4294967295
    byte_mask = 255
    block_mask = (1 << 128) - 1

    def sub_word(word):
        table = state["sbox"]
        result = 0
        for i in range(4):
            shift = 24 - 8 * i
            result = (result << 8) | table[(word >> shift) & byte_mask]
        return result

    def xtime(value):
        result = value << 1
        if value & 128:
            result = result ^ 283
        return result & byte_mask

    def aes_round(block, round_key, final_round):
        source = [0] * 16
        shifted = [0] * 16
        mixed = [0] * 16
        table = state["sbox"]

        for i in range(16):
            source[i] = (block >> (120 - 8 * i)) & byte_mask

        for row in range(4):
            for col in range(4):
                source_index = row + 4 * col
                target_index = row + 4 * ((col + row) & 3)
                shifted[target_index] = table[source[source_index]]

        if final_round:
            mixed = shifted
        else:
            for col in range(4):
                i = 4 * col
                a = shifted[i]
                b = shifted[i + 1]
                c = shifted[i + 2]
                d = shifted[i + 3]
                total = a ^ b ^ c ^ d
                mixed[i] = a ^ total ^ xtime(a ^ b)
                mixed[i + 1] = b ^ total ^ xtime(b ^ c)
                mixed[i + 2] = c ^ total ^ xtime(c ^ d)
                mixed[i + 3] = d ^ total ^ xtime(d ^ a)

        result = 0
        for i in range(16):
            key_byte = (round_key >> (120 - 8 * i)) & byte_mask
            result = (result << 8) | (mixed[i] ^ key_byte)
        return result & block_mask

    def next_key(round_key, round_constant):
        word = round_key & mask
        rotated = ((word << 8) | (word >> 24)) & mask
        transformed = sub_word(rotated) ^ (round_constant << 24)

        w0 = ((round_key >> 96) & mask) ^ transformed
        w1 = ((round_key >> 64) & mask) ^ w0
        w2 = ((round_key >> 32) & mask) ^ w1
        w3 = word ^ w2
        return ((w0 << 96) | (w1 << 64) | (w2 << 32) | w3) & block_mask

    rst = inputs.get("rst", 0)
    if rst:
        state["busy"] = 0
        state["out_valid"] = 0
        state["rnd"] = 0
        state["ct"] = 0
        state["rk"] = 0
    elif state["busy"]:
        round_index = state["rnd"]
        round_constant = state["rcon"][round_index]
        next_ct = aes_round(state["ct"], state["rk"], round_index == 10)
        next_rk = next_key(state["rk"], round_constant)
        state["rk"] = next_rk
        if round_index == 0:
            state["rnd"] = 1
        else:
            state["ct"] = next_ct
            if round_index == 10:
                state["busy"] = 0
                state["out_valid"] = 1
                state["rnd"] = 0
            else:
                state["rnd"] = round_index + 1
    elif state["out_valid"]:
        if inputs.get("out_ready", 0):
            state["out_valid"] = 0
    elif inputs.get("in_valid", 0):
        state["ct"] = (inputs.get("pt", 0) ^ inputs.get("key", 0)) & block_mask
        state["rk"] = inputs.get("key", 0) & block_mask
        state["rnd"] = 0
        state["busy"] = 1

    rnd = state["rnd"]
    outputs = dict(
        in_ready=1 if state["busy"] == 0 and state["out_valid"] == 0 else 0,
        out_valid=state["out_valid"],
        ct=state["ct"] & block_mask,
        rk=state["rk"] & block_mask,
        rcon=state["rcon"][rnd],
        last=1 if rnd == 10 else 0,
    )
    return state, outputs