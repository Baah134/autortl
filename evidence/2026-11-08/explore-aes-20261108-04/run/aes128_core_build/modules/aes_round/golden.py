def gf_mul(a, b):
    result = 0
    while b:
        if b & 1:
            result = result ^ a
        a = a << 1
        if a & 256:
            a = a ^ 283
        b = b >> 1
    return result & 255


def rotl8(value, amount):
    return ((value << amount) | (value >> (8 - amount))) & 255


def init():
    # Build powers of 3, a primitive generator for AES's field.
    powers = list(range(255))
    logs = list(range(256))
    value = 1
    for exponent in range(255):
        powers[exponent] = value
        logs[value] = exponent
        value = gf_mul(value, 3)

    # Build inverses by lookup, then apply the AES affine transformation.
    sbox = list(range(256))
    for value in range(256):
        inverse = 0
        if value != 0:
            inverse = powers[(255 - logs[value]) % 255]
        sbox[value] = (
            inverse
            ^ rotl8(inverse, 1)
            ^ rotl8(inverse, 2)
            ^ rotl8(inverse, 3)
            ^ rotl8(inverse, 4)
            ^ 99
        )

    return dict(sbox=sbox)


def step(state, inputs):
    mask = (1 << 128) - 1
    state_in = inputs.get("state_in", 0) & mask
    round_key = inputs.get("round_key", 0) & mask
    final_round = inputs.get("final_round", 0)
    sbox = state.get("sbox")

    values = list(range(16))
    for index in range(16):
        values[index] = sbox[(state_in >> (120 - 8 * index)) & 255]

    shifted = list(range(16))
    for row in range(4):
        for column in range(4):
            shifted[row + 4 * column] = values[row + 4 * ((column + row) % 4)]

    mixed = list(range(16))
    if final_round:
        mixed = shifted
    else:
        for column in range(4):
            base = 4 * column
            a0 = shifted[base]
            a1 = shifted[base + 1]
            a2 = shifted[base + 2]
            a3 = shifted[base + 3]
            mixed[base] = gf_mul(a0, 2) ^ gf_mul(a1, 3) ^ a2 ^ a3
            mixed[base + 1] = a0 ^ gf_mul(a1, 2) ^ gf_mul(a2, 3) ^ a3
            mixed[base + 2] = a0 ^ a1 ^ gf_mul(a2, 2) ^ gf_mul(a3, 3)
            mixed[base + 3] = gf_mul(a0, 3) ^ a1 ^ a2 ^ gf_mul(a3, 2)

    output = 0
    for index in range(16):
        output = (output << 8) | (
            mixed[index] ^ ((round_key >> (120 - 8 * index)) & 255)
        )

    return state, {"state_out": output & mask}