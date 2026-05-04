use std::fs::File;
use std::path::Path;
use parquet::file::reader::{FileReader, SerializedFileReader};
use parquet::record::RowAccessor;
use serde_json::json;

pub fn serialize_parquet_to_bytes(path: &Path) -> anyhow::Result<Vec<u8>> {
    let file = File::open(path)?;
    let reader = SerializedFileReader::new(file)?;
    
    let mut lines = Vec::new();
    let row_iter = reader.get_row_iter(None)?;
    
    for record in row_iter {
        let record = record?;
        // Find fields by name
        let equation = find_field(&record, "equation").unwrap_or_default();
        let pattern = find_field(&record, "pattern").unwrap_or_default();
        let domain = find_field(&record, "domain").unwrap_or_default();
        let confidence = find_float_field(&record, "confidence").unwrap_or(0.0);

        let compact = json!({
            "e": equation,
            "p": pattern,
            "d": domain,
            "c": confidence,
        });
        lines.push(serde_json::to_string(&compact)?);
    }

    Ok(lines.join("\n").into_bytes())
}

fn find_field(record: &parquet::record::Row, name: &str) -> Option<String> {
    for (i, (field_name, _)) in record.get_column_iter().enumerate() {
        if field_name == name {
            return Some(record.get_string(i).ok()?.to_string());
        }
    }
    None
}

fn find_float_field(record: &parquet::record::Row, name: &str) -> Option<f64> {
    for (i, (field_name, _)) in record.get_column_iter().enumerate() {
        if field_name == name {
            return Some(record.get_double(i).ok()?);
        }
    }
    None
}
