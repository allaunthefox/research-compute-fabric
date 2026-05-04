import Std
import ExtensionScaffold.ENE.SemanticLinter

open Std
open Semantics.SemanticLinter

namespace SemanticLinterTest

/-- Sample provenance pipeline code to lint. -/
def sampleProvenanceCode : String := "
class ENEProvenancePipeline:
    def create_manifest(self, archive_record, op_code, signal_metadata):
        input_digest = self.current_state_hash
        output_digest = archive_record.get('content_hash', self.compute_digest(archive_record['raw_content']))
        
        manifest = ProvenanceManifest(
            pipeline_id=self.pipeline_id,
            input_digest=input_digest,
            op_code=op_code,
            signal_metadata=signal_metadata,
            output_digest=output_digest,
            timestamp=datetime.now().isoformat(),
            sequence_num=self.sequence,
            prev_manifest_hash=self.current_state_hash if self.sequence > 0 else None
        )
        return manifest
    
    def compute_merkle_root(self, leaves):
        if len(leaves) % 2 == 1:
            leaves.append(leaves[-1])
        current_level = leaves
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                combined = hashlib.sha256((left + right).encode()).hexdigest()
                next_level.append(combined)
            current_level = next_level
        return current_level[0]
    
    def process_archive(self, archive_path):
        for archive_id, record in archive['records'].items():
            self.merkle_leaves.append(record.get('content_hash', ''))
    
    def main():
        import math
        import argparse
"

/-- Run semantic linter on sample code. -/
#eval do
  let report := renderReport sampleProvenanceCode
  IO.println "=== Semantic Lint Report ==="
  IO.println report
  IO.println ""
  IO.println "=== End Report ==="

/-- Sample compliant code (post-fix). -/
def sampleCompliantCode : String := "
class ENEProvenancePipeline:
    def create_manifest(self, archive_record, op_code, signal_metadata):
        input_digest = self.current_state_hash
        output_digest = archive_record.get('content_hash') or self.compute_digest(archive_record['raw_content'])
        
        prev_manifest_hash = None
        if self.sequence > 0 and self.manifests:
            prev_manifest_hash = self.manifests[-1].manifest_hash
        
        manifest_dict = {
            'pipeline_id': self.pipeline_id,
            'input_digest': input_digest,
            'op_code': op_code,
            'signal_metadata': signal_metadata,
            'output_digest': output_digest,
            'timestamp': datetime.now().isoformat(),
            'sequence_num': self.sequence,
            'prev_manifest_hash': prev_manifest_hash,
        }
        
        manifest_hash = self.compute_manifest_hash(manifest_dict)
        return manifest_hash
    
    def compute_merkle_root(self, leaves):
        current_level = list(leaves)
        if len(current_level) % 2 == 1:
            current_level.append(current_level[-1])
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                combined = hashlib.sha256((left + right).encode()).hexdigest()
                next_level.append(combined)
            current_level = next_level
        return current_level[0]
    
    def process_archive(self, archive_path):
        for archive_id, record in archive['records'].items():
            content_hash = record.get('content_hash') or self.compute_digest(record['raw_content'])
            self.merkle_leaves.append(content_hash)
"

/-- Run semantic linter on compliant code. -/
#eval do
  let report := renderReport sampleCompliantCode
  IO.println "=== Compliant Code Lint Report ==="
  IO.println report
  IO.println ""
  IO.println "=== End Report ==="

end SemanticLinterTest
