"""Independent reference models for the harness winners, written from the frozen
specifications in curriculum/*/design_spec.json, not from the harness's
generated oracles.

Each model consumes one transaction (IN_BYTES bytes, least significant first)
and returns its result (OUT_BYTES bytes, least significant first). `wrong()`
returns a deliberately incorrect variant for negative controls: a correct
hardware result must fail against it.
"""
from __future__ import annotations

import math
import random


class Model:
    name = ""
    in_bytes = 1
    out_bytes = 1

    def __init__(self, wrong: bool = False):
        self.is_wrong = wrong
        self.reset()

    def reset(self):
        """Return to the state after a reset (stateless models: nothing)."""

    def step(self, tx: bytes) -> bytes:
        if len(tx) != self.in_bytes:
            raise ValueError(f"{self.name}: expected {self.in_bytes} input bytes, got {len(tx)}")
        result = self._compute(tx)
        if result < 0 or result >= 1 << (8 * self.out_bytes):
            raise ValueError(f"{self.name}: result {result} does not fit {self.out_bytes} bytes")
        return result.to_bytes(self.out_bytes, "little")

    def _compute(self, tx: bytes) -> int:
        raise NotImplementedError

    def leading(self) -> list[bytes]:
        """Edge-case transactions sent before the random ones."""
        return []

    def random_tx(self, rng: random.Random) -> bytes:
        return bytes(rng.randrange(256) for _ in range(self.in_bytes))

    def stimulus(self, rng: random.Random, count: int) -> list[bytes]:
        lead = self.leading()[:count]
        return lead + [self.random_tx(rng) for _ in range(count - len(lead))]


def _signed8(value: int) -> int:
    return value - 256 if value & 0x80 else value


class Fir4(Model):
    """y = 3x[n] - 5x[n-1] + 7x[n-2] - 2x[n-3]; signed 8-bit in, 13-bit out,
    sign-extended to 16 bits. History is cleared by reset and only advances
    on accepted samples."""
    name, in_bytes, out_bytes = "fir4", 1, 2

    def reset(self):
        self.history = [0, 0, 0]

    def _compute(self, tx):
        x = _signed8(tx[0])
        c2 = 6 if self.is_wrong else 7
        full = 3 * x - 5 * self.history[0] + c2 * self.history[1] - 2 * self.history[2]
        self.history = [x] + self.history[:2]
        y = full & 0x1FFF
        y = y - 0x2000 if y & 0x1000 else y
        return y & 0xFFFF

    def leading(self):
        return [bytes([b & 0xFF]) for b in (127, -128, 127, -128, -1, 0, -128, 127, -128, 127)]


class Dot4(Model):
    """Unsigned exact a0*b0 + a1*b1 + a2*b2 + a3*b3 (0..260100), 18 bits.
    Byte order a0, b0, a1, b1, a2, b2, a3, b3."""
    in_bytes, out_bytes = 8, 3

    def _compute(self, tx):
        pairs = [(tx[2 * i], tx[2 * i + 1]) for i in range(4)]
        if self.is_wrong:
            pairs = pairs[:3]                       # drops the a3*b3 term
        return sum(a * b for a, b in pairs)

    def leading(self):
        return [bytes([255] * 8), bytes(8), bytes([255, 1] * 4), bytes([1, 255] * 4),
                bytes([128] * 8), bytes([255, 255, 0, 0, 255, 255, 0, 0]),
                bytes([0, 0, 255, 255, 0, 0, 255, 255])]


class ElasticDot4(Dot4):
    name = "elastic_dot4"


class Dot4Pipeline(Dot4):
    name = "dot4_pipeline"


class IterativeDivider(Model):
    """Unsigned 8-bit: quotient = dividend // divisor, remainder = dividend % divisor.
    Divide by zero: quotient = 0xFF and remainder = the dividend.
    Byte 0 = dividend, byte 1 = divisor; result byte 0 = quotient, byte 1 = remainder."""
    name, in_bytes, out_bytes = "iterative_divider", 2, 2

    def _compute(self, tx):
        dividend, divisor = tx[0], tx[1]
        if divisor == 0:
            quotient, remainder = 0xFF, dividend
        else:
            quotient, remainder = dividend // divisor, dividend % divisor
        if self.is_wrong:
            remainder = (remainder + 1) & 0xFF
        return quotient | remainder << 8

    def leading(self):
        cases = [(0, 0), (255, 0), (1, 0), (255, 1), (255, 255), (0, 1), (0, 255),
                 (7, 7), (5, 9), (200, 13), (128, 2), (255, 16), (254, 255), (129, 128)]
        return [bytes(case) for case in cases]

    def random_tx(self, rng):
        divisor = 0 if rng.randrange(16) == 0 else rng.randrange(256)
        return bytes([rng.randrange(256), divisor])


