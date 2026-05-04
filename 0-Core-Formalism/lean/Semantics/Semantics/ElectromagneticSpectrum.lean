/-
  ElectromagneticSpectrum.lean - Minimal stub for RegimeCore dependency
-/

namespace Semantics.ElectromagneticSpectrum

-- Local Q16_16 definition to avoid circular dependencies
abbrev Q16_16 := UInt32

namespace Q16_16

def scale : Nat := 65536

def zero : Q16_16 := UInt32.ofNat 0
def one : Q16_16 := UInt32.ofNat 65536
def half : Q16_16 := UInt32.ofNat 32768
def quarter : Q16_16 := UInt32.ofNat 16384
def eighth : Q16_16 := UInt32.ofNat 8192

def satFromNat (n : Nat) : Q16_16 :=
  UInt32.ofNat (min n 4294967295)

def fromNat (n : Nat) : Q16_16 :=
  satFromNat (n * scale)

def ge (left right : Q16_16) : Bool :=
  left.toNat >= right.toNat

def le (left right : Q16_16) : Bool :=
  left.toNat <= right.toNat

end Q16_16

inductive SpectrumBand
| radio
| microwave
| infrared
| optical
| ultraviolet
| xray
| gamma
  deriving Repr, DecidableEq

structure BandProfile where
  band : SpectrumBand
  intensity : Q16_16
  deriving Repr, DecidableEq

inductive PlasmaInteraction
| none
| plasmaCoupling
| ionization
  deriving Repr, DecidableEq

structure ElectromagneticSample where
  bandProfile : BandProfile
  interaction : PlasmaInteraction
  deriving Repr, DecidableEq

def isIonizingBand (band : SpectrumBand) : Bool :=
  match band with
  | .xray => true
  | .gamma => true
  | _ => false

end Semantics.ElectromagneticSpectrum
