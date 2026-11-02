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


# ---------------------------------------------------------------- CRC-16 stream

def crc16_update(state: int, byte: int, poly: int = 0x1021) -> int:
    """One CRC-16 byte step, unreflected, most significant bit first: the
    spec's S = S ^ (D << 8), then eight shift-and-conditional-XOR steps."""
    state ^= byte << 8
    for _ in range(8):
        state = ((state << 1) ^ poly) if state & 0x8000 else (state << 1)
        state &= 0xFFFF
    return state


def crc16_ccitt_false(data: bytes, init: int = 0xFFFF) -> int:
    """CRC-16/CCITT-FALSE: width 16, poly 0x1021, init 0xFFFF, no reflection, no final XOR."""
    state = init
    for byte in data:
        state = crc16_update(state, byte)
    return state


class Crc16Stream(Model):
    """Streaming CRC-16/CCITT-FALSE, one output per accepted byte. Byte 0 = the
    data byte; byte 1 = the last marker (any nonzero value sets in_last). Result bytes
    0..1 = out_crc (least significant first), the CRC of the current frame up
    to and including this byte; result byte 2 = out_last (0 or 1). The byte
    after a last byte starts a new frame from 0xFFFF; reset restarts the frame.
    The wrong twin starts every frame from 0x0000 instead."""
    name, in_bytes, out_bytes = "crc16_stream", 2, 3

    def reset(self):
        self.frame = self._init()

    def _init(self):
        return 0x0000 if self.is_wrong else 0xFFFF

    def _compute(self, tx):
        last = 1 if tx[1] else 0
        crc = crc16_update(self.frame, tx[0])
        self.frame = self._init() if last else crc
        return crc | last << 16

    def leading(self):
        frames = [b"123456789", b"\x00", b"\xff", bytes(12), b"\xff" * 12,
                  bytes(range(1, 17)), b"\x80", b"\x01"]
        out = []
        for frame in frames:
            out += [bytes([b, 0]) for b in frame[:-1]] + [bytes([frame[-1], 1])]
        # every bit of the marker byte counts: frames ended by 0x80 and by 0x02
        out += [bytes([0x31, 0x00]), bytes([0x32, 0x80]), bytes([0x33, 0x02])]
        return out

    def random_tx(self, rng):
        marker = rng.randrange(1, 256) if rng.randrange(8) == 0 else 0
        return bytes([rng.randrange(256), marker])


# ---------------------------------------------------------------- SPI master

def spi_exchange(master_byte: int, slave_byte: int, msb_first: bool = True) -> tuple[int, int]:
    """One 8-bit full-duplex SPI transfer, bit by bit: on each of eight SCLK
    pulses the master shifts out one bit of master_byte on MOSI and the slave one
    bit of slave_byte on MISO; each side shifts what it samples into the bottom
    of its receive register. Returns (what the master received, what the slave
    received)."""
    order = range(7, -1, -1) if msb_first else range(8)
    master_rx = slave_rx = 0
    for bit in order:
        mosi, miso = (master_byte >> bit) & 1, (slave_byte >> bit) & 1
        master_rx = (master_rx << 1) | miso
        slave_rx = (slave_rx << 1) | mosi
    return master_rx, slave_rx


class SpiMaster(Model):
    """SPI master, mode 0, 8 bits MSB first, against the adapter's mode-0 slave.
    Byte 0 = cmd_data (sent on MOSI); byte 1 = the byte the slave returns on
    MISO for this transfer. Result byte 0 = rsp_data (what the master
    received), byte 1 = what the slave captured from MOSI. The wrong twin
    shifts least significant bit first."""
    name, in_bytes, out_bytes = "spi_master", 2, 2

    def _compute(self, tx):
        rsp, captured = spi_exchange(tx[0], tx[1], msb_first=not self.is_wrong)
        return rsp | captured << 8

    def leading(self):
        cases = [(0x00, 0x00), (0xFF, 0xFF), (0xA5, 0xFF), (0x3C, 0x00), (0x80, 0x01), (0x01, 0x80),
                 (0xAA, 0x55), (0x55, 0xAA), (0x0F, 0xF0), (0x12, 0x34), (0xC3, 0x96)]
        return [bytes(case) for case in cases]


# ---------------------------------------------------------------- RV32I core
#
# An ISA-level interpreter for the subset the spec names (curriculum/tier6/
# rv32i_core_build), written from the RV32I definition plus the spec's resolved
# choices: word-only LW/SW whose funct3 is ignored, instruction word pc[7:2] and
# data word address[6:2] (higher bits alias, bits [1:0] ignored), branch funct3
# 010/011 never taken, every other opcode (FENCE, SYSTEM, unknown) a
# no-operation, and an rf write reported for every writing instruction even
# when rd = 0. Cycles: 4 per instruction, 5 for a store, 6 for a load.

