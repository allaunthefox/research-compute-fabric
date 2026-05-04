import os
import sys
from infra.deepseek_adapter import DeepSeekV4, DeepSeekProver

def resolve_batch():
    client = DeepSeekV4(use_local=True)
    prover = DeepSeekProver(client)
    
    tasks = [
        {
            "name": "foldl_add_reverse",
            "context": "Score addition is commutative and associative. Prove: l.reverse.foldl Score.add init = l.foldl Score.add init"
        },
        {
            "name": "pathCost_reverse",
            "context": "pathCost p = foldl add e.cost p init. Prove: pathCost (p.reversePath) = pathCost p"
        },
        {
            "name": "dist_self_zero",
            "context": "shortestPathDist x x is the cost of the empty path. Prove it equals {num:=0, den:=1}."
        }
    ]
    
    for task in tasks:
        print(f"Resolving {task['name']}...")
        proof = prover.formalize(task['context'])
        print(f"Result for {task['name']}:\n{proof}\n")

if __name__ == "__main__":
    resolve_batch()
