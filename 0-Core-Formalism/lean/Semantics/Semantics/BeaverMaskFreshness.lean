namespace Semantics.BeaverMaskFreshness

/-- Source class for a Beaver-style mask coefficient.  Only `freshRandom`
    is admissible for privacy-equivalent Beaver masking in this gate model. -/
inductive MaskSource where
  | freshRandom
  | reused
  | topologyDerived
  | adversarialChosen
  deriving Repr, DecidableEq, BEq

/-- A finite audit event for one mask coefficient. -/
structure MaskEvent where
  epoch : Nat
  party : Nat
  maskId : Nat
  source : MaskSource
  deriving Repr, DecidableEq, BEq

def sourceFreshIndependent (source : MaskSource) : Bool :=
  source == MaskSource.freshRandom

def eventFreshIndependent (event : MaskEvent) : Bool :=
  sourceFreshIndependent event.source

def maskIdUsedBefore (maskId : Nat) : List MaskEvent → Bool
  | [] => false
  | event :: rest => (event.maskId == maskId) || maskIdUsedBefore maskId rest

/-- Admission gate for treating a coefficient as a privacy-equivalent mask.
    It must be fresh/independent and its mask id must not already occur in the
    receipt history. -/
def admissibleMaskEvent (history : List MaskEvent) (event : MaskEvent) : Bool :=
  eventFreshIndependent event && !maskIdUsedBefore event.maskId history

def admitMaskEvent (history : List MaskEvent) (event : MaskEvent) : Option (List MaskEvent) :=
  if admissibleMaskEvent history event then
    some (event :: history)
  else
    none

def freshA : MaskEvent :=
  { epoch := 0, party := 0, maskId := 1001, source := MaskSource.freshRandom }

def freshB : MaskEvent :=
  { epoch := 0, party := 1, maskId := 1002, source := MaskSource.freshRandom }

def reusedA : MaskEvent :=
  { epoch := 1, party := 0, maskId := 1001, source := MaskSource.reused }

def topologyA : MaskEvent :=
  { epoch := 1, party := 0, maskId := 2001, source := MaskSource.topologyDerived }

def adversarialA : MaskEvent :=
  { epoch := 1, party := 0, maskId := 3001, source := MaskSource.adversarialChosen }

/-- Positive control: a fresh random mask with an unused id admits. -/
theorem freshUnusedAdmits :
    admissibleMaskEvent [] freshA = true := by
  native_decide

/-- Positive control: distinct fresh random mask ids may both admit. -/
theorem distinctFreshSequenceAdmits :
    admitMaskEvent [freshA] freshB = some [freshB, freshA] := by
  native_decide

/-- Negative control: an explicit reused-source coefficient is rejected. -/
theorem reusedSourceRejected :
    admissibleMaskEvent [freshA] reusedA = false := by
  native_decide

/-- Negative control: even if source were mislabeled fresh, mask-id reuse is rejected. -/
theorem reusedMaskIdRejected :
    admissibleMaskEvent [freshA] { reusedA with source := MaskSource.freshRandom } = false := by
  native_decide

/-- Negative control: topology-derived adaptive coefficients are not treated as
    privacy-equivalent random masks by this gate. -/
theorem topologyDerivedRejected :
    admissibleMaskEvent [] topologyA = false := by
  native_decide

/-- Negative control: adversarially chosen coefficients are rejected. -/
theorem adversarialChosenRejected :
    admissibleMaskEvent [] adversarialA = false := by
  native_decide

#eval admissibleMaskEvent [] freshA
#eval admissibleMaskEvent [freshA] reusedA
#eval admissibleMaskEvent [freshA] { reusedA with source := MaskSource.freshRandom }
#eval admissibleMaskEvent [] topologyA
#eval admissibleMaskEvent [] adversarialA

end Semantics.BeaverMaskFreshness
