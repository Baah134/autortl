def init():
    exp = []
    log = [0] * 256
    value = 1
    for i in range(255):
        exp.append(value)
        log[value] = i
        shifted = (value << 1) & 255
        if value & 128:
            shifted = shifted ^ 27
        value = shifted ^ value

    sbox = []
    for x in range(256):
        if x == 0:
            inv = 0
        else:
            index = 255 - log[x]
            if index == 255:
                index = 0
            inv = exp[index]

        rot1 = ((inv << 1) | (inv >> 7)) & 255
        rot2 = ((inv << 2) | (inv >> 6)) & 255
        rot3 = ((inv << 3) | (inv >> 5)) & 255
        rot4 = ((inv << 4) | (inv >> 4)) & 255
        sbox.append(inv ^ rot1 ^ rot2 ^ rot3 ^ rot4 ^ 99)

    return dict(sbox=sbox)


def step(state, inputs):
    key = int(inputs.get("key_in", 0)) & ((1 << 128) - 1)
    rcon = int(inputs.get("rcon", 0)) & 255
    sbox = state.get("sbox", [])

    w0 = (key >> 96) & 4294967295
    w1 = (key >> 64) & 4294967295
    w2 = (key >> 32) & 4294967295
    w3 = key & 4294967295

    b0 = (w3 >> 24) & 255
    b1 = (w3 >> 16) & 255
    b2 = (w3 >> 8) & 255
    b3 = w3 & 255

    temp = (
        (sbox[b1] << 24)
        | (sbox[b2] << 16)
        | (sbox[b3] << 8)
        | sbox[b0]
    )
    temp = temp ^ (rcon << 24)

    w4 = (w0 ^ temp) & 4294967295
    w5 = (w1 ^ w4) & 4294967295
    w6 = (w2 ^ w5) & 4294967295
    w7 = (w3 ^ w6) & 4294967295

    outputs = dict(key_out=((w4 << 96) | (w5 << 64) | (w6 << 32) | w7) & ((1 << 128) - 1))
    return state, outputs