class PacketFifo(Model):
    """Order-preserving identity on (data, last). Byte 0 = data; byte 1 is the
    last marker, and any nonzero value sets last. The result's byte 1 is 0 or 1."""
    name, in_bytes, out_bytes = "packet_fifo", 2, 2

    def _compute(self, tx):
        last = 1 if tx[1] else 0
        if self.is_wrong:
            last ^= 1
        return tx[0] | last << 8

    def leading(self):
        return [bytes([0, 0]), bytes([255, 1]), bytes([1, 0]), bytes([0, 1]), bytes([0xA5, 0x80]),
                bytes([0x5A, 0x02]), bytes([0xFF, 0xFF]), bytes([0x00, 0x40]), bytes([0xFF, 0])]

    def random_tx(self, rng):
        marker = 0 if rng.randrange(2) else rng.randrange(1, 256)
        return bytes([rng.randrange(256), marker])


class SyncFifo(Model):
    """Order-preserving identity on 8-bit words."""
    name, in_bytes, out_bytes = "sync_fifo", 1, 1

    def _compute(self, tx):
        return tx[0] ^ 1 if self.is_wrong else tx[0]

    def leading(self):
        return [bytes([b]) for b in (0x00, 0xFF, 0xA5, 0x5A, 0x01, 0x80, 0x7F, 0xFE)]


def _signed(value: int, bits: int) -> int:
    """The two's complement value of the low `bits` bits of `value`."""
    value &= (1 << bits) - 1
    return value - (1 << bits) if value >> (bits - 1) else value


# ---------------------------------------------------------------- AES-128

def _gf_mul(a: int, b: int) -> int:
    """Multiply in GF(2^8) modulo x^8 + x^4 + x^3 + x + 1."""
    product = 0
    for _ in range(8):
        if b & 1:
            product ^= a
        a = (a << 1) ^ 0x11B if a & 0x80 else a << 1
        b >>= 1
    return product


def _gf_inverse(a: int) -> int:
    """a^254 = a^-1 in GF(2^8) (0 maps to 0), by square and multiply."""
    result, power, exponent = 1, a, 254
    while exponent:
        if exponent & 1:
            result = _gf_mul(result, power)
        power = _gf_mul(power, power)
        exponent >>= 1
    return result if a else 0


def _rotl8(value: int, shift: int) -> int:
    return ((value << shift) | (value >> (8 - shift))) & 0xFF


def aes_sbox() -> list[int]:
    """FIPS-197 S-box computed from its definition: GF(2^8) inverse, then the
    affine map b ^ rotl(b,1) ^ rotl(b,2) ^ rotl(b,3) ^ rotl(b,4) ^ 0x63."""
    table = []
    for value in range(256):
        inv = _gf_inverse(value)
        table.append(inv ^ _rotl8(inv, 1) ^ _rotl8(inv, 2) ^ _rotl8(inv, 3) ^ _rotl8(inv, 4) ^ 0x63)
    return table


AES_SBOX = aes_sbox()


def aes_key_step(key: bytes, rcon: int, sbox=AES_SBOX) -> bytes:
    """One AES-128 KeyExpansion step (FIPS-197 5.2): {w0..w3} to {w4..w7}."""
    words = [list(key[4 * i:4 * i + 4]) for i in range(4)]
    temp = [sbox[b] for b in words[3][1:] + words[3][:1]]   # SubWord(RotWord(w3))
    temp[0] ^= rcon
    for i in range(4):
        temp = [a ^ b for a, b in zip(words[i], temp)]      # w4 = w0 ^ temp, w5 = w1 ^ w4, ...
        words[i] = temp
    return bytes(sum(words, []))


def aes_round(state: bytes, round_key: bytes, final: bool, sbox=AES_SBOX) -> bytes:
    """One encryption round. Byte n sits at row n % 4, column n // 4 of the state."""
    s = [sbox[b] for b in state]                                                  # SubBytes
    s = [s[row + 4 * ((col + row) % 4)] for col in range(4) for row in range(4)]  # ShiftRows
    if not final:                                                                 # MixColumns
        mixed = []
        for col in range(4):
            a0, a1, a2, a3 = s[4 * col:4 * col + 4]
            mixed += [_gf_mul(2, a0) ^ _gf_mul(3, a1) ^ a2 ^ a3,
                      a0 ^ _gf_mul(2, a1) ^ _gf_mul(3, a2) ^ a3,
                      a0 ^ a1 ^ _gf_mul(2, a2) ^ _gf_mul(3, a3),
                      _gf_mul(3, a0) ^ a1 ^ a2 ^ _gf_mul(2, a3)]
        s = mixed
    return bytes(a ^ k for a, k in zip(s, round_key))                             # AddRoundKey


