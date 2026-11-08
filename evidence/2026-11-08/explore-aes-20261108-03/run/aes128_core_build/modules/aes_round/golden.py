def init():
    powers = [0] * 512
    logs = [0] * 256
    value = 1

    for exponent in range(255):
        powers[exponent] = value
        logs[value] = exponent
        value = value << 1
        if value & 256:
            value = value ^ 283

    for exponent in range(255, 512):
        powers[exponent] = powers[exponent - 255]

    sbox = [0] * 256
    for byte in range(256):
        inverse = 0
        if byte != 0:
            inverse = powers[(255 - logs[byte]) % 255]

        rotated1 = ((inverse << 1) | (inverse >> 7)) & 255
        rotated2 = ((inverse << 2) | (inverse >> 6)) & 255
        rotated3 = ((inverse << 3) | (inverse >> 5)) & 255
        rotated4 = ((inverse << 4) | (inverse >> 4)) & 255
        sbox[byte] = inverse ^ rotated1 ^ rotated2 ^ rotated3 ^ rotated4 ^ 99

    return dict(sbox=sbox)


def step(state, inputs):
    sbox = state.get("sbox", [])
    state_in = int(inputs.get("state_in", 0)) & ((1 << 128) - 1)
    round_key = int(inputs.get("round_key", 0)) & ((1 << 128) - 1)
    final_round = int(inputs.get("final_round", 0)) & 1

    substituted = [0] * 16
    for index in range(16):
        shift = 120 - 8 * index
        substituted[index] = sbox[(state_in >> shift) & 255]

    shifted = [0] * 16
    for row in range(4):
        for column in range(4):
            source_column = (column + row) % 4
            shifted[row + 4 * column] = substituted[row + 4 * source_column]

    result_bytes = shifted
    if final_round == 0:
        mixed = [0] * 16
        for column in range(4):
            base = 4 * column
            a0 = shifted[base]
            a1 = shifted[base + 1]
            a2 = shifted[base + 2]
            a3 = shifted[base + 3]

            d0 = ((a0 << 1) & 255) ^ (27 if a0 & 128 else 0)
            d1 = ((a1 << 1) & 255) ^ (27 if a1 & 128 else 0)
            d2 = ((a2 << 1) & 255) ^ (27 if a2 & 128 else 0)
            d3 = ((a3 << 1) & 255) ^ (27 if a3 & 128 else 0)

            mixed[base] = d0 ^ d1 ^ a1 ^ a2 ^ a3
            mixed[base + 1] = a0 ^ d1 ^ d2 ^ a2 ^ a3
            mixed[base + 2] = a0 ^ a1 ^ d2 ^ d3 ^ a3
            mixed[base + 3] = d0 ^ a0 ^ a1 ^ a2 ^ d3
        result_bytes = mixed

    result = 0
    for index in range(16):
        result = (result << 8) | result_bytes[index]

    outputs = dict(state_out=(result ^ round_key) & ((1 << 128) - 1))
    return state, outputs