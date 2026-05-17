# Palindrome Hex Symmetry Markers

Status: `DETERMINISTIC_MARKER_DESIGN_PRIOR`

Source prompt: Scientific American Proof Positive puzzle context, user supplied
palindrome probability counts, 2026-05-09.

Source page:

```text
https://www.scientificamerican.com/article/why-some-mathematicians-think-we-should-abandon-pi/
```

## Claim Boundary

Palindrome hex values are useful as deterministic symmetry markers, frame
sentinels, mirror-route tags, and replay witnesses.

They are not:

- entropy sources
- cryptographic identifiers
- collision-resistant hashes
- uniqueness guarantees
- proof of payload correctness by themselves

The correct role is:

```text
palindrome marker + marker namespace + payload hash + receipt hash
```

not:

```text
palindrome marker = secure identity
```

## Counting Rule

The decimal puzzle gives the intuition: if a number must read the same forward
and backward, the first symbol controls both ends. That makes leading-zero
constraints matter.

For a four-hex-digit marker:

```text
ABBA
```

with no leading zero:

```text
A in {1..F}  -> 15 choices
B in {0..F}  -> 16 choices
palindromes  -> 15 * 16 = 240
4-hex-digit values from 0x1000..0xFFFF -> 61440
probability -> 240 / 61440 = 1 / 256
```

If leading zeros are allowed inside a fixed 16-bit lane:

```text
palindromes -> 16 * 16 = 256
all 16-bit values -> 65536
probability -> 1 / 256
```

So the marker is deterministic and sparse enough to be visible, but nowhere
near sparse enough to act as a security token.

## Marker Examples

These are reserved as examples until a Lean/Rust marker registry exists:

| Marker | Meaning |
|---|---|
| `0xA55A` | mirror-route synchronization marker |
| `0x5AA5` | reverse replay checkpoint marker |
| `0xC33C` | closure witness marker |
| `0xE11E` | admitted edge marker |
| `0xF00F` | frame boundary marker |

## Static Decompressor Use

For a static decompressor, palindrome hex markers can provide cheap boundaries
inside a zero-whitespace or compact base stream:

```text
packet stream
-> palindrome frame marker
-> marker namespace
-> payload hash
-> residual policy
-> replay receipt
```

The decompressor may use the marker to regain synchronization, choose the mirror
replay lane, or reject a malformed frame early. It still must verify hashes and
receipts before admitting payload bytes.

## Remote Test Use

For local/remote reproducibility tests, palindrome markers are useful because
they make packet boundaries deterministic across environments:

```text
local packet marker == remote packet marker
local payload hash  == remote payload hash
local receipt hash  == remote receipt hash
```

If marker equality holds but payload or receipt hashes diverge, the marker has
done its job: it localized the mismatch without pretending the result is valid.

## Gates

```text
ADMIT_MARKER
  if marker is palindromic
  and namespace is declared
  and payload hash exists
  and receipt hash exists
  and mirror replay agrees

HOLD_NOT_SYMMETRIC
  if a marker in the palindrome lane is not palindromic

HOLD_NAMESPACE_COLLISION
  if the same marker is reused without a namespace or packet kind

HOLD_MIRROR_REPLAY_MISMATCH
  if forward and reverse replay disagree

QUARANTINE_ENTROPY_MISUSE
  if a palindrome marker is used as a secret, random nonce, or security proof
```

## Integration Rule

Palindrome hex values are structural punctuation for the receipt stream:

```text
symbol count gives spacing
palindrome gives mirror boundary
hash gives payload identity
receipt gives replay authority
```

This pairs cleanly with whitespace-zero grammar, omindirection, static OISC
decompression, and remote reproducibility tests.
