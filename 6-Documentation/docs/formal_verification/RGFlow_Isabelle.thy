(* RGFlow_Isabelle.thy

Isabelle/HOL port of Bitcoin RG Flow compression using Q16.16 fixed-point arithmetic.

Purpose:
  * Formalize the RGFlow lawfulness invariant
  * Define Q16.16 fixed-point arithmetic operations
  * Specify sigma channel computation
  * Separate validity from lawfulness

This theory focuses on the core mathematical definitions and invariants.
*)

theory RGFlow_Isabelle
  imports Main
begin

section {* Q16.16 Fixed-Point Arithmetic *}

definition SCALE :: int where
  "SCALE = 65536"

definition HALF :: int where
  "HALF = SCALE div 2"

definition ONE :: int where
  "ONE = SCALE"

(* Q16.16 constructor from integer *)
definition q_of_int :: "int \<Rightarrow> int" where
  "q_of_int x = x * SCALE"

(* Q16.16 constructor from numerator/denominator *)
definition q_div_int :: "int \<Rightarrow> int \<Rightarrow> int" where
  "q_div_int num den = (if den = 0 then 0 else (num * SCALE) div den)"

(* Q16.16 multiplication *)
definition q_mul :: "int \<Rightarrow> int \<Rightarrow> int" where
  "q_mul a b = (a * b) div SCALE"

(* Q16.16 division *)
definition q_div :: "int \<Rightarrow> int \<Rightarrow> int" where
  "q_div a b = (if b = 0 then 0 else (a * SCALE) div b)"

(* Absolute value *)
definition q_abs :: "int \<Rightarrow> int" where
  "q_abs x = (if x < 0 then -x else x)"

(* Clamp fixed-point value *)
definition q_clamp :: "int \<Rightarrow> int \<Rightarrow> int \<Rightarrow> int" where
  "q_clamp lo hi x = max lo (min hi x)"

(* Q16 constants *)
definition q0001 :: int where "q0001 = q_div_int 1 1000"      (* 0.001 *)
definition q0002 :: int where "q0002 = q_div_int 2 1000"      (* 0.002 *)
definition q0003 :: int where "q0003 = q_div_int 3 1000"      (* 0.003 *)
definition q0004 :: int where "q0004 = q_div_int 4 1000"      (* 0.004 *)
definition q0008 :: int where "q0008 = q_div_int 8 1000"      (* 0.008 *)
definition q0125 :: int where "q0125 = q_div_int 125 1000"    (* 0.125 *)
definition q025  :: int where "q025  = q_div_int 25 100"      (* 0.25 *)
definition q035  :: int where "q035  = q_div_int 35 100"      (* 0.35 *)
definition q05   :: int where "q05   = q_div_int 5 10"        (* 0.5 *)
definition q0875 :: int where "q0875 = q_div_int 875 1000"    (* 0.875 *)
definition q3    :: int where "q3    = q_of_int 3"

section {* RGFlow Constants *}

definition D :: int where "D = q0003"
definition B :: int where "B = q0001"
definition lambda :: int where "lambda = q05"
definition epsilon :: int where "epsilon = 1"

section {* Data Structures *}

record PricePoint =
  day_index :: nat
  price_cents :: int

record CompressedCode =
  index :: nat
  symbol :: "8 word"
  valid :: bool
  mu_q :: int
  rho_q :: int
  c_fac :: int
  m_fac :: int
  ne_eff :: int
  sigma_q :: int
  lawful :: bool
  cost :: nat

record AuditSummary =
  total_codes :: nat
  valid_codes :: nat
  lawful_codes :: nat
  sigma_min :: int
  sigma_max :: int
  sigma_mean :: int
  sigma_std :: int
  sigma_pinned :: bool

section {* Helper Functions *}

(* Healthy modularity factor, maximized at 0.5 *)
definition phi :: "int \<Rightarrow> int" where
  "phi m_fac = ONE - q_abs (m_fac - q05)"

(*
The RGFlow lawfulness invariant.

This is deliberately independent from `valid`.
A code may be syntactically valid but fail the RGFlow invariant.
*)
definition rg_lawful :: "int \<Rightarrow> int \<Rightarrow> int \<Rightarrow> int \<Rightarrow> int \<Rightarrow> int \<Rightarrow> bool" where
  "rg_lawful mu_q rho_q c_fac m_fac ne_eff sigma_q =
    (mu_q \<le> q_div D (max c_fac epsilon)) \<and>
    (q_mul (q_mul rho_q ne_eff) (phi m_fac) \<ge> B) \<and>
    (sigma_q > ONE + q_mul lambda mu_q)"

(*
Integer log-return proxy in Q16.16.

Uses absolute relative price move: |curr - prev| / prev
This avoids floating-point logarithms in the fixed-point path.
*)
definition rel_move_q16 :: "int \<Rightarrow> int \<Rightarrow> int" where
  "rel_move_q16 prev curr =
    (if prev \<le> 0 \<or> curr \<le> 0 then 0
     else q_div (q_abs (curr - prev)) prev)"

(*
Mean in Q16.16 for a list of values.
*)
definition q_mean :: "int list \<Rightarrow> int" where
  "q_mean xs = (if xs = [] then 0 else sum xs div int (length xs))"