def aes128_encrypt(key: bytes, plaintext: bytes, sbox=AES_SBOX) -> bytes:
    """FIPS-197 AES-128 encryption of one block; blocks are byte strings in FIPS order."""
    state = bytes(p ^ k for p, k in zip(plaintext, key))
    round_key, rcon = bytes(key), 0x01
    for rnd in range(1, 11):
        round_key = aes_key_step(round_key, rcon, sbox)
        rcon = _gf_mul(rcon, 2)
        state = aes_round(state, round_key, rnd == 10, sbox)
    return state


class Aes128(Model):
    """AES-128 encryption (FIPS-197). Bytes 0..15 = the key and bytes 16..31 =
    the plaintext, each in FIPS byte order (byte 0 first, the most significant
    byte of the spec's big-endian 128-bit port). The 16 result bytes are the
    ciphertext in the same order. The wrong twin's S-box has two adjacent
    entries (0x52, 0x53) exchanged."""
    name, in_bytes, out_bytes = "aes128", 32, 16

    def _compute(self, tx):
        sbox = AES_SBOX
        if self.is_wrong:
            sbox = list(AES_SBOX)
            sbox[0x52], sbox[0x53] = sbox[0x53], sbox[0x52]
        ciphertext = aes128_encrypt(tx[:16], tx[16:], sbox)
        return int.from_bytes(ciphertext, "little")         # step() emits byte 0 first

    def leading(self):
        known = [  # (key, plaintext): FIPS-197 C.1 and Appendix B, then AESAVS corners
            ("000102030405060708090a0b0c0d0e0f", "00112233445566778899aabbccddeeff"),
            ("2b7e151628aed2a6abf7158809cf4f3c", "3243f6a8885a308d313198a2e0370734"),
            ("00" * 16, "00" * 16),
            ("ff" * 16, "00" * 16),
            ("00" * 16, "ff" * 16),
            ("ff" * 16, "ff" * 16),
            ("80" + "00" * 15, "00" * 16),
            ("00" * 16, "80" + "00" * 15),
            ("00" * 15 + "01", "00" * 15 + "01"),
            ("10a58869d74be5a374cf867cfb473859", "00" * 16),
        ]
        return [bytes.fromhex(k) + bytes.fromhex(p) for k, p in known]


# ---------------------------------------------------------------- CORDIC

CORDIC_ITERATIONS = 16


def cordic_atan_table() -> list[int]:
    """round(atan(2^-i) / (2 pi) * 2^20), round half up, i = 0..15 (2^-20 turn units)."""
    return [math.floor(math.atan(2.0 ** -i) / (2 * math.pi) * (1 << 20) + 0.5)
            for i in range(CORDIC_ITERATIONS)]


def cordic_gain() -> int:
    """K = round(2^16 * prod_{i=0..15} 1/sqrt(1 + 2^-2i))."""
    product = 1.0
    for i in range(CORDIC_ITERATIONS):
        product /= math.sqrt(1.0 + 2.0 ** (-2 * i))
    return math.floor((1 << 16) * product + 0.5)


CORDIC_ATAN = cordic_atan_table()
CORDIC_K = cordic_gain()


def cordic_prerot(angle: int) -> tuple[int, int]:
    """(x0, z0) as unsigned 18- and 20-bit patterns: fold quadrants 01 and 10 by half a turn."""
    x0, reduced = CORDIC_K, angle & 0xFFFF
    if (reduced >> 15) & 1 != (reduced >> 14) & 1:
        x0, reduced = -CORDIC_K, reduced ^ 0x8000
    return x0 & 0x3FFFF, (_signed(reduced, 16) * 16) & 0xFFFFF


def cordic_rotate(x0: int, z0: int, table, iterations: int = CORDIC_ITERATIONS) -> tuple[int, int]:
    """The engine's micro-rotations from (x0, y = 0, z0); returns (x, y) as 18-bit patterns.
    `table[i]` is the atan value presented at iteration i."""
    x, y, z = _signed(x0, 18), 0, _signed(z0, 20)
    for i in range(iterations):
        xs, ys = x >> i, y >> i                    # Python >> on ints is arithmetic (floor)
        if z >= 0:
            x, y, z = _signed(x - ys, 18), _signed(y + xs, 18), _signed(z - table[i], 20)
        else:
            x, y, z = _signed(x + ys, 18), _signed(y - xs, 18), _signed(z + table[i], 20)
    return x & 0x3FFFF, y & 0x3FFFF


