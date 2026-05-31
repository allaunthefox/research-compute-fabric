use wasm_bindgen::prelude::*;

const VM_OPS: usize = 7;
const TRIT_WIDTH: usize = 32;

#[wasm_bindgen]
pub struct VmState {
    sub: [[i8; TRIT_WIDTH]; VM_OPS],
}

#[wasm_bindgen]
impl VmState {
    #[wasm_bindgen(constructor)]
    pub fn new() -> VmState {
        VmState {
            sub: [[0; TRIT_WIDTH]; VM_OPS],
        }
    }

    #[wasm_bindgen]
    pub fn reset(&mut self) {
        self.sub = [[0; TRIT_WIDTH]; VM_OPS];
    }

    #[wasm_bindgen]
    pub fn step(&mut self, op: u8, idx: u8, val: i8) {
        let op_idx = (op as usize) % VM_OPS;
        let i = (idx as usize) % TRIT_WIDTH;
        let val = clamp(val);

        match op {
            0 => self.sub[op_idx][i] = val,            // SET
            1 => self.sub[op_idx][i] = clamp(self.sub[op_idx][i] + 1), // ADD
            2 => self.sub[op_idx][i] = clamp(self.sub[op_idx][i] - 1), // SUB
            3 => {                                     // SHIFT
                let tmp = self.sub[op_idx][TRIT_WIDTH - 1];
                for j in (1..TRIT_WIDTH).rev() {
                    self.sub[op_idx][j] = self.sub[op_idx][j - 1];
                }
                self.sub[op_idx][0] = tmp;
            }
            4 => {                                     // MERGE
                let src_reg = ((val + 1) as usize) % VM_OPS;
                self.sub[op_idx][i] = clamp(self.sub[op_idx][i] + self.sub[src_reg][i]);
            }
            5 => {                                     // PROJECT
                let src_idx = (idx as usize + 1) % TRIT_WIDTH;
                let src_reg = (op as usize + 1) % VM_OPS;
                self.sub[op_idx][i] = self.sub[src_reg][src_idx];
            }
            6 => self.sub[op_idx][i] = clamp(self.sub[op_idx][i] * val), // W (weight)
            _ => {}
        }
    }

    #[wasm_bindgen]
    pub fn derive_scalar(&self) -> u16 {
        let mut acc: i32 = 0;
        for s in 0..VM_OPS {
            for t in 0..TRIT_WIDTH {
                acc = (acc << 1) + (self.sub[s][t] as i32);
            }
        }
        (acc & 0xFFFF) as u16
    }
}

#[inline]
fn clamp(v: i8) -> i8 {
    if v < -1 {
        -1
    } else if v > 1 {
        1
    } else {
        v
    }
}
