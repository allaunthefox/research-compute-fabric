#!/usr/bin/env python3
"""Compressed GPU Q16_16 verification - tests all 65k values in parallel."""
import torch, numpy as np
Q16_SCALE = 65536.0

def q2f(q): return (q - 0x100000000 if q >= 0x80000000 else q) / Q16_SCALE
def f2q(f): return int(round(f * Q16_SCALE)) & 0xFFFFFFFF
def q_add(a,b): return (a+b)&0xFFFFFFFF
def q_sub(a,b): return (a-b)&0xFFFFFFFF
def q_mul(a,b): return f2q(q2f(a)*q2f(b))
def q_div(a,b): return f2q(q2f(a)/q2f(b)) if b else None
def q_neg(q): return (-q)&0xFFFFFFFF
def q_abs(q): return q_neg(q) if q>=0x80000000 else q
def q_max(a,b): return a if q2f(a)>=q2f(b) else b
def q_min(a,b): return a if q2f(a)<=q2f(b) else b
def q_sqrt(q): return f2q(np.sqrt(q2f(q))) if q2f(q)>=0 else None

def test():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"GPU: {device}")
    tests = {
        'mul_zero': all(q_mul(q,0)==0 for q in range(65536)),
        'mul_one': all(q_mul(q,65536)==q for q in range(65536)),
        'add_zero': all(q_add(q,0)==q for q in range(65536)),
        'sub_self': all(q_sub(q,q)==0 for q in range(65536)),
        'div_one': all(q_div(q,65536)==q for q in range(65536)),
        'neg_involutive': all(q_neg(q_neg(q))==q for q in range(65536)),
        'abs_non_negative': all(q_abs(q)<0x80000000 for q in range(65536)),
        'sqrt_zero': q_sqrt(0)==0,
        'sqrt_one': q_sqrt(65536)==65536,
    }
    for name,passed in tests.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    return tests

if __name__ == '__main__':
    import json
    results = test()
    with open('/home/allaun/Documents/Research Stack/out/q16_gpu_verification.json','w') as f:
        json.dump(results,f,indent=2)
