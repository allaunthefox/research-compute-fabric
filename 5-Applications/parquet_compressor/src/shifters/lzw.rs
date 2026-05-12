use crate::shifters::{ManifoldState, Shifter};
use byteorder::{BigEndian, ByteOrder};
use serde_json::json;
use std::collections::HashMap;

pub struct LZWShifter;

impl Shifter for LZWShifter {
    fn name(&self) -> &'static str {
        "lzw"
    }

    fn encode(&self, state: &mut ManifoldState) -> anyhow::Result<()> {
        let data = if !state.encoded.is_empty() {
            &state.encoded
        } else {
            &state.raw_bytes
        };
        let max_dict = 4096;
        if data.is_empty() {
            state.update(Vec::new(), self.name(), json!({"max_dict": max_dict}));
            return Ok(());
        }

        let mut dictionary: HashMap<Vec<u8>, u16> =
            (0..=255).map(|b| (vec![b], b as u16)).collect();
        let mut next_code = 256u16;
        let mut result = Vec::new();
        let mut w = Vec::new();

        for &b in data {
            let mut wc = w.clone();
            wc.push(b);
            if dictionary.contains_key(&wc) {
                w = wc;
            } else {
                let code = dictionary.get(&w).unwrap();
                let mut buf = [0u8; 2];
                BigEndian::write_u16(&mut buf, *code);
                result.extend_from_slice(&buf);

                if next_code < max_dict {
                    dictionary.insert(wc, next_code);
                    next_code += 1;
                }
                w = vec![b];
            }
        }
        if !w.is_empty() {
            let code = dictionary.get(&w).unwrap();
            let mut buf = [0u8; 2];
            BigEndian::write_u16(&mut buf, *code);
            result.extend_from_slice(&buf);
        }

        state.update(result, self.name(), json!({"max_dict": max_dict}));
        Ok(())
    }

    fn decode(&self, state: &mut ManifoldState) -> anyhow::Result<()> {
        let data = &state.encoded;
        if data.len() < 2 {
            return Ok(());
        }

        let mut dictionary: HashMap<u16, Vec<u8>> =
            (0..=255).map(|i| (i as u16, vec![i as u8])).collect();
        let mut next_code = 256u16;
        let mut result = Vec::new();

        let mut old_code = BigEndian::read_u16(&data[0..2]);
        let s = dictionary.get(&old_code).cloned().unwrap();
        result.extend_from_slice(&s);

        for i in (2..data.len()).step_by(2) {
            if i + 1 >= data.len() {
                break;
            }
            let code = BigEndian::read_u16(&data[i..i + 2]);

            let entry = if let Some(v) = dictionary.get(&code) {
                v.clone()
            } else if code == next_code {
                let mut v = dictionary.get(&old_code).unwrap().clone();
                v.push(v[0]);
                v
            } else {
                break;
            };

            result.extend_from_slice(&entry);

            if next_code < 4096 {
                let mut v = dictionary.get(&old_code).unwrap().clone();
                v.push(entry[0]);
                dictionary.insert(next_code, v);
                next_code += 1;
            }
            old_code = code;
        }

        state.encoded = result;
        Ok(())
    }
}
