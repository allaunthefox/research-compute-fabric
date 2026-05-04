import json

def sadd(a, b):
    """Saturating 32-bit signed addition."""
    res = a + b
    if res > 0x7FFFFFFF: return 0x7FFFFFFF
    if res < -0x80000000: return -0x80000000
    return res

def to_q16_16(val):
    return int(val * 65536)

class AVMReference:
    def __init__(self):
        self.state = {"stack": [], "pc": 0}

    def compute_routing(self, genome, event_source, lawful):
        # GenomeAddr = {mu, rho, c, m, ne, sigma}
        # addr = {muBin, rhoBin, cBin, mBin, neBin, sigmaBin}
        addr = 0
        for i, val in enumerate(genome):
            addr = (addr << 3) | (val & 0x7)
        
        bucket = genome[0] # muBin
        
        # SourceTargetClassifier
        # notion=0, linear=1, ene=2, rgflow=3, swarm=4
        # TGT: ene_pkgs=0, swarm_man=1, swarm_nodes=2, swarm_wq=3, mcast=4
        source = event_source
        if source in [0, 1, 2]: target = 0
        elif source == 3: target = 1
        elif source == 4 and lawful: target = 2
        elif source == 4 and not lawful: target = 3
        else: target = 4
        
        return addr, bucket, target

    def compute_cost(self, bind_cost, bucket):
        return sadd(bind_cost, bucket)

def generate_receipts():
    avm = AVMReference()
    boards = [
        {"name": "Board 0", "genome": [2,4,0,4,7,0], "source": 4, "lawful": True, "cost": 0x10000},
        {"name": "Board 1", "genome": [7,7,7,7,7,7], "source": 4, "lawful": False, "cost": 0x20000},
        {"name": "Board 2", "genome": [1,2,3,4,5,6], "source": 2, "lawful": True, "cost": 0xA000},
        {"name": "Board 3", "genome": [0,0,0,0,0,0], "source": 4, "lawful": True, "cost": 0x0000},
        {"name": "Board 4", "genome": [5,3,1,6,2,4], "source": 3, "lawful": True, "cost": 0x15000},
    ]
    
    results = []
    for b in boards:
        addr, bucket, target = avm.compute_routing(b["genome"], b["source"], b["lawful"])
        total_cost = avm.compute_cost(b["cost"], bucket)
        results.append({
            "board": b["name"],
            "addr": hex(addr),
            "target": target,
            "cost": hex(total_cost)
        })
        
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    generate_receipts()