def cordic_out(x: int, y: int) -> tuple[int, int]:
    """Q2.16 to Q2.14 with round half up: ((v + 2) >>> 2), low 16 bits. Returns (cos, sin)."""
    return ((_signed(x, 18) + 2) >> 2) & 0xFFFF, ((_signed(y, 18) + 2) >> 2) & 0xFFFF


def cordic_sincos(angle: int, table=CORDIC_ATAN) -> tuple[int, int]:
    """(cos_out, sin_out) of the spec's contract, bit exact, as unsigned 16-bit patterns."""
    x0, z0 = cordic_prerot(angle)
    return cordic_out(*cordic_rotate(x0, z0, table))


class Cordic(Model):
    """16-iteration CORDIC sine and cosine. Bytes 0..1 = the 16-bit binary angle
    (one turn = 2^16), least significant first. Result bytes 0..1 = sin_out and
    bytes 2..3 = cos_out, each Q2.14 two's complement, least significant first
    (the 32-bit word {cos_out, sin_out}). The wrong twin's arctangent entry 3
    is 20735 (digits transposed) instead of 20753."""
    name, in_bytes, out_bytes = "cordic", 2, 4

    def _compute(self, tx):
        table = CORDIC_ATAN
        if self.is_wrong:
            table = list(CORDIC_ATAN)
            table[3] = 20735
        cos_out, sin_out = cordic_sincos(int.from_bytes(tx, "little"), table)
        return sin_out | cos_out << 16

    def leading(self):
        # Quadrant and octant boundaries, both sides of each fold, the circle's ends.
        angles = (0x0000, 0x4000, 0x8000, 0xC000, 0x3FFF, 0x4001, 0x7FFF, 0x8001, 0xBFFF, 0xC001,
                  0xFFFF, 0x0001, 0x2000, 0x6000, 0xA000, 0xE000, 0x1555, 0x2AAB, 0x5555, 0xD555)
        return [a.to_bytes(2, "little") for a in angles]


# ---------------------------------------------------------------- 16-tap FIR

FIR16_COEFFICIENTS = (-6, -20, -24, 18, 110, 226, 330, 390, 390, 330, 226, 110, 18, -24, -20, -6)


class Fir16Sym(Model):
    """Direct-form 16-tap FIR: acc = sum_k h[k] * x[n-k] over accepted signed
    16-bit samples (zeros before the first since reset), r = floor((acc + 1024)
    / 2048), saturated to [-32768, 32767]. Byte 0..1 = the sample and result
    bytes 0..1 = the output, both least significant first. History is cleared
    by reset and only advances on accepted samples. The wrong twin flips the
    sign of tap h[3] only."""
    name, in_bytes, out_bytes = "fir16_sym", 2, 2

    def reset(self):
        self.history = [0] * 15                   # x[n-1] .. x[n-15]

    def _compute(self, tx):
        x = int.from_bytes(tx, "little", signed=True)
        taps = list(FIR16_COEFFICIENTS)
        if self.is_wrong:
            taps[3] = -taps[3]
        window = [x] + self.history
        acc = sum(h * v for h, v in zip(taps, window))
        self.history = window[:15]
        r = (acc + 1024) >> 11                    # floor division: round half up
        r = max(-32768, min(32767, r))
        return r & 0xFFFF

    def leading(self):
        samples = []
        for impulse in (32767, -32768, 512, -512, 1, -1):     # impulse responses; +-512 hit rounding ties
            samples += [impulse] + [0] * 16
        samples += [32767] * 20 + [-32768] * 20                # both rails saturate
        samples += [-32768 if (i <= 2 or i >= 13) else 32767 for i in range(16)]   # |acc| maximum
        samples += [32767 if (i <= 2 or i >= 13) else -32768 for i in range(16)]
        samples += [(32767, -32768)[i % 2] for i in range(32)]                    # alternating extremes
        return [(s & 0xFFFF).to_bytes(2, "little") for s in samples]

    def random_tx(self, rng):
        if rng.randrange(4) == 0:
            return rng.choice((32767, -32768 & 0xFFFF)).to_bytes(2, "little")
        return bytes([rng.randrange(256), rng.randrange(256)])


MODELS = {cls.name: cls for cls in (Fir4, ElasticDot4, Dot4Pipeline, IterativeDivider,
                                     PacketFifo, SyncFifo, Aes128, Cordic, Fir16Sym)}


def model_for(name: str, wrong: bool = False) -> Model:
    try:
        return MODELS[name](wrong=wrong)
    except KeyError:
        raise KeyError(f"no model for design {name!r}; known: {', '.join(MODELS)}") from None