RV_PROGRAM_WORDS = 8           # 32 input bytes
RV_RETIRES = 32                # instructions retired per transaction
RV_SHADOW = range(1, 7)        # x1..x6 are reported
MASK32 = 0xFFFFFFFF


def _sext(value: int, bits: int) -> int:
    return _signed(value, bits) & MASK32


def rv_fold(sig: int, word: int) -> int:
    """The adapter's trace signature step: rotate left by 5, then XOR."""
    return (((sig << 5) | (sig >> 27)) ^ word) & MASK32


def rv_run(program, retires: int = RV_RETIRES, slt_unsigned: bool = False) -> dict:
    """Run `program` (up to 64 words at word 0, zeros elsewhere) from reset for
    `retires` instructions. Returns the final registers, data memory, cycle
    count and the trace signature the adapter computes:
      store (in M):  sig = fold(fold(sig, data word index), store data)
      retire (in W): sig = fold(sig, pc); then if the instruction writes,
                     fold(32 | rd) and fold(value), else fold(0) twice."""
    imem = list(program) + [0] * (64 - len(program))
    x, dmem = [0] * 32, [0] * 32
    pc = sig = cycles = 0
    for _ in range(retires):
        instr = imem[(pc >> 2) & 63]
        opcode, rd, f3 = instr & 0x7F, (instr >> 7) & 31, (instr >> 12) & 7
        rs1, rs2, bit30 = x[(instr >> 15) & 31], x[(instr >> 20) & 31], (instr >> 30) & 1
        imm_i = _sext(instr >> 20, 12)
        imm_s = _sext(((instr >> 25) << 5) | ((instr >> 7) & 31), 12)
        imm_b = _sext((((instr >> 31) & 1) << 12) | (((instr >> 7) & 1) << 11) |
                      (((instr >> 25) & 63) << 5) | (((instr >> 8) & 15) << 1), 13)
        imm_u = instr & 0xFFFFF000
        imm_j = _sext((((instr >> 31) & 1) << 20) | (((instr >> 12) & 255) << 12) |
                      (((instr >> 20) & 1) << 11) | (((instr >> 21) & 1023) << 1), 21)
        link, next_pc, value, cost = (pc + 4) & MASK32, (pc + 4) & MASK32, None, 4
        if opcode in (0x33, 0x13):                          # OP, OP-IMM
            a, b = rs1, (rs2 if opcode == 0x33 else imm_i)
            alt = bit30 and (opcode == 0x33 or f3 == 5)     # SUB / SRA / SRAI
            shamt = b & 31
            if f3 == 0:
                value = a - b if (alt and opcode == 0x33) else a + b
            elif f3 == 1:
                value = a << shamt
            elif f3 == 2:
                value = int(a < b) if slt_unsigned else int(_signed(a, 32) < _signed(b, 32))
            elif f3 == 3:
                value = int(a < b)
            elif f3 == 4:
                value = a ^ b
            elif f3 == 5:
                value = (_signed(a, 32) >> shamt) if alt else (a >> shamt)
            elif f3 == 6:
                value = a | b
            else:
                value = a & b
        elif opcode == 0x37:                                # LUI
            value = imm_u
        elif opcode == 0x17:                                # AUIPC
            value = pc + imm_u
        elif opcode == 0x6F:                                # JAL
            value, next_pc = link, (pc + imm_j) & MASK32
        elif opcode == 0x67:                                # JALR (funct3 ignored)
            value, next_pc = link, (rs1 + imm_i) & MASK32 & ~1
        elif opcode == 0x63:                                # BRANCH
            s1, s2 = _signed(rs1, 32), _signed(rs2, 32)
            taken = {0: rs1 == rs2, 1: rs1 != rs2, 4: s1 < s2, 5: s1 >= s2,
                     6: rs1 < rs2, 7: rs1 >= rs2}.get(f3, False)
            if taken:
                next_pc = (pc + imm_b) & MASK32
        elif opcode == 0x03:                                # LOAD: always a word
            value, cost = dmem[(((rs1 + imm_i) & MASK32) >> 2) & 31], 6
        elif opcode == 0x23:                                # STORE: always a word
            index = (((rs1 + imm_s) & MASK32) >> 2) & 31
            dmem[index], cost = rs2, 5
            sig = rv_fold(rv_fold(sig, index), rs2)
        sig = rv_fold(sig, pc)
        if value is None:
            sig = rv_fold(rv_fold(sig, 0), 0)
        else:
            value &= MASK32
            sig = rv_fold(rv_fold(sig, 32 | rd), value)
            if rd:
                x[rd] = value
        cycles += cost
        pc = next_pc
    return {"x": x, "dmem": dmem, "pc": pc, "cycles": cycles, "sig": sig}