(*
Mean absolute deviation in Q16.16.

Used instead of sqrt variance to keep the fixed-point path simple.
*)
definition q_mad :: "int list \<Rightarrow> int" where
  "q_mad xs =
    (if length xs \<le> 1 then 0
     else let m = q_mean xs in
          sum (map (\<lambda>x. q_abs (x - m)) xs) div int (length xs))"

(*
First-pass fixed-point sigma channel.

It rewards local trend coherence and penalizes move dispersion.

raw: sigma = 1.0 + 0.35 * coherence - 8 * dispersion
where: coherence = |mean(move)| / (MAD(move) + epsilon)

Range: sigma_q is clamped to [0.25, 3.0].
*)
definition compute_sigma_q :: "int list \<Rightarrow> nat \<Rightarrow> nat \<Rightarrow> int" where
  "compute_sigma_q prices code_index window =
    (let moves = map (\<lambda>i. rel_move_q16 (prices ! (i - 1)) (prices ! i)) 
                        [1..<length prices];
         ri = (if code_index = 0 then 0 else code_index - 1);
         local_len = min (ri + 1) window;
         local = take local_len (drop (max 0 (ri + 1 - window)) moves);
         disp = q_mad local;
         mom = q_mean local;
         coherence = q_div (q_abs mom) (disp + epsilon);
         raw = ONE + q_mul q035 coherence - q_mul (q_of_int 8) disp
     in q_clamp q025 q3 raw)"

section {* Validity Predicate *}

(*
Toy validity predicate for a compressed symbol.

Replace with the production validity predicate. Kept separate from lawfulness.
*)
definition valid_symbol :: "8 word \<Rightarrow> bool" where
  "valid_symbol s = ((ucast s :: nat) AND 3) \<noteq> 3"

section {* Encoding Function *}

(*
Encode one adjacent pair into Q16.16 RGFlow variables.

This is a reference mapping. Replace with production genome mapping.
*)
definition encode_code :: "int list \<Rightarrow> int \<Rightarrow> int \<Rightarrow> nat \<Rightarrow> CompressedCode" where
  "encode_code prices min_price max_price i =
    (let p0 = prices ! i;
         p1 = prices ! (i + 1);
         span = max (max_price - min_price) 1;
         x = max 0 (min span (p0 - min_price));
         pos0 = nat ((x * 65535) div span);
         y = max 0 (min span (p1 - min_price));
         pos1 = nat ((y * 65535) div span);
         d = (if pos1 \<ge> pos0 then pos1 - pos0 else pos0 - pos1);
         sym = word_of_int (int (d mod 256)) :: 8 word;
         valid = valid_symbol sym;
         move = rel_move_q16 p0 p1;
         mu_q = q_clamp q0001 q0008 
                  (q0001 + q_mul (q_div_int 7 1000) 
                    (q_clamp 0 ONE (q_mul move (q_of_int 25))));
         rho_q = q_clamp q0001 q0008 
                  (q0004 + (if valid then q0002 else -q0002));
         c_fac = q_clamp q0125 ONE 
                  (q0125 + q_mul q0875 (q_clamp 0 ONE (q_mul move (q_of_int 10))));
         m_fac = q05;
         ne_raw = min (i + 1) 365;
         ne_eff = q_mul (q_of_int (int ne_raw)) LN2_Q16;
         sigma_q = compute_sigma_q prices i 30;
         lawful = rg_lawful mu_q rho_q c_fac m_fac ne_eff sigma_q;
         cost = (if valid then 0 else 1) + (if lawful then 0 else 4)
     in \<lparr> index = i, symbol = sym, valid = valid, mu_q = mu_q,
          rho_q = rho_q, c_fac = c_fac, m_fac = m_fac, ne_eff = ne_eff,
          sigma_q = sigma_q, lawful = lawful, cost = cost \<rparr>)"

(* LN(2) approximation in Q16.16: ln(2) \<approx> 0.693147 *)
definition LN2_Q16 :: int where "LN2_Q16 = 45426"

section {* Theorems *}

theorem rg_lawful_components:
  assumes "rg_lawful mu_q rho_q c_fac m_fac ne_eff sigma_q"
  shows "mu_q \<le> q_div D (max c_fac epsilon)"
    and "q_mul (q_mul rho_q ne_eff) (phi m_fac) \<ge> B"
    and "sigma_q > ONE + q_mul lambda mu_q"
  using assms unfolding rg_lawful_def by auto

theorem phi_bounds:
  assumes "0 \<le> m_fac" and "m_fac \<le> ONE"
  shows "0 \<le> phi m_fac" and "phi m_fac \<le> ONE"
proof -
  have "q_abs (m_fac - q05) \<le> q05"
    using assms unfolding q_abs_def by auto
  thus "0 \<le> phi m_fac" and "phi m_fac \<le> ONE"
    unfolding phi_def ONE_def q05_def by auto
qed

theorem sigma_clamped:
  assumes "compute_sigma_q prices i window = sigma"
  shows "q025 \<le> sigma" and "sigma \<le> q3"
  using assms unfolding compute_sigma_q_def q_clamp_def by auto

theorem valid_symbol_decidable:
  "\<forall>s. valid_symbol s \<or> \<not> valid_symbol s"
  unfolding valid_symbol_def by auto

end
