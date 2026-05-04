import ExtensionScaffold.ENE.SessionArchive

namespace ExtensionScaffold.ENE.ENEImport

/-! # Auto-Generated ENE Import

Generated: 2026-04-18T01:08:03.993782
Source: Legacy database migration
Records: 131

This module contains records imported from legacy databases:
- substrate_index.db
- graph_address_space.sql
- JSON manifest files

Status: Import complete. Ready for verification.
-/

/-- Imported legacy records as typed SessionArchive entries. -/
def importedRecords : List LegacySessionRecord := [  -- Imported record 0: substrate_packages_755cad3f154...
  { recordId := "substrate_packages_755cad3f154c4dc7"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.991840"
    sessionRef := "legacy_import_substrate"
    title := "packages record"
    summary := "Imported from substrate: substrate_packages_755cad3f154c4dc7..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"pkg\": \"chat-iso-precompression-20260325\", \"version\": \"1.0.0\", \"layer\": \"RULE\", \"domain\": \"DATA\", \"condition\": \"EXPERIMENTAL\", \"stage\": \"ACTIVE\", \"so" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 1: substrate_packages_745d534f84d...
  { recordId := "substrate_packages_745d534f84d23977"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.991873"
    sessionRef := "legacy_import_substrate"
    title := "packages record"
    summary := "Imported from substrate: substrate_packages_745d534f84d23977..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"pkg\": \"chat-iso-as-neural-filter-20260325\", \"version\": \"1.0.0\", \"layer\": \"RULE\", \"domain\": \"DATA\", \"condition\": \"EXPERIMENTAL\", \"stage\": \"ACTIVE\", \"" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 2: substrate_packages_fts_0190be8...
  { recordId := "substrate_packages_fts_0190be8958a903e4"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992099"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts record"
    summary := "Imported from substrate: substrate_packages_fts_0190be8958a903e4..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"pkg\": \"chat-iso-precompression-20260325\", \"version\": \"1.0.0\", \"tier\": \"RESEARCH\", \"domain\": \"DATA\", \"module\": \"ISO_PRECOMPRESSION_LAYER\", \"archetype" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 3: substrate_packages_fts_aa9e24b...
  { recordId := "substrate_packages_fts_aa9e24b4c76cde19"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992109"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts record"
    summary := "Imported from substrate: substrate_packages_fts_aa9e24b4c76cde19..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"pkg\": \"chat-iso-as-neural-filter-20260325\", \"version\": \"1.0.0\", \"tier\": \"RESEARCH\", \"domain\": \"DATA\", \"module\": \"ISO_NEURAL_FILTER_EQUIVALENCE\", \"ar" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 4: substrate_packages_fts_data_fe...
  { recordId := "substrate_packages_fts_data_fead6fafae18f7f9"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992265"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts_data record"
    summary := "Imported from substrate: substrate_packages_fts_data_fead6fafae18..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"id\": 1, \"block\": \"061e1206061512820857\"}" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 5: substrate_packages_fts_data_bd...
  { recordId := "substrate_packages_fts_data_bd7a558e16bd27c2"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992271"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts_data record"
    summary := "Imported from substrate: substrate_packages_fts_data_bd7a558e16bd..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"id\": 10, \"block\": \"000000000106060006010101020101030101040101050101060101\"}" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 6: substrate_packages_fts_data_bb...
  { recordId := "substrate_packages_fts_data_bbbb47b8cf172510"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992276"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts_data record"
    summary := "Imported from substrate: substrate_packages_fts_data_bbbb47b8cf17..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"id\": 137438953473, \"block\": \"0000026f02303001080101030301013101060101020108323032363033323501\"}" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 7: substrate_packages_fts_data_83...
  { recordId := "substrate_packages_fts_data_837dcc45fb597246"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992280"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts_data record"
    summary := "Imported from substrate: substrate_packages_fts_data_837dcc45fb59..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"id\": 274877906945, \"block\": \"0000033c02303002080101030301013102060101020108323032363033323502\"}" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 8: substrate_packages_fts_data_86...
  { recordId := "substrate_packages_fts_data_8690aa957442339a"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992283"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts_data record"
    summary := "Imported from substrate: substrate_packages_fts_data_8690aa957442..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"id\": 412316860417, \"block\": \"0000026f02303003080101030301013103060101020108323032363033323503\"}" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 9: substrate_packages_fts_data_c4...
  { recordId := "substrate_packages_fts_data_c4cb0623a3f13ac9"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992287"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts_data record"
    summary := "Imported from substrate: substrate_packages_fts_data_c4cb0623a3f1..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"id\": 549755813889, \"block\": \"0000033c02303004080101030301013104060101020108323032363033323504\"}" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 10: substrate_packages_fts_data_a2...
  { recordId := "substrate_packages_fts_data_a219bcbbab31fd5d"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992290"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts_data record"
    summary := "Imported from substrate: substrate_packages_fts_data_a219bcbbab31..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"id\": 687194767361, \"block\": \"0000026f02303005080101030301013105060101020108323032363033323505\"}" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 11: substrate_packages_fts_data_cd...
  { recordId := "substrate_packages_fts_data_cdc3074ddb810486"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992294"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts_data record"
    summary := "Imported from substrate: substrate_packages_fts_data_cdc3074ddb81..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"id\": 824633720833, \"block\": \"0000033c02303006080101030301013106060101020108323032363033323506\"}" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 12: substrate_packages_fts_idx_5ab...
  { recordId := "substrate_packages_fts_idx_5ab7b437429c00b2"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992422"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts_idx record"
    summary := "Imported from substrate: substrate_packages_fts_idx_5ab7b437429c0..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"segid\": 1, \"term\": \"\", \"pgno\": 2}" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 13: substrate_packages_fts_idx_57a...
  { recordId := "substrate_packages_fts_idx_57a97792eb95ae1f"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992428"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts_idx record"
    summary := "Imported from substrate: substrate_packages_fts_idx_57a97792eb95a..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"segid\": 2, \"term\": \"\", \"pgno\": 2}" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 14: substrate_packages_fts_idx_c13...
  { recordId := "substrate_packages_fts_idx_c136bde3dab69689"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992431"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts_idx record"
    summary := "Imported from substrate: substrate_packages_fts_idx_c136bde3dab69..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"segid\": 3, \"term\": \"\", \"pgno\": 2}" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 15: substrate_packages_fts_idx_b53...
  { recordId := "substrate_packages_fts_idx_b53431d731ab7c83"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992434"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts_idx record"
    summary := "Imported from substrate: substrate_packages_fts_idx_b53431d731ab7..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"segid\": 4, \"term\": \"\", \"pgno\": 2}" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 16: substrate_packages_fts_idx_59b...
  { recordId := "substrate_packages_fts_idx_59bb28ada9918e1a"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992437"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts_idx record"
    summary := "Imported from substrate: substrate_packages_fts_idx_59bb28ada9918..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"segid\": 5, \"term\": \"\", \"pgno\": 2}" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 17: substrate_packages_fts_idx_fe8...
  { recordId := "substrate_packages_fts_idx_fe80e7774305c08d"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992440"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts_idx record"
    summary := "Imported from substrate: substrate_packages_fts_idx_fe80e7774305c..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"segid\": 6, \"term\": \"\", \"pgno\": 2}" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 18: substrate_packages_fts_docsize...
  { recordId := "substrate_packages_fts_docsize_baef14aa16326535"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992557"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts_docsize record"
    summary := "Imported from substrate: substrate_packages_fts_docsize_baef14aa1..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"id\": 1, \"sz\": \"040301010303230a\"}" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 19: substrate_packages_fts_docsize...
  { recordId := "substrate_packages_fts_docsize_20fedbbb05f9f7dc"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992561"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts_docsize record"
    summary := "Imported from substrate: substrate_packages_fts_docsize_20fedbbb0..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"id\": 2, \"sz\": \"0603010104033513\"}" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 20: substrate_packages_fts_docsize...
  { recordId := "substrate_packages_fts_docsize_3a58cfd0dfd86c43"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992564"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts_docsize record"
    summary := "Imported from substrate: substrate_packages_fts_docsize_3a58cfd0d..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"id\": 3, \"sz\": \"040301010303230a\"}" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 21: substrate_packages_fts_docsize...
  { recordId := "substrate_packages_fts_docsize_c73406751634da18"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992567"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts_docsize record"
    summary := "Imported from substrate: substrate_packages_fts_docsize_c73406751..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"id\": 4, \"sz\": \"0603010104033513\"}" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 22: substrate_packages_fts_docsize...
  { recordId := "substrate_packages_fts_docsize_d22c81a7878f6438"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992570"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts_docsize record"
    summary := "Imported from substrate: substrate_packages_fts_docsize_d22c81a78..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"id\": 5, \"sz\": \"040301010303230a\"}" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 23: substrate_packages_fts_docsize...
  { recordId := "substrate_packages_fts_docsize_6eeadfabb8d43b43"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992573"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts_docsize record"
    summary := "Imported from substrate: substrate_packages_fts_docsize_6eeadfabb..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"id\": 6, \"sz\": \"0603010104033513\"}" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 24: substrate_packages_fts_config_...
  { recordId := "substrate_packages_fts_config_6efa245bf49d1682"
    kind := .ingestAttestation
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992683"
    sessionRef := "legacy_import_substrate"
    title := "packages_fts_config record"
    summary := "Imported from substrate: substrate_packages_fts_config_6efa245bf4..."
    artifacts := 
      [ { path := "data/substrate_index.db", role := .related, artifactType := .dataFile, summary := "{\"k\": \"version\", \"v\": 4}" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 25: graph_manifold_registry_836bd1...
  { recordId := "graph_manifold_registry_836bd1c7bfeea606"
    kind := .bootAttestation
    source := .ptosBootSession
    timestamp := "2026-04-18T01:08:03.992924"
    sessionRef := "legacy_import_graph_address"
    title := "Graph OS manifold_registry manifest"
    summary := "Imported from graph_address: graph_manifold_registry_836bd1c7bfeea606..."
    artifacts := 
      [ { path := "data/graph_address_space.sql", role := .related, artifactType := .dataFile, summary := "{\"address_index\": \"b58f88b7f51ab4e7\", \"relevance_bucket\": \"12\", \"merkle_root_sha256\": \"b58f88b7f51ab4e7e3ec8e6cf6269d19a58e9cb98f0b556f70ece57e5df0c98" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 26: json_ingestion_catalog_downloa...
  { recordId := "json_ingestion_catalog_downloads_2026-04-12_0_1312e1353eb77447"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.992986"
    sessionRef := "legacy_import_json_manifest"
    title := "ingestion_catalog_downloads_2026-04-12 entry 0"
    summary := "Imported from json_manifest: json_ingestion_catalog_downloads_2026-04..."
    artifacts := 
      [ { path := "data/ingestion_catalog_downloads_2026-04-12.json", role := .related, artifactType := .dataFile, summary := "{\"source_path\": \"/home/allaun/Downloads/data/Downloads_from_internet\", \"ingestion_date\": \"2026-04-12\", \"ingestion_timestamp\": \"2026-04-12T21:55:00-05:" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 27: json_ingestion_catalog_downloa...
  { recordId := "json_ingestion_catalog_downloads_2026-04-12_1_2c95accc08bc6893"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993001"
    sessionRef := "legacy_import_json_manifest"
    title := "ingestion_catalog_downloads_2026-04-12 entry 1"
    summary := "Imported from json_manifest: json_ingestion_catalog_downloads_2026-04..."
    artifacts := 
      [ { path := "data/ingestion_catalog_downloads_2026-04-12.json", role := .related, artifactType := .dataFile, summary := "{\"academic_papers\": {\"count\": 14, \"extensions\": [\".pdf\"], \"description\": \"Scientific papers from arXiv, Nature, Science Advances, Optica\"}, \"code_arti" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 28: json_ingestion_catalog_downloa...
  { recordId := "json_ingestion_catalog_downloads_2026-04-12_2_466f7cbdb9b52405"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993008"
    sessionRef := "legacy_import_json_manifest"
    title := "ingestion_catalog_downloads_2026-04-12 entry 2"
    summary := "Imported from json_manifest: json_ingestion_catalog_downloads_2026-04..."
    artifacts := 
      [ { path := "data/ingestion_catalog_downloads_2026-04-12.json", role := .related, artifactType := .dataFile, summary := "{\"filename\": \"canonical.py\", \"sha256\": \"6bc7c4a16c0c2c9e1c2d8e5b3f8a9d7e6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0\", \"size_bytes\": 18427, \"type\": \"python_scrip" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 29: json_ingestion_catalog_downloa...
  { recordId := "json_ingestion_catalog_downloads_2026-04-12_3_426cc36cd32e3d29"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993013"
    sessionRef := "legacy_import_json_manifest"
    title := "ingestion_catalog_downloads_2026-04-12 entry 3"
    summary := "Imported from json_manifest: json_ingestion_catalog_downloads_2026-04..."
    artifacts := 
      [ { path := "data/ingestion_catalog_downloads_2026-04-12.json", role := .related, artifactType := .dataFile, summary := "{\"filename\": \"relation_mask_trainer.rs\", \"sha256\": \"85e1f79eb72a04937457d33e4d20e2b1102d50cce98923e9c6daec9a58f989b9\", \"size_bytes\": 11683, \"type\": \"r" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 30: json_ingestion_catalog_downloa...
  { recordId := "json_ingestion_catalog_downloads_2026-04-12_4_5ba96312eab58cb0"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993018"
    sessionRef := "legacy_import_json_manifest"
    title := "ingestion_catalog_downloads_2026-04-12 entry 4"
    summary := "Imported from json_manifest: json_ingestion_catalog_downloads_2026-04..."
    artifacts := 
      [ { path := "data/ingestion_catalog_downloads_2026-04-12.json", role := .related, artifactType := .dataFile, summary := "{\"filename\": \"pbacs_core.py\", \"sha256\": \"dc0fd105fcce1fc0d04a2f3c8f50a73cbe503b64d85eefcaf671f7e25f15c4df\", \"size_bytes\": 7018, \"type\": \"python_script" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 31: json_ingestion_catalog_downloa...
  { recordId := "json_ingestion_catalog_downloads_2026-04-12_5_ea8d594b026470d7"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993022"
    sessionRef := "legacy_import_json_manifest"
    title := "ingestion_catalog_downloads_2026-04-12 entry 5"
    summary := "Imported from json_manifest: json_ingestion_catalog_downloads_2026-04..."
    artifacts := 
      [ { path := "data/ingestion_catalog_downloads_2026-04-12.json", role := .related, artifactType := .dataFile, summary := "{\"filename\": \"ROOT_SPEC_V2.md\", \"sha256\": \"6365597947d8958c248c7cb4b58a59156e4f9d18d816c94306b433cb4d3c84aa\", \"size_bytes\": 4345, \"type\": \"specificati" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 32: json_ingestion_catalog_downloa...
  { recordId := "json_ingestion_catalog_downloads_2026-04-12_6_f5286891fa35730d"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993026"
    sessionRef := "legacy_import_json_manifest"
    title := "ingestion_catalog_downloads_2026-04-12 entry 6"
    summary := "Imported from json_manifest: json_ingestion_catalog_downloads_2026-04..."
    artifacts := 
      [ { path := "data/ingestion_catalog_downloads_2026-04-12.json", role := .related, artifactType := .dataFile, summary := "{\"filename\": \"PROJECTION_BASIS_THEOREM.md\", \"sha256\": \"ca5ca8456eb81c906ab0feafa1d502f055a83718cda7c36816618ca697acf0c2\", \"size_bytes\": 2966, \"type\": " } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 33: json_ingestion_catalog_downloa...
  { recordId := "json_ingestion_catalog_downloads_2026-04-12_7_12dddf4f347ccec5"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993030"
    sessionRef := "legacy_import_json_manifest"
    title := "ingestion_catalog_downloads_2026-04-12 entry 7"
    summary := "Imported from json_manifest: json_ingestion_catalog_downloads_2026-04..."
    artifacts := 
      [ { path := "data/ingestion_catalog_downloads_2026-04-12.json", role := .related, artifactType := .dataFile, summary := "{\"filename\": \"PCM_PIPEWIRE_PROFILE_V1.md\", \"sha256\": \"1c3717528ebcdb167fd83b159307890383ad7c0b6414194d00d00a5f4414b8f6\", \"size_bytes\": 2181, \"type\": \"" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 34: json_ingestion_catalog_downloa...
  { recordId := "json_ingestion_catalog_downloads_2026-04-12_8_1d9f8fd118c3dee1"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993034"
    sessionRef := "legacy_import_json_manifest"
    title := "ingestion_catalog_downloads_2026-04-12 entry 8"
    summary := "Imported from json_manifest: json_ingestion_catalog_downloads_2026-04..."
    artifacts := 
      [ { path := "data/ingestion_catalog_downloads_2026-04-12.json", role := .related, artifactType := .dataFile, summary := "{\"filename\": \"arXiv-2506.15521v1.tar.gz\", \"sha256\": \"f289c56330b5cec1a51cf80c2e2e886d83ea26681ab55f6880d0b7562654d673\", \"size_bytes\": 6510541, \"type\":" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 35: json_ingestion_catalog_downloa...
  { recordId := "json_ingestion_catalog_downloads_2026-04-12_9_e4f748ce33541c9f"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993038"
    sessionRef := "legacy_import_json_manifest"
    title := "ingestion_catalog_downloads_2026-04-12 entry 9"
    summary := "Imported from json_manifest: json_ingestion_catalog_downloads_2026-04..."
    artifacts := 
      [ { path := "data/ingestion_catalog_downloads_2026-04-12.json", role := .related, artifactType := .dataFile, summary := "{\"filename\": \"2506.15521v1.pdf\", \"sha256\": \"7424264\", \"size_bytes\": 7424264, \"type\": \"academic_paper\", \"priority\": \"medium\", \"description\": \"ArXiv pap" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 36: json_ingestion_catalog_downloa...
  { recordId := "json_ingestion_catalog_downloads_2026-04-12_10_bf7af5a86badc7a8"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993042"
    sessionRef := "legacy_import_json_manifest"
    title := "ingestion_catalog_downloads_2026-04-12 entry 10"
    summary := "Imported from json_manifest: json_ingestion_catalog_downloads_2026-04..."
    artifacts := 
      [ { path := "data/ingestion_catalog_downloads_2026-04-12.json", role := .related, artifactType := .dataFile, summary := "{\"filename\": \"reddit.mp4\", \"sha256\": \"dda201c83c9e104a0bfbcb26040b6f49646c47990e33db58dc954799e66a9421\", \"size_bytes\": 73990421, \"type\": \"video\", \"pri" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 37: json_ingestion_catalog_downloa...
  { recordId := "json_ingestion_catalog_downloads_2026-04-12_11_77b51df5aad9ebc9"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993046"
    sessionRef := "legacy_import_json_manifest"
    title := "ingestion_catalog_downloads_2026-04-12 entry 11"
    summary := "Imported from json_manifest: json_ingestion_catalog_downloads_2026-04..."
    artifacts := 
      [ { path := "data/ingestion_catalog_downloads_2026-04-12.json", role := .related, artifactType := .dataFile, summary := "{\"filename\": \"semi-trailer-container-20-truck-1.snapshot.1.zip\", \"sha256\": \"b35764032d511afeaf9cdfeea8a9f35f3f5ac7c656bf7b02004c5e8ad000e5eb\", \"size_b" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 38: json_ingestion_catalog_downloa...
  { recordId := "json_ingestion_catalog_downloads_2026-04-12_12_e585af03a1ce2906"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993050"
    sessionRef := "legacy_import_json_manifest"
    title := "ingestion_catalog_downloads_2026-04-12 entry 12"
    summary := "Imported from json_manifest: json_ingestion_catalog_downloads_2026-04..."
    artifacts := 
      [ { path := "data/ingestion_catalog_downloads_2026-04-12.json", role := .related, artifactType := .dataFile, summary := "{\"sovereign_stack_related\": 23, \"academic_research\": 14, \"test_artifacts\": 8, \"protocol_specifications\": 12, \"media_large_files\": 9, \"unknown\": 21, \"_" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 39: json_ingestion_catalog_downloa...
  { recordId := "json_ingestion_catalog_downloads_2026-04-12_13_a84558acfb56a4b8"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993053"
    sessionRef := "legacy_import_json_manifest"
    title := "ingestion_catalog_downloads_2026-04-12 entry 13"
    summary := "Imported from json_manifest: json_ingestion_catalog_downloads_2026-04..."
    artifacts := 
      [ { path := "data/ingestion_catalog_downloads_2026-04-12.json", role := .related, artifactType := .dataFile, summary := "{\"source\": \"Downloads from internet - mixed academic, code, and media\", \"verification\": \"SHA256 hashes computed for all files\", \"integrity\": \"pending_" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 40: json_event_catalog_0_9a112df0c...
  { recordId := "json_event_catalog_0_9a112df0cd8ebebc"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993212"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 0"
    summary := "Imported from json_manifest: json_event_catalog_0_9a112df0cd8ebebc..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"version\": \"1.0\", \"description\": \"Canonical catalog of major global economic, financial, geopolitical, and structural events for surprise-mechanics c" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 41: json_event_catalog_1_a8b70c12e...
  { recordId := "json_event_catalog_1_a8b70c12e6af838b"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993218"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 1"
    summary := "Imported from json_manifest: json_event_catalog_1_a8b70c12e6af838b..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"black_tuesday_1929\", \"date\": \"1929-10-29\", \"label\": \"Black Tuesday \\u2014 Great Crash\", \"description\": \"S&P Composite falls 11.7% on record vo" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 42: json_event_catalog_2_f25fac396...
  { recordId := "json_event_catalog_2_f25fac396168160d"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993223"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 2"
    summary := "Imported from json_manifest: json_event_catalog_2_f25fac396168160d..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"uk_leaves_gold_1931\", \"date\": \"1931-09-21\", \"label\": \"UK abandons gold standard\", \"description\": \"Bank of England suspends pound convertibilit" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 43: json_event_catalog_3_365b766ac...
  { recordId := "json_event_catalog_3_365b766ac80144f8"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993227"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 3"
    summary := "Imported from json_manifest: json_event_catalog_3_365b766ac80144f8..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"fdr_bank_holiday_1933\", \"date\": \"1933-03-06\", \"label\": \"FDR bank holiday\", \"description\": \"Roosevelt closes all US banks for four days to stop" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 44: json_event_catalog_4_ffbb5b874...
  { recordId := "json_event_catalog_4_ffbb5b874e850920"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993231"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 4"
    summary := "Imported from json_manifest: json_event_catalog_4_ffbb5b874e850920..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"wwii_begins_1939\", \"date\": \"1939-09-01\", \"label\": \"WWII begins \\u2014 Germany invades Poland\", \"description\": \"Wehrmacht crosses the Polish bo" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 45: json_event_catalog_5_d437eb115...
  { recordId := "json_event_catalog_5_d437eb115e6e62c6"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993237"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 5"
    summary := "Imported from json_manifest: json_event_catalog_5_d437eb115e6e62c6..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"pearl_harbor_1941\", \"date\": \"1941-12-08\", \"label\": \"Pearl Harbor \\u2014 US enters WWII\", \"description\": \"Japan attacks US Pacific Fleet; NYSE " } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 46: json_event_catalog_6_917b2439f...
  { recordId := "json_event_catalog_6_917b2439fc1b54cd"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993242"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 6"
    summary := "Imported from json_manifest: json_event_catalog_6_917b2439fc1b54cd..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"ve_day_1945\", \"date\": \"1945-05-08\", \"label\": \"VE Day \\u2014 Germany surrenders\", \"description\": \"Nazi Germany unconditional surrender ends war" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 47: json_event_catalog_7_0d728087e...
  { recordId := "json_event_catalog_7_0d728087ea0f9983"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993246"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 7"
    summary := "Imported from json_manifest: json_event_catalog_7_0d728087ea0f9983..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"vj_day_1945\", \"date\": \"1945-08-15\", \"label\": \"VJ Day \\u2014 Japan surrenders\", \"description\": \"Emperor Hirohito announces Japan's surrender; W" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 48: json_event_catalog_8_95eec2d83...
  { recordId := "json_event_catalog_8_95eec2d83baf3f76"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993250"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 8"
    summary := "Imported from json_manifest: json_event_catalog_8_95eec2d83baf3f76..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"suez_crisis_1956\", \"date\": \"1956-11-05\", \"label\": \"Suez Crisis \\u2014 UK/France invasion\", \"description\": \"Anglo-French forces land at Suez Ca" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 49: json_event_catalog_9_a47ea7479...
  { recordId := "json_event_catalog_9_a47ea7479cbe19ab"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993254"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 9"
    summary := "Imported from json_manifest: json_event_catalog_9_a47ea7479cbe19ab..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"cuban_missile_crisis_1962\", \"date\": \"1962-10-22\", \"label\": \"Cuban Missile Crisis \\u2014 Kennedy televised address\", \"description\": \"Kennedy an" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 50: json_event_catalog_10_037a4245...
  { recordId := "json_event_catalog_10_037a4245cdb108b4"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993258"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 10"
    summary := "Imported from json_manifest: json_event_catalog_10_037a4245cdb108b4..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"jfk_assassination_1963\", \"date\": \"1963-11-22\", \"label\": \"JFK assassination\", \"description\": \"Kennedy shot in Dallas; NYSE halted 2:07pm, loses" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 51: json_event_catalog_11_587dd30e...
  { recordId := "json_event_catalog_11_587dd30eeabf7993"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993263"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 11"
    summary := "Imported from json_manifest: json_event_catalog_11_587dd30eeabf7993..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"nixon_shock_1971\", \"date\": \"1971-08-16\", \"label\": \"Nixon shock \\u2014 end of Bretton Woods\", \"description\": \"Nixon suspends dollar convertibil" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 52: json_event_catalog_12_8a77dc9a...
  { recordId := "json_event_catalog_12_8a77dc9ae09d4cdc"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993267"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 12"
    summary := "Imported from json_manifest: json_event_catalog_12_8a77dc9ae09d4cdc..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"opec_embargo_1973\", \"date\": \"1973-10-17\", \"label\": \"OPEC oil embargo begins\", \"description\": \"Arab OPEC members embargo oil to US, Netherlands" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 53: json_event_catalog_13_aa263262...
  { recordId := "json_event_catalog_13_aa26326257e4c78c"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993271"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 13"
    summary := "Imported from json_manifest: json_event_catalog_13_aa26326257e4c78c..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"volcker_shock_1979\", \"date\": \"1979-10-06\", \"label\": \"Volcker shock \\u2014 Fed rate spike\", \"description\": \"Fed Chair Volcker announces shift t" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 54: json_event_catalog_14_b12bfa49...
  { recordId := "json_event_catalog_14_b12bfa496cee9fc8"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993276"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 14"
    summary := "Imported from json_manifest: json_event_catalog_14_b12bfa496cee9fc8..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"iran_revolution_1979\", \"date\": \"1979-01-16\", \"label\": \"Iranian Revolution \\u2014 Shah flees\", \"description\": \"Shah Mohammad Reza Pahlavi flees" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 55: json_event_catalog_15_9e2ab77a...
  { recordId := "json_event_catalog_15_9e2ab77a5658cbe4"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993281"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 15"
    summary := "Imported from json_manifest: json_event_catalog_15_9e2ab77a5658cbe4..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"mexico_debt_crisis_1982\", \"date\": \"1982-08-12\", \"label\": \"Mexico debt crisis \\u2014 peso default\", \"description\": \"Mexico declares it cannot s" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 56: json_event_catalog_16_2a56164f...
  { recordId := "json_event_catalog_16_2a56164fa9fa97e7"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993285"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 16"
    summary := "Imported from json_manifest: json_event_catalog_16_2a56164fa9fa97e7..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"plaza_accord_1985\", \"date\": \"1985-09-22\", \"label\": \"Plaza Accord \\u2014 coordinated dollar devaluation\", \"description\": \"G5 finance ministers " } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 57: json_event_catalog_17_ef61dc9c...
  { recordId := "json_event_catalog_17_ef61dc9c46824636"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993290"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 17"
    summary := "Imported from json_manifest: json_event_catalog_17_ef61dc9c46824636..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"black_monday_1987\", \"date\": \"1987-10-19\", \"label\": \"Black Monday \\u2014 S&P -20.5% single day\", \"description\": \"Largest single-day percentage " } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 58: json_event_catalog_18_eba36b52...
  { recordId := "json_event_catalog_18_eba36b523d8854ab"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993294"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 18"
    summary := "Imported from json_manifest: json_event_catalog_18_eba36b523d8854ab..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"tiananmen_1989\", \"date\": \"1989-06-04\", \"label\": \"Tiananmen Square massacre\", \"description\": \"PLA moves against protesters in Beijing; internat" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 59: json_event_catalog_19_e84412b7...
  { recordId := "json_event_catalog_19_e84412b7a2dae722"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993298"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 19"
    summary := "Imported from json_manifest: json_event_catalog_19_e84412b7a2dae722..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"berlin_wall_1989\", \"date\": \"1989-11-09\", \"label\": \"Fall of the Berlin Wall\", \"description\": \"East Germany opens borders; Berlin Wall falls. Tr" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 60: json_event_catalog_20_5d7b5396...
  { recordId := "json_event_catalog_20_5d7b5396672702c6"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993302"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 20"
    summary := "Imported from json_manifest: json_event_catalog_20_5d7b5396672702c6..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"nikkei_peak_1989\", \"date\": \"1989-12-29\", \"label\": \"Nikkei all-time high \\u2014 Japan bubble peak\", \"description\": \"Nikkei closes at 38,957. Ja" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 61: json_event_catalog_21_c68d0b72...
  { recordId := "json_event_catalog_21_c68d0b729bf78114"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993306"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 21"
    summary := "Imported from json_manifest: json_event_catalog_21_c68d0b729bf78114..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"nikkei_crash_1990\", \"date\": \"1990-01-04\", \"label\": \"Nikkei crash begins \\u2014 Japan bubble bursts\", \"description\": \"First trading day of 1990" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 62: json_event_catalog_22_e0aa9393...
  { recordId := "json_event_catalog_22_e0aa93931d35fb17"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993310"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 22"
    summary := "Imported from json_manifest: json_event_catalog_22_e0aa93931d35fb17..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"gulf_war_1991\", \"date\": \"1991-01-17\", \"label\": \"Gulf War \\u2014 Operation Desert Storm\", \"description\": \"Coalition air campaign begins. Oil pr" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 63: json_event_catalog_23_32bbcc76...
  { recordId := "json_event_catalog_23_32bbcc76b6bca782"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993314"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 23"
    summary := "Imported from json_manifest: json_event_catalog_23_32bbcc76b6bca782..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"ussr_dissolution_1991\", \"date\": \"1991-12-25\", \"label\": \"USSR officially dissolved\", \"description\": \"Gorbachev resigns; Soviet Union ceases to " } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 64: json_event_catalog_24_5ba6b693...
  { recordId := "json_event_catalog_24_5ba6b693682d9138"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993318"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 24"
    summary := "Imported from json_manifest: json_event_catalog_24_5ba6b693682d9138..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"black_wednesday_1992\", \"date\": \"1992-09-16\", \"label\": \"Black Wednesday \\u2014 GBP exits ERM\", \"description\": \"UK forced out of European Exchan" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 65: json_event_catalog_25_ec7b4b46...
  { recordId := "json_event_catalog_25_ec7b4b465c2d07e8"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993322"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 25"
    summary := "Imported from json_manifest: json_event_catalog_25_ec7b4b465c2d07e8..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"tequila_crisis_1994\", \"date\": \"1994-12-20\", \"label\": \"Mexico Tequila Crisis\", \"description\": \"Mexico devalues peso, triggering capital flight " } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 66: json_event_catalog_26_d18d4269...
  { recordId := "json_event_catalog_26_d18d4269d0b9facd"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993327"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 26"
    summary := "Imported from json_manifest: json_event_catalog_26_d18d4269d0b9facd..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"kobe_earthquake_1995\", \"date\": \"1995-01-17\", \"label\": \"Kobe earthquake \\u2014 Great Hanshin\", \"description\": \"6,434 killed; \\u00a510T ($100B) " } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 67: json_event_catalog_27_46416a4d...
  { recordId := "json_event_catalog_27_46416a4d29e477f8"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993331"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 27"
    summary := "Imported from json_manifest: json_event_catalog_27_46416a4d29e477f8..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"barings_collapse_1995\", \"date\": \"1995-02-26\", \"label\": \"Barings Bank collapse \\u2014 Nick Leeson\", \"description\": \"Oldest merchant bank in UK " } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 68: json_event_catalog_28_1e850bd0...
  { recordId := "json_event_catalog_28_1e850bd0a936b8ed"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993336"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 28"
    summary := "Imported from json_manifest: json_event_catalog_28_1e850bd0a936b8ed..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"asian_crisis_thai_baht_1997\", \"date\": \"1997-07-02\", \"label\": \"Asian Crisis \\u2014 Thai baht devaluation\", \"description\": \"Thailand abandons ba" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 69: json_event_catalog_29_f12f699c...
  { recordId := "json_event_catalog_29_f12f699cc535e8d0"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993340"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 29"
    summary := "Imported from json_manifest: json_event_catalog_29_f12f699cc535e8d0..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"russia_default_1998\", \"date\": \"1998-08-17\", \"label\": \"Russia default / ruble devaluation\", \"description\": \"Russia defaults on domestic debt an" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 70: json_event_catalog_30_e4b369c4...
  { recordId := "json_event_catalog_30_e4b369c45f52fe26"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993344"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 30"
    summary := "Imported from json_manifest: json_event_catalog_30_e4b369c45f52fe26..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"ltcm_bailout_1998\", \"date\": \"1998-09-23\", \"label\": \"LTCM bailout arranged by Federal Reserve\", \"description\": \"Fed organizes $3.6B private sec" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 71: json_event_catalog_31_afe77674...
  { recordId := "json_event_catalog_31_afe77674019523f6"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993348"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 31"
    summary := "Imported from json_manifest: json_event_catalog_31_afe77674019523f6..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"euro_launch_1999\", \"date\": \"1999-01-04\", \"label\": \"Euro launched\", \"description\": \"Euro introduced as accounting currency for 11 EU member sta" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 72: json_event_catalog_32_39325e18...
  { recordId := "json_event_catalog_32_39325e1800d29465"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993352"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 32"
    summary := "Imported from json_manifest: json_event_catalog_32_39325e1800d29465..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"dotcom_peak_2000\", \"date\": \"2000-03-10\", \"label\": \"NASDAQ all-time high \\u2014 dot-com peak\", \"description\": \"NASDAQ Composite closes at 5,048" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 73: json_event_catalog_33_ad40ad53...
  { recordId := "json_event_catalog_33_ad40ad53702a0b34"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993356"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 33"
    summary := "Imported from json_manifest: json_event_catalog_33_ad40ad53702a0b34..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"9_11_attacks_2001\", \"date\": \"2001-09-11\", \"label\": \"9/11 terrorist attacks\", \"description\": \"Twin Towers and Pentagon attacked. NYSE/NASDAQ cl" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 74: json_event_catalog_34_81deda3a...
  { recordId := "json_event_catalog_34_81deda3a43e3389e"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993361"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 34"
    summary := "Imported from json_manifest: json_event_catalog_34_81deda3a43e3389e..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"enron_bankruptcy_2001\", \"date\": \"2001-12-02\", \"label\": \"Enron bankruptcy\", \"description\": \"Largest US bankruptcy at time; exposes fraudulent a" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 75: json_event_catalog_35_5b6815af...
  { recordId := "json_event_catalog_35_5b6815af2d9309fa"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993365"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 35"
    summary := "Imported from json_manifest: json_event_catalog_35_5b6815af2d9309fa..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"argentina_default_2001\", \"date\": \"2001-12-23\", \"label\": \"Argentina default \\u2014 $100B\", \"description\": \"Largest sovereign default in history" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 76: json_event_catalog_36_4df600ad...
  { recordId := "json_event_catalog_36_4df600adb80ad9c3"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993369"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 36"
    summary := "Imported from json_manifest: json_event_catalog_36_4df600adb80ad9c3..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"iraq_war_2003\", \"date\": \"2003-03-20\", \"label\": \"Iraq War begins \\u2014 Operation Iraqi Freedom\", \"description\": \"US-led coalition invades Iraq" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 77: json_event_catalog_37_7220dba0...
  { recordId := "json_event_catalog_37_7220dba0d7708937"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993373"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 37"
    summary := "Imported from json_manifest: json_event_catalog_37_7220dba0d7708937..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"sars_global_emergency_2003\", \"date\": \"2003-04-16\", \"label\": \"SARS declared global emergency by WHO\", \"description\": \"WHO declares SARS a world" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 78: json_event_catalog_38_0a6fe1e1...
  { recordId := "json_event_catalog_38_0a6fe1e1e0fee2fb"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993377"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 38"
    summary := "Imported from json_manifest: json_event_catalog_38_0a6fe1e1e0fee2fb..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"indian_ocean_tsunami_2004\", \"date\": \"2004-12-26\", \"label\": \"Indian Ocean tsunami \\u2014 230,000 killed\", \"description\": \"Deadliest natural dis" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 79: json_event_catalog_39_d92ba8f5...
  { recordId := "json_event_catalog_39_d92ba8f53b1cc68e"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993381"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 39"
    summary := "Imported from json_manifest: json_event_catalog_39_d92ba8f53b1cc68e..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"bnp_paribas_freeze_2007\", \"date\": \"2007-08-09\", \"label\": \"BNP Paribas freezes subprime funds\", \"description\": \"BNP Paribas suspends three inve" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 80: json_event_catalog_40_819b3833...
  { recordId := "json_event_catalog_40_819b38334db0603b"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993385"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 40"
    summary := "Imported from json_manifest: json_event_catalog_40_819b38334db0603b..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"northern_rock_run_2007\", \"date\": \"2007-09-14\", \"label\": \"Northern Rock bank run \\u2014 first in UK since 1866\", \"description\": \"Customers queu" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 81: json_event_catalog_41_33871492...
  { recordId := "json_event_catalog_41_33871492e17d86d7"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993390"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 41"
    summary := "Imported from json_manifest: json_event_catalog_41_33871492e17d86d7..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"bear_stearns_2008\", \"date\": \"2008-03-14\", \"label\": \"Bear Stearns collapse \\u2014 Fed emergency intervention\", \"description\": \"Fed arranges JPM" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 82: json_event_catalog_42_16b10ec8...
  { recordId := "json_event_catalog_42_16b10ec81d9f5a14"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993394"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 42"
    summary := "Imported from json_manifest: json_event_catalog_42_16b10ec81d9f5a14..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"lehman_bankruptcy_2008\", \"date\": \"2008-09-15\", \"label\": \"Lehman Brothers bankruptcy\", \"description\": \"Largest bankruptcy in US history ($691B " } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 83: json_event_catalog_43_94e7e052...
  { recordId := "json_event_catalog_43_94e7e052607d418a"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993398"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 43"
    summary := "Imported from json_manifest: json_event_catalog_43_94e7e052607d418a..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"tarp_rejection_2008\", \"date\": \"2008-09-29\", \"label\": \"US Congress rejects TARP \\u2014 S&P -8.8%\", \"description\": \"House votes 228-205 against " } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 84: json_event_catalog_44_b99d83e0...
  { recordId := "json_event_catalog_44_b99d83e0cd1c2ca9"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993402"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 44"
    summary := "Imported from json_manifest: json_event_catalog_44_b99d83e0cd1c2ca9..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"coordinated_rate_cuts_2008\", \"date\": \"2008-10-08\", \"label\": \"Seven central banks simultaneous rate cuts\", \"description\": \"Fed, ECB, Bank of En" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 85: json_event_catalog_45_ed38e065...
  { recordId := "json_event_catalog_45_ed38e0657d0b2d9d"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993406"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 45"
    summary := "Imported from json_manifest: json_event_catalog_45_ed38e0657d0b2d9d..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"sp500_gfc_low_2009\", \"date\": \"2009-03-09\", \"label\": \"S&P 500 GFC low \\u2014 666 points\", \"description\": \"S&P 500 closes at 676.53 (intraday lo" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 86: json_event_catalog_46_684c0c72...
  { recordId := "json_event_catalog_46_684c0c72885f3032"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993410"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 46"
    summary := "Imported from json_manifest: json_event_catalog_46_684c0c72885f3032..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"flash_crash_2010\", \"date\": \"2010-05-06\", \"label\": \"Flash Crash \\u2014 Dow -1000 intraday\", \"description\": \"US equity markets plunge 9% and rec" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 87: json_event_catalog_47_12caf712...
  { recordId := "json_event_catalog_47_12caf712b88699dd"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993415"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 47"
    summary := "Imported from json_manifest: json_event_catalog_47_12caf712b88699dd..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"greece_bailout_2010\", \"date\": \"2010-04-23\", \"label\": \"Greece requests first EU/IMF bailout\", \"description\": \"Greece formally requests \\u20ac45" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 88: json_event_catalog_48_d0364c8e...
  { recordId := "json_event_catalog_48_d0364c8e0c32baae"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993419"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 48"
    summary := "Imported from json_manifest: json_event_catalog_48_d0364c8e0c32baae..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"fukushima_2011\", \"date\": \"2011-03-11\", \"label\": \"Fukushima nuclear disaster \\u2014 Japan earthquake\", \"description\": \"9.1 magnitude earthquake" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 89: json_event_catalog_49_188ae82b...
  { recordId := "json_event_catalog_49_188ae82b25879962"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993423"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 49"
    summary := "Imported from json_manifest: json_event_catalog_49_188ae82b25879962..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"sp_downgrades_us_2011\", \"date\": \"2011-08-05\", \"label\": \"S&P downgrades US credit rating\", \"description\": \"First-ever downgrade of US sovereign" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 90: json_event_catalog_50_ceda873c...
  { recordId := "json_event_catalog_50_ceda873c1ab72554"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993427"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 50"
    summary := "Imported from json_manifest: json_event_catalog_50_ceda873c1ab72554..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"taper_tantrum_2013\", \"date\": \"2013-05-22\", \"label\": \"Taper Tantrum \\u2014 Bernanke hints at tapering\", \"description\": \"Bernanke tells Congress" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 91: json_event_catalog_51_62896986...
  { recordId := "json_event_catalog_51_6289698622a3b285"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993431"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 51"
    summary := "Imported from json_manifest: json_event_catalog_51_6289698622a3b285..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"mtgox_collapse_2014\", \"date\": \"2014-02-24\", \"label\": \"Mt. Gox Bitcoin exchange collapses\", \"description\": \"Mt. Gox files for bankruptcy with 8" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 92: json_event_catalog_52_41b60df7...
  { recordId := "json_event_catalog_52_41b60df74fd7d43e"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993435"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 52"
    summary := "Imported from json_manifest: json_event_catalog_52_41b60df74fd7d43e..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"russia_crimea_2014\", \"date\": \"2014-03-18\", \"label\": \"Russia annexes Crimea\", \"description\": \"Russia formally annexes Crimea after military occ" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 93: json_event_catalog_53_61bfbe70...
  { recordId := "json_event_catalog_53_61bfbe702d95aae7"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993439"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 53"
    summary := "Imported from json_manifest: json_event_catalog_53_61bfbe702d95aae7..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"greece_capital_controls_2015\", \"date\": \"2015-06-29\", \"label\": \"Greece capital controls imposed\", \"description\": \"Greek banks closed; \\u20ac60/" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 94: json_event_catalog_54_4bd26961...
  { recordId := "json_event_catalog_54_4bd26961a2b0d47b"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993444"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 54"
    summary := "Imported from json_manifest: json_event_catalog_54_4bd26961a2b0d47b..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"china_black_monday_2015\", \"date\": \"2015-08-24\", \"label\": \"China Black Monday \\u2014 CSI -8.5%\", \"description\": \"Shanghai Composite falls 8.5% " } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 95: json_event_catalog_55_85603359...
  { recordId := "json_event_catalog_55_856033598fc24524"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993448"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 55"
    summary := "Imported from json_manifest: json_event_catalog_55_856033598fc24524..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"brexit_referendum_2016\", \"date\": \"2016-06-24\", \"label\": \"Brexit referendum result\", \"description\": \"UK votes 52% to leave EU. GBP/USD falls 10" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 96: json_event_catalog_56_fa3736c9...
  { recordId := "json_event_catalog_56_fa3736c91d5bdfb7"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993452"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 56"
    summary := "Imported from json_manifest: json_event_catalog_56_fa3736c91d5bdfb7..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"trump_election_2016\", \"date\": \"2016-11-09\", \"label\": \"Trump 2016 election \\u2014 surprise result\", \"description\": \"Trump defeats Clinton; S&P " } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 97: json_event_catalog_57_b729b2c6...
  { recordId := "json_event_catalog_57_b729b2c67382d5fa"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993456"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 57"
    summary := "Imported from json_manifest: json_event_catalog_57_b729b2c67382d5fa..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"btc_peak_2017\", \"date\": \"2017-12-17\", \"label\": \"Bitcoin all-time high $20K \\u2014 first bubble peak\", \"description\": \"Bitcoin reaches $19,891;" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 98: json_event_catalog_58_77564fa4...
  { recordId := "json_event_catalog_58_77564fa4a4ff5a97"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993460"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 58"
    summary := "Imported from json_manifest: json_event_catalog_58_77564fa4a4ff5a97..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"volmageddon_2018\", \"date\": \"2018-02-05\", \"label\": \"Volmageddon \\u2014 VIX spike and inverse-VIX collapse\", \"description\": \"VIX jumps from 17 t" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 99: json_event_catalog_59_4d149e50...
  { recordId := "json_event_catalog_59_4d149e50511c9107"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993464"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 59"
    summary := "Imported from json_manifest: json_event_catalog_59_4d149e50511c9107..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"us_china_trade_war_2018\", \"date\": \"2018-03-22\", \"label\": \"US-China trade war \\u2014 Section 301 tariffs\", \"description\": \"Trump announces $60B" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 100: json_event_catalog_60_4db208d9...
  { recordId := "json_event_catalog_60_4db208d9fd09b023"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993469"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 60"
    summary := "Imported from json_manifest: json_event_catalog_60_4db208d9fd09b023..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"covid_wuhan_2019\", \"date\": \"2019-12-31\", \"label\": \"First COVID-19 cluster reported \\u2014 Wuhan\", \"description\": \"Chinese authorities report m" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 101: json_event_catalog_61_18ba7b37...
  { recordId := "json_event_catalog_61_18ba7b372d9d6fe3"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993473"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 61"
    summary := "Imported from json_manifest: json_event_catalog_61_18ba7b372d9d6fe3..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"covid_global_crash_2020\", \"date\": \"2020-02-20\", \"label\": \"COVID-19 global market crash begins\", \"description\": \"S&P 500 begins fastest-ever 30" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 102: json_event_catalog_62_2b5f6aa6...
  { recordId := "json_event_catalog_62_2b5f6aa6729a795a"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993477"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 62"
    summary := "Imported from json_manifest: json_event_catalog_62_2b5f6aa6729a795a..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"covid_black_thursday_2020\", \"date\": \"2020-03-12\", \"label\": \"COVID crash \\u2014 S&P -9.5% single day\", \"description\": \"S&P falls 9.51%; markets" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 103: json_event_catalog_63_7c8d2a69...
  { recordId := "json_event_catalog_63_7c8d2a697d15adb5"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993481"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 63"
    summary := "Imported from json_manifest: json_event_catalog_63_7c8d2a697d15adb5..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"covid_market_low_2020\", \"date\": \"2020-03-23\", \"label\": \"COVID market low \\u2014 S&P 2237\", \"description\": \"S&P 500 closes at 2237.40; -34% fro" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 104: json_event_catalog_64_bb42aae8...
  { recordId := "json_event_catalog_64_bb42aae8d921bd26"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993485"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 64"
    summary := "Imported from json_manifest: json_event_catalog_64_bb42aae8d921bd26..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"oil_goes_negative_2020\", \"date\": \"2020-04-20\", \"label\": \"WTI crude goes negative \\u2014 -$37/barrel\", \"description\": \"WTI May 2020 futures con" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 105: json_event_catalog_65_b7600fe8...
  { recordId := "json_event_catalog_65_b7600fe8eae53e42"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993490"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 65"
    summary := "Imported from json_manifest: json_event_catalog_65_b7600fe8eae53e42..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"pfizer_vaccine_2020\", \"date\": \"2020-11-09\", \"label\": \"Pfizer announces 90%+ effective COVID vaccine\", \"description\": \"Pfizer/BioNTech announce" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 106: json_event_catalog_66_1cbb1e4d...
  { recordId := "json_event_catalog_66_1cbb1e4df30224df"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993494"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 66"
    summary := "Imported from json_manifest: json_event_catalog_66_1cbb1e4df30224df..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"gamestop_squeeze_2021\", \"date\": \"2021-01-27\", \"label\": \"GameStop short squeeze peak \\u2014 WallStreetBets\", \"description\": \"GME peaks at $347;" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 107: json_event_catalog_67_10c02289...
  { recordId := "json_event_catalog_67_10c02289336711f2"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993498"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 67"
    summary := "Imported from json_manifest: json_event_catalog_67_10c02289336711f2..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"btc_eth_crypto_ath_2021\", \"date\": \"2021-11-10\", \"label\": \"BTC/ETH crypto all-time highs \\u2014 $69K/$4830\", \"description\": \"Bitcoin reaches $6" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 108: json_event_catalog_68_56779a33...
  { recordId := "json_event_catalog_68_56779a3393dd396b"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993503"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 68"
    summary := "Imported from json_manifest: json_event_catalog_68_56779a3393dd396b..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"russia_ukraine_war_2022\", \"date\": \"2022-02-24\", \"label\": \"Russia invades Ukraine \\u2014 full-scale war\", \"description\": \"Russia launches multi" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 109: json_event_catalog_69_f2eb4508...
  { recordId := "json_event_catalog_69_f2eb4508ec759157"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993508"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 69"
    summary := "Imported from json_manifest: json_event_catalog_69_f2eb4508ec759157..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"russia_moex_halt_2022\", \"date\": \"2022-02-25\", \"label\": \"Moscow Exchange halts trading \\u2014 sanctions shock\", \"description\": \"Bank of Russia " } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 110: json_event_catalog_70_516c4cdd...
  { recordId := "json_event_catalog_70_516c4cddc2e1dc0a"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993512"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 70"
    summary := "Imported from json_manifest: json_event_catalog_70_516c4cddc2e1dc0a..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"russia_moex_reopen_2022\", \"date\": \"2022-03-24\", \"label\": \"Moscow Exchange partially reopens \\u2014 ~50% lower\", \"description\": \"IMOEX resumes " } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 111: json_event_catalog_71_86b2c54a...
  { recordId := "json_event_catalog_71_86b2c54ad7f5c234"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993516"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 71"
    summary := "Imported from json_manifest: json_event_catalog_71_86b2c54ad7f5c234..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"fed_75bp_hike_2022\", \"date\": \"2022-06-15\", \"label\": \"Fed hikes 75bp \\u2014 largest since 1994\", \"description\": \"First 75bp Fed hike since Nove" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 112: json_event_catalog_72_20bf7969...
  { recordId := "json_event_catalog_72_20bf7969fe1547ed"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993520"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 72"
    summary := "Imported from json_manifest: json_event_catalog_72_20bf7969fe1547ed..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"luna_terra_collapse_2022\", \"date\": \"2022-05-12\", \"label\": \"Luna/Terra $40B collapse\", \"description\": \"TerraUSD algorithmic stablecoin depegs; " } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 113: json_event_catalog_73_8e764b62...
  { recordId := "json_event_catalog_73_8e764b6233e01777"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993524"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 73"
    summary := "Imported from json_manifest: json_event_catalog_73_8e764b6233e01777..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"ethereum_merge_2022\", \"date\": \"2022-09-15\", \"label\": \"Ethereum Merge \\u2014 PoW to PoS\", \"description\": \"Ethereum transitions from Proof-of-Wo" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 114: json_event_catalog_74_64944266...
  { recordId := "json_event_catalog_74_64944266c073081f"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993528"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 74"
    summary := "Imported from json_manifest: json_event_catalog_74_64944266c073081f..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"uk_mini_budget_ldi_2022\", \"date\": \"2022-09-23\", \"label\": \"UK mini-budget LDI crisis \\u2014 GBP record low\", \"description\": \"Truss/Kwarteng ann" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 115: json_event_catalog_75_646912de...
  { recordId := "json_event_catalog_75_646912de3ec9bca9"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993533"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 75"
    summary := "Imported from json_manifest: json_event_catalog_75_646912de3ec9bca9..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"ftx_bankruptcy_2022\", \"date\": \"2022-11-11\", \"label\": \"FTX bankruptcy \\u2014 Bankman-Fried\", \"description\": \"FTX files for Chapter 11; ~$8B cus" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 116: json_event_catalog_76_0b227b6d...
  { recordId := "json_event_catalog_76_0b227b6d5b0a269e"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993537"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 76"
    summary := "Imported from json_manifest: json_event_catalog_76_0b227b6d5b0a269e..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"svb_collapse_2023\", \"date\": \"2023-03-10\", \"label\": \"Silicon Valley Bank collapse\", \"description\": \"16th-largest US bank fails in 48 hours afte" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 117: json_event_catalog_77_fce31dba...
  { recordId := "json_event_catalog_77_fce31dbaa81c78e1"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993541"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 77"
    summary := "Imported from json_manifest: json_event_catalog_77_fce31dbaa81c78e1..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"credit_suisse_collapse_2023\", \"date\": \"2023-03-19\", \"label\": \"Credit Suisse emergency acquisition by UBS\", \"description\": \"167-year-old Swiss " } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 118: json_event_catalog_78_4e9998aa...
  { recordId := "json_event_catalog_78_4e9998aa860319a1"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993545"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 78"
    summary := "Imported from json_manifest: json_event_catalog_78_4e9998aa860319a1..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"bitcoin_etf_approval_2024\", \"date\": \"2024-01-10\", \"label\": \"US spot Bitcoin ETF approved \\u2014 SEC ruling\", \"description\": \"SEC approves 11 s" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 119: json_event_catalog_79_03422f73...
  { recordId := "json_event_catalog_79_03422f7364c8c230"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993549"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 79"
    summary := "Imported from json_manifest: json_event_catalog_79_03422f7364c8c230..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"yen_carry_unwind_2024\", \"date\": \"2024-08-05\", \"label\": \"Yen carry trade unwind \\u2014 global equity drop\", \"description\": \"Bank of Japan hike " } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 120: json_event_catalog_80_8222d459...
  { recordId := "json_event_catalog_80_8222d459b512d973"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993554"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 80"
    summary := "Imported from json_manifest: json_event_catalog_80_8222d459b512d973..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"trump_tariffs_liberation_day_2025\", \"date\": \"2025-04-02\", \"label\": \"Liberation Day \\u2014 global tariffs announced\", \"description\": \"Trump ann" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 121: json_event_catalog_81_734e6924...
  { recordId := "json_event_catalog_81_734e6924a1a4e9a6"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993562"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 81"
    summary := "Imported from json_manifest: json_event_catalog_81_734e6924a1a4e9a6..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"ai_hyperscaler_energy_inflection_2025\", \"date\": \"2025-01-01\", \"label\": \"AI/LLM hyperscaler energy demand \\u2014 structural inflection\", \"descr" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 122: json_event_catalog_82_623a2c0a...
  { recordId := "json_event_catalog_82_623a2c0a098a2777"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993570"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 82"
    summary := "Imported from json_manifest: json_event_catalog_82_623a2c0a098a2777..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"wti_curve_bifurcation_2026\", \"date\": \"2026-03-20\", \"label\": \"WTI futures curve bifurcates \\u2014 Iran/Hormuz shock\", \"description\": \"On or aro" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 123: json_event_catalog_83_b5f2ccde...
  { recordId := "json_event_catalog_83_b5f2ccdec39d7e85"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993578"
    sessionRef := "legacy_import_json_manifest"
    title := "event_catalog entry 83"
    summary := "Imported from json_manifest: json_event_catalog_83_b5f2ccdec39d7e85..."
    artifacts := 
      [ { path := "data/event_catalog.json", role := .related, artifactType := .dataFile, summary := "{\"id\": \"openai_circular_financing_2026\", \"date\": \"2026-03-16\", \"label\": \"OpenAI circular financing structure revealed \\u2014 pre-IPO\", \"description\": " } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 124: json_transport_lut_0_a2bab09b0...
  { recordId := "json_transport_lut_0_a2bab09b0d9d2b5d"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993644"
    sessionRef := "legacy_import_json_manifest"
    title := "transport_lut entry 0"
    summary := "Imported from json_manifest: json_transport_lut_0_a2bab09b0d9d2b5d..."
    artifacts := 
      [ { path := "data/transport_lut.json", role := .related, artifactType := .dataFile, summary := "{\"v\": \"1.2\", \"desc\": \"Transport LUT with full fallback chains and OMNITOKEN fragmentation map\", \"count\": 47, \"enc\": \"base36\", \"_manifest_key\": \"meta\"}" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 125: json_transport_lut_1_752fdf99b...
  { recordId := "json_transport_lut_1_752fdf99b1ef4cbb"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993700"
    sessionRef := "legacy_import_json_manifest"
    title := "transport_lut entry 1"
    summary := "Imported from json_manifest: json_transport_lut_1_752fdf99b1ef4cbb..."
    artifacts := 
      [ { path := "data/transport_lut.json", role := .related, artifactType := .dataFile, summary := "{\"TCP\": {\"f\": \"RFC793\", \"s\": [\"RFC9293\", \"RFC5681\", \"RFC7323\", \"RFC8684\", \"RFC8985\", \"RFC5925\"], \"c\": \"core\", \"t\": \"stream\"}, \"UDP\": {\"f\": \"RFC768\", \"" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 126: json_transport_lut_2_e8a9558a3...
  { recordId := "json_transport_lut_2_e8a9558a3fa4e50c"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993709"
    sessionRef := "legacy_import_json_manifest"
    title := "transport_lut entry 2"
    summary := "Imported from json_manifest: json_transport_lut_2_e8a9558a3fa4e50c..."
    artifacts := 
      [ { path := "data/transport_lut.json", role := .related, artifactType := .dataFile, summary := "{\"core\": [\"TCP\", \"UDP\", \"UDPLite\", \"SCTP\", \"DCCP\"], \"modern\": [\"QUIC\"], \"ext\": [\"MPTCP\"], \"cc\": [\"LEDBAT\", \"TFRC\", \"CUBIC\", \"L4S\", \"DCTCP\", \"SCReAM\", " } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 127: json_secret_sub_registers_0_61...
  { recordId := "json_secret_sub_registers_0_6137b94dfba7ee6b"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993754"
    sessionRef := "legacy_import_json_manifest"
    title := "secret_sub_registers entry 0"
    summary := "Imported from json_manifest: json_secret_sub_registers_0_6137b94dfba7..."
    artifacts := 
      [ { path := "data/secret_sub_registers.json", role := .related, artifactType := .dataFile, summary := "{\"sub_register_id\": \"subreg_6580c2cd3ed2\", \"target_register\": \"R00\", \"foam_score\": -0.000171, \"nd_point\": [2.2754899156599455e+18, -1.901738162092724e" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 128: json_secret_sub_registers_1_38...
  { recordId := "json_secret_sub_registers_1_3822dcbf74fda506"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993764"
    sessionRef := "legacy_import_json_manifest"
    title := "secret_sub_registers entry 1"
    summary := "Imported from json_manifest: json_secret_sub_registers_1_3822dcbf74fd..."
    artifacts := 
      [ { path := "data/secret_sub_registers.json", role := .related, artifactType := .dataFile, summary := "{\"sub_register_id\": \"subreg_bb5f5f0b3b74\", \"target_register\": \"R05\", \"foam_score\": -0.000171, \"nd_point\": [-1.5111063315059196e+19, -4.921361567032248" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 129: json_secret_sub_registers_2_06...
  { recordId := "json_secret_sub_registers_2_0660f79baf9ac66a"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993772"
    sessionRef := "legacy_import_json_manifest"
    title := "secret_sub_registers entry 2"
    summary := "Imported from json_manifest: json_secret_sub_registers_2_0660f79baf9a..."
    artifacts := 
      [ { path := "data/secret_sub_registers.json", role := .related, artifactType := .dataFile, summary := "{\"sub_register_id\": \"subreg_7378e8fdc276\", \"target_register\": \"R00\", \"foam_score\": -0.000171, \"nd_point\": [-1.7629348035374208e+17, 8.694728912461402e" } ]
    auditCorrections := []
    verificationResults := [] }
,  -- Imported record 130: json_secret_sub_registers_3_64...
  { recordId := "json_secret_sub_registers_3_64fd58349c3ed6a6"
    kind := .researchSession
    source := .archivedResearchSession
    timestamp := "2026-04-18T01:08:03.993779"
    sessionRef := "legacy_import_json_manifest"
    title := "secret_sub_registers entry 3"
    summary := "Imported from json_manifest: json_secret_sub_registers_3_64fd58349c3e..."
    artifacts := 
      [ { path := "data/secret_sub_registers.json", role := .related, artifactType := .dataFile, summary := "{\"sub_register_id\": \"subreg_3ba786689738\", \"target_register\": \"R10\", \"foam_score\": -0.000171, \"nd_point\": [-7.922500224989327e+18, -5.853250055086345e" } ]
    auditCorrections := []
    verificationResults := [] }]

/-- Total count of imported records. -/
def importedCount : Nat := 131

/-- Hash of all imported content for integrity verification. -/
def importIntegrityHash : String := "1dba0812cbf3829e"

end ExtensionScaffold.ENE.ENEImport