# A small RV32I encoder for the stimulus (registers are numbers 0..31).
def rv_r(f7, rs2, rs1, f3, rd, op=0x33):
    return (f7 << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | op


def rv_i(imm, rs1, f3, rd, op=0x13):
    return ((imm & 0xFFF) << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | op


def rv_s(imm, rs2, rs1, f3=2, op=0x23):
    imm &= 0xFFF
    return ((imm >> 5) << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | ((imm & 31) << 7) | op


def rv_b(imm, rs2, rs1, f3, op=0x63):
    imm &= 0x1FFF
    return ((((imm >> 12) & 1) << 31) | (((imm >> 5) & 63) << 25) | (rs2 << 20) | (rs1 << 15) |
            (f3 << 12) | (((imm >> 1) & 15) << 8) | (((imm >> 11) & 1) << 7) | op)


def rv_u(imm20, rd, op=0x37):
    return ((imm20 & 0xFFFFF) << 12) | (rd << 7) | op


def rv_j(imm, rd, op=0x6F):
    imm &= 0x1FFFFF
    return ((((imm >> 20) & 1) << 31) | (((imm >> 1) & 1023) << 21) | (((imm >> 11) & 1) << 20) |
            (((imm >> 12) & 255) << 12) | (rd << 7) | op)


ADD, SUB, SLL, SLT, SLTU, XOR, SRL, SRA, OR, AND = (
    (0, 0), (0x20, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0x20, 5), (0, 6), (0, 7))
BEQ, BNE, BLT, BGE, BLTU, BGEU = 0, 1, 4, 5, 6, 7


def rv_op(kind, rd, rs1, rs2):
    f7, f3 = kind
    return rv_r(f7, rs2, rs1, f3, rd)


RV_DIRECTED = {
    # Signed and unsigned arithmetic and comparison; then 24 no-operations.
    "arith": [rv_i(-5, 0, 0, 1), rv_i(3, 0, 0, 2), rv_op(ADD, 3, 1, 2), rv_op(SUB, 4, 2, 1),
              rv_op(SLT, 5, 1, 2), rv_op(SLTU, 6, 1, 2), rv_i(0x400 | 1, 1, 5, 1),   # SRAI x1, x1, 1
              rv_op(XOR, 2, 2, 4)],
    # sum 5 + 4 + 3 + 2 + 1 in a backward loop, store, load it back, then JAL to itself.
    "loop": [rv_i(0, 0, 0, 1), rv_i(5, 0, 0, 2), rv_op(ADD, 1, 1, 2), rv_i(-1, 2, 0, 2),
             rv_b(-8, 0, 2, BNE), rv_s(8, 1, 0), rv_i(8, 0, 2, 3, op=0x03), rv_j(0, 4)],
    # Signed branches on 0x80000000 vs 1, AUIPC, JALR forward, JAL to itself.
    "branch": [rv_u(0x80000, 1), rv_i(1, 0, 0, 2), rv_b(8, 2, 1, BLT), rv_i(99, 0, 0, 3),
               rv_b(8, 2, 1, BGE), rv_u(1, 3, op=0x17), rv_i(28, 0, 0, 4, op=0x67), rv_j(0, 5)],
    # Word stores and loads with address aliasing and ignored low bits, then SLTI.
    "memory": [rv_i(0x123, 0, 0, 1), rv_i(-1, 0, 0, 2), rv_s(4, 1, 0), rv_s(132, 2, 0),
               rv_i(4, 0, 2, 3, op=0x03), rv_s(8, 1, 0), rv_i(11, 0, 2, 4, op=0x03), rv_i(0, 2, 2, 5)],
    # Shifts by register and immediate, shift amounts above 31, SLTIU against -1.
    "shift": [rv_u(0x80000, 1), rv_i(0x400 | 4, 1, 5, 2), rv_i(4, 1, 5, 3), rv_i(1, 2, 1, 4),
              rv_i(33, 0, 0, 5), rv_op(SLL, 6, 5, 5), rv_op(SRA, 1, 1, 5), rv_i(-1, 5, 3, 5)],
    # Unsigned branches on 0xFFFFFFFF vs 1 (BGEU skips word 4), a reserved
    # branch encoding (never taken), FENCE and ECALL as no-operations.
    "branch_u": [rv_i(-1, 0, 0, 1), rv_i(1, 0, 0, 2), rv_b(8, 2, 1, BLTU), rv_b(8, 2, 1, BGEU),
                 rv_i(7, 0, 0, 3), rv_b(8, 2, 1, 2), 0x0FF0000F, 0x00000073],
    "nops": [0] * 8,
}


def rv_random_program(rng: random.Random) -> list[int]:
    """Eight valid words with forward-only control flow, so the program runs
    off its end into the no-operations after word 7. Registers x0..x7; two
    seeding writes first, then three signed comparisons (SLT or SLTI) among six
    random instructions."""
    reg = lambda: rng.randrange(8)
    dst = lambda: rng.randrange(1, 8)
    words = []
    for _ in range(2):
        words.append(rv_u(rng.randrange(1 << 20), dst()) if rng.randrange(2)
                     else rv_i(rng.randrange(4096), reg(), 0, dst()))
    compare_slots = set(rng.sample(range(2, RV_PROGRAM_WORDS), 3))
    for index in range(2, RV_PROGRAM_WORDS):
        forward = 4 * rng.randrange(1, RV_PROGRAM_WORDS + 1 - index)   # to a later word, at most word 8
        if index in compare_slots:
            words.append(rv_op(SLT, dst(), reg(), reg()) if rng.randrange(2)
                         else rv_i(rng.randrange(4096), reg(), 2, dst()))
            continue
        kind = rng.randrange(10)
        if kind < 3:
            op = rng.choice((ADD, SUB, SLL, SLT, SLTU, XOR, SRL, SRA, OR, AND))
            words.append(rv_op(op, dst(), reg(), reg()))
        elif kind < 5:
            f3 = rng.choice((0, 2, 3, 4, 6, 7, 1, 5))
            if f3 == 1:                                                 # SLLI
                imm = rng.randrange(32)
            elif f3 == 5:                                               # SRLI or SRAI
                imm = rng.randrange(32) | rng.choice((0, 0x400))
            else:
                imm = rng.randrange(4096)
            words.append(rv_i(imm, reg(), f3, dst()))
        elif kind == 5:
            words.append(rv_u(rng.randrange(1 << 20), dst(), op=rng.choice((0x37, 0x17))))
        elif kind == 6:
            words.append(rv_s(4 * rng.randrange(-512, 512), reg(), 0))
        elif kind == 7:
            words.append(rv_i(4 * rng.randrange(-512, 512), 0, 2, dst(), op=0x03))
        elif kind == 8:
            words.append(rv_b(forward, reg(), reg(), rng.choice((BEQ, BNE, BLT, BGE, BLTU, BGEU))))
        else:
            words.append(rv_j(forward, reg()) if rng.randrange(2)
                         else rv_i(4 * index + forward, 0, 0, reg(), op=0x67))   # JALR x0-based
    return words


class Rv32iCore(Model):
    """RV32I subset core running one program per transaction. Bytes 4n..4n+3
    = instruction word n (n = 0..7, least significant byte first), loaded at
    word n after a reset of the core; words 8..63 stay zero (no-operations).
    The core then runs until it retires 32 instructions. Result: bytes 0..3 =
    the trace signature (see rv_run), bytes 4..7 = clock cycles from run to the
    32nd retirement inclusive, bytes 8..31 = the final x1..x6, each least
    significant byte first. The wrong twin treats SLT and SLTI as unsigned."""
    name, in_bytes, out_bytes = "rv32i_core", 32, 32

    def _compute(self, tx):
        program = [int.from_bytes(tx[4 * n:4 * n + 4], "little") for n in range(RV_PROGRAM_WORDS)]
        result = rv_run(program, slt_unsigned=self.is_wrong)
        words = [result["sig"], result["cycles"]] + [result["x"][r] for r in RV_SHADOW]
        return int.from_bytes(b"".join(w.to_bytes(4, "little") for w in words), "little")

    def leading(self):
        return [b"".join(w.to_bytes(4, "little") for w in program) for program in RV_DIRECTED.values()]

    def random_tx(self, rng):
        return b"".join(w.to_bytes(4, "little") for w in rv_random_program(rng))


MODELS = {cls.name: cls for cls in (Fir4, ElasticDot4, Dot4Pipeline, IterativeDivider,
                                     PacketFifo, SyncFifo, Aes128, Cordic, Fir16Sym,
                                     Crc16Stream, SpiMaster, Rv32iCore)}


def model_for(name: str, wrong: bool = False) -> Model:
    try:
        return MODELS[name](wrong=wrong)
    except KeyError:
        raise KeyError(f"no model for design {name!r}; known: {', '.join(MODELS)}") from None
