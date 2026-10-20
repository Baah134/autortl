# Structural interface contracts

Static checks compare the interface before compilation. They reject drift even
when the changed design happens to have the same default number of port bits.
Simulation and final evaluation remain mandatory after these structural checks.

## Typed ports

Existing JSON specifications remain unsigned by default. Optional `signed`
and `packed_dimensions` fields describe explicit port types:

```json
{"name":"sample","direction":"input","width":8,
 "signed":true,"packed_dimensions":[[0,7]]}
```

This is an ascending, signed eight-bit packed input. `signed` must be boolean;
packed dimensions are nonempty integer bound pairs whose product matches width.
Omitting dimensions retains the previous descending vector convention; width
one is scalar. Multiple packed dimensions retain their order and index direction.

The shared declaration renderer carries these types through child stubs, top
ports, internal wires, generated testbench signals and role descriptions. Wiring
checks reject signedness and packed shape mismatches rather than silently casting.

## Inferred optimization interfaces

The parser separates public parameters from local constants. Public parameter
names, declaration order, defaults and types are part of the contract. Constant
resolution uses both public and local definitions, but local constants do not
become overridable public parameters.

An inferred interface also retains a versioned structural signature:

- Symbolic public defaults and declaration types, in declaration order.
- Port names, order, directions, signedness and packed bound expressions.
- Local constants referenced transitively by those interface expressions.

Changing `WIDTH-1` to `7` is rejected even if WIDTH currently defaults to eight.
Changing a dependent default to its current resolved value is also rejected.
Reversing a range or flattening a multidimensional shape changes the contract.
Unrelated internal constants remain available for optimization.

Comments, spacing and compatible grouped declarations are normalized. Symbolic
expressions are preserved conservatively; the parser does not prove algebraic
equivalence of arbitrary rewritten declarations. Keep the original declarations
when only implementation logic is being optimized.

Common non-ANSI output/reg declarations remain supported when their shapes and
types agree explicitly. Conflicting or ambiguous redeclarations fail with an
explanation. Unsupported syntax fails rather than being guessed. This is a
bounded Verilog interface parser, not a full SystemVerilog language frontend.

## Stubs and qualification

Inferred stubs retain symbolic public defaults and the local constants needed
by packed bounds. Fallback qualification mutants use the same interface stub
and replace output behavior with stuck-zero assignments. A compilation failure
is not evidence that a testbench detected the intended behavioral defect.

## Signed golden models

The oracle API still uses nonnegative masked bit patterns, from zero through
`2**width - 1`. A signed eight-bit input value 128 represents -128. The Python
oracle must implement the contract's two's-complement interpretation explicitly;
port signedness does not silently change the software API or permit negative
expected output integers.

For example, interpret an eight-bit value with
`value if value < 128 else value - 256` before a signed comparison. Return the
result encoded back into the output width when arithmetic produces negative data.

## What these checks do not prove

Structural preservation does not establish behavioral equivalence for every
legal parameter override. Independent references must cover relevant sizes,
thresholds, signed extremes, overflow, reset, stalls and timing. Finite simulation
is not a formal equivalence or physical CDC proof. Parser rejection is an
unsupported-interface outcome, not evidence of a successful optimization.

## Declared latency metadata

ModuleSpec.latency_known defaults to true for typed JSON compatibility. Typed
build validation and every generated-TB entry point require it to be exactly
true and latency to be a supported integer. A numeric annotation is metadata,
not independent proof that a circuit has that behavior.

When optimization source has no @latency annotation, inference records
latency_known=false. The internal legacy numeric placeholder is not a known
zero-cycle or combinational contract. Authoritative source evidence instead
exposes known=false/cycles=null and binds that observation to the source hash.
Generators preserve the original cycles and do not invent a numeric annotation.
The original source and frozen testbench remain behavioral authorities.
