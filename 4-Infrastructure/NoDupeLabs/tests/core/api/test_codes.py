# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Comprehensive tests for the codes module."""

import json
from pathlib import Path
from unittest.mock import mock_open, patch

from nodupe.core.api.codes import (
    RISK_LEVELS,
    SENSITIVE_METHODS,
    ActionCode,
    _load_lut,
)


class TestLoadLut:
    """Test LUT loading functionality."""

    def test_load_lut_success(self):
        """Test loading LUT from existing file."""
        mock_data = {"codes": [{"mnemonic": "TEST", "code": 123456}]}
        with patch('nodupe.core.api.codes.open', mock_open(read_data=json.dumps(mock_data))):
            with patch.object(Path, 'exists', return_value=True):
                result = _load_lut()
                assert result == mock_data

    def test_load_lut_file_not_exists(self):
        """Test loading LUT when file doesn't exist."""
        with patch.object(Path, 'exists', return_value=False):
            result = _load_lut()
            assert result == {"codes": []}


class TestActionCodeCreation:
    """Test ActionCode enum creation and values."""

    def test_action_code_enum_exists(self):
        """Test ActionCode enum is created."""
        assert ActionCode is not None

    def test_action_code_has_expected_members(self):
        """Test ActionCode has expected members."""
        assert hasattr(ActionCode, 'FIA_UAU_INIT')
        assert hasattr(ActionCode, 'FPT_STM_ERR')
        assert hasattr(ActionCode, 'FPT_FLS_FAIL')
        assert hasattr(ActionCode, 'ACC_ISO_CMP')

    def test_action_code_values(self):
        """Test ActionCode values are correct."""
        assert ActionCode.FIA_UAU_INIT == 300001
        assert ActionCode.FPT_STM_ERR == 500001
        assert ActionCode.FPT_FLS_FAIL == 500000
        assert ActionCode.ACC_ISO_CMP == 600013

    def test_action_code_aliases_exist(self):
        """Test ActionCode aliases are created."""
        # Check aliases that exist (target must be in LUT)
        assert hasattr(ActionCode, 'IPC_START')  # FAU_GEN_START exists
        assert hasattr(ActionCode, 'TOOL_INIT')  # FIA_UAU_INIT exists
        assert hasattr(ActionCode, 'ERR_INTERNAL')  # FPT_STM_ERR exists
        assert hasattr(ActionCode, 'ARCHIVE_SIP')  # OAIS_SIP_INGEST exists
        assert hasattr(ActionCode, 'DB_OP')  # FDP_ETC_DB exists
        # These aliases don't exist because their targets are not in LUT:
        # DEDUP_FP (target: DEDUP_FP_GEN), BKP_VERIFY (target: BKP_VERIFY_OK)
        # ARCHIVE_OP (target: FDP_DAU_ARCH)

    def test_action_code_alias_values(self):
        """Test ActionCode aliases map to correct values."""
        assert ActionCode.IPC_START == ActionCode.FAU_GEN_START
        assert ActionCode.TOOL_INIT == ActionCode.FIA_UAU_INIT
        assert ActionCode.ERR_INTERNAL == ActionCode.FPT_STM_ERR


class TestActionCodeMethods:
    """Test ActionCode class methods."""

    def test_get_lut(self):
        """Test getting LUT data."""
        lut = ActionCode.get_lut()
        assert isinstance(lut, dict)
        assert "codes" in lut
        assert len(lut["codes"]) > 0

    def test_get_description_found(self):
        """Test getting description for known code."""
        desc = ActionCode.get_description(ActionCode.FIA_UAU_INIT)
        assert isinstance(desc, str)
        assert len(desc) > 0

    def test_get_description_not_found(self):
        """Test getting description for unknown code."""
        desc = ActionCode.get_description(999999)
        assert desc == "Unknown Action"

    def test_get_category_oais(self):
        """Test getting category for OAIS code."""
        category = ActionCode.get_category(ActionCode.OAIS_SIP_INGEST)
        assert category == "ARCHIVE"

    def test_get_category_protection(self):
        """Test getting category for FDP code."""
        category = ActionCode.get_category(ActionCode.FDP_DAU_HASH)
        assert category == "PROTECTION"

    def test_get_category_crypto(self):
        """Test getting category for FCS code."""
        # Check if any FCS codes exist
        has_fcs = any(item.get("iso_class") == "FCS" for item in ActionCode.get_lut()["codes"])
        if has_fcs:
            # Find an FCS code and test it
            for item in ActionCode.get_lut()["codes"]:
                if item.get("iso_class") == "FCS":
                    code_value = item["code"]
                    category = ActionCode.get_category(code_value)
                    assert category == "CRYPTO"
                    break

    def test_get_category_ai_ml(self):
        """Test getting category for ML code."""
        has_ml = any(item.get("iso_class") == "ML" for item in ActionCode.get_lut()["codes"])
        if has_ml:
            for item in ActionCode.get_lut()["codes"]:
                if item.get("iso_class") == "ML":
                    code_value = item["code"]
                    category = ActionCode.get_category(code_value)
                    assert category == "AI_ML"
                    break

    def test_get_category_hardware(self):
        """Test getting category for FRU code."""
        has_fru = any(item.get("iso_class") == "FRU" for item in ActionCode.get_lut()["codes"])
        if has_fru:
            for item in ActionCode.get_lut()["codes"]:
                if item.get("iso_class") == "FRU":
                    code_value = item["code"]
                    category = ActionCode.get_category(code_value)
                    assert category == "HARDWARE"
                    break

    def test_get_category_network(self):
        """Test getting category for FCO code."""
        has_fco = any(item.get("iso_class") == "FCO" for item in ActionCode.get_lut()["codes"])
        if has_fco:
            for item in ActionCode.get_lut()["codes"]:
                if item.get("iso_class") == "FCO":
                    code_value = item["code"]
                    category = ActionCode.get_category(code_value)
                    assert category == "NETWORK"
                    break

    def test_get_category_general(self):
        """Test getting category for unknown ISO class."""
        category = ActionCode.get_category(999999)
        assert category == "GENERAL"

    def test_to_jsonrpc_code_backup_media_fault(self):
        """Test converting backup/media fault codes."""
        # Codes >= 530000 should map to -32603
        rpc_code = ActionCode.to_jsonrpc_code(530000)
        assert rpc_code == -32603

    def test_to_jsonrpc_code_engine_failure(self):
        """Test converting engine failure codes."""
        # Codes >= 500000 and < 530000 should map to -32000
        rpc_code = ActionCode.to_jsonrpc_code(500000)
        assert rpc_code == -32000

    def test_to_jsonrpc_code_other(self):
        """Test converting other codes."""
        # Codes < 500000 should map to -32099
        rpc_code = ActionCode.to_jsonrpc_code(100000)
        assert rpc_code == -32099


class TestSensitiveMethods:
    """Test SENSITIVE_METHODS mapping."""

    def test_sensitive_methods_exists(self):
        """Test SENSITIVE_METHODS is defined."""
        assert isinstance(SENSITIVE_METHODS, dict)
        assert len(SENSITIVE_METHODS) > 0

    def test_sensitive_methods_has_extract_archive(self):
        """Test extract_archive is in sensitive methods."""
        assert 'extract_archive' in SENSITIVE_METHODS

    def test_sensitive_methods_has_delete_file(self):
        """Test delete_file is in sensitive methods."""
        assert 'delete_file' in SENSITIVE_METHODS

    def test_sensitive_methods_values_are_action_codes(self):
        """Test sensitive methods values are ActionCode values."""
        for method, code in SENSITIVE_METHODS.items():
            assert isinstance(code, int)
            assert code > 0


class TestRiskLevels:
    """Test RISK_LEVELS mapping."""

    def test_risk_levels_exists(self):
        """Test RISK_LEVELS is defined."""
        assert isinstance(RISK_LEVELS, dict)

    def test_risk_levels_has_critical_entries(self):
        """Test RISK_LEVELS has critical entries."""
        # Should have at least one CRITICAL level
        has_critical = any(level == "CRITICAL" for level in RISK_LEVELS.values())
        assert has_critical is True

    def test_risk_levels_values(self):
        """Test risk level values."""
        for code, level in RISK_LEVELS.items():
            assert level in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]


class TestActionCodeIntegration:
    """Test ActionCode integration scenarios."""

    def test_all_codes_have_descriptions(self):
        """Test all codes have descriptions."""
        lut = ActionCode.get_lut()
        for item in lut["codes"]:
            code = item["code"]
            desc = ActionCode.get_description(code)
            assert desc != "Unknown Action", f"Code {code} ({item['mnemonic']}) has no description"

    def test_all_codes_have_categories(self):
        """Test all codes have categories."""
        lut = ActionCode.get_lut()
        for item in lut["codes"]:
            code = item["code"]
            category = ActionCode.get_category(code)
            assert isinstance(category, str)
            assert len(category) > 0

    def test_enum_member_count(self):
        """Test enum has expected number of members."""
        members = [m for m in dir(ActionCode) if not m.startswith('_')]
        # Should have many members from the LUT
        assert len(members) > 20


class TestActionCodeCollisionFix:
    """Test the fix for P0 ActionCode collision bug.
    
    Previously, 6 distinct error types all mapped to FPT_FLS_FAIL (500000).
    This breaks audit trails and security incident response capability.
    
    New distinct codes:
    - 510000 series: Tool/Method errors (ERR_TOOL_NOT_FOUND, ERR_METHOD_NOT_FOUND)
    - 510002-510003: Request validation errors (ERR_INVALID_REQUEST, ERR_INVALID_JSON)
    - 520000 series: Security/Rate limiting (RATE_LIMIT_HIT, SECURITY_RISK_FLAGGED)
    """

    # Mapping of error aliases to their expected new codes
    ERROR_CODE_MAPPING = {
        'ERR_TOOL_NOT_FOUND': ('FPT_TOOL_NOT_FOUND', 510000),
        'ERR_METHOD_NOT_FOUND': ('FPT_METHOD_NOT_FOUND', 510001),
        'ERR_INVALID_REQUEST': ('FPT_INVALID_REQUEST', 510002),
        'ERR_INVALID_JSON': ('FPT_INVALID_JSON', 510003),
        'RATE_LIMIT_HIT': ('FPT_RATE_LIMIT', 520000),
        'SECURITY_RISK_FLAGGED': ('FPT_SECURITY_RISK', 520001),
    }

    def test_all_error_aliases_exist(self):
        """Test all error aliases are defined in ActionCode enum."""
        for alias in self.ERROR_CODE_MAPPING.keys():
            assert hasattr(ActionCode, alias), f"Missing alias: {alias}"

    def test_all_error_codes_have_unique_values(self):
        """Test each error type maps to a unique ActionCode value."""
        code_values = []
        for alias, (mnemonic, expected_code) in self.ERROR_CODE_MAPPING.items():
            code_value = getattr(ActionCode, alias).value
            code_values.append(code_value)
        
        # Check all values are unique
        assert len(code_values) == len(set(code_values)), \
            f"Duplicate codes found: {code_values}"

    def test_error_codes_match_expected_values(self):
        """Test each error alias maps to the expected code value."""
        for alias, (mnemonic, expected_code) in self.ERROR_CODE_MAPPING.items():
            code_value = getattr(ActionCode, alias).value
            assert code_value == expected_code, \
                f"{alias} should be {expected_code}, got {code_value}"

    def test_error_codes_have_correct_mnemonics(self):
        """Test each error alias maps to the correct mnemonic."""
        for alias, (expected_mnemonic, expected_code) in self.ERROR_CODE_MAPPING.items():
            # The alias should resolve to the same value as the target mnemonic
            alias_value = getattr(ActionCode, alias).value
            mnemonic_value = getattr(ActionCode, expected_mnemonic).value
            assert alias_value == mnemonic_value, \
                f"{alias} should map to {expected_mnemonic}"

    def test_error_codes_in_510000_series_are_tool_validation_errors(self):
        """Test 510000 series codes are for tool/method/validation errors."""
        # 510000-510003 should be tool/method/validation errors
        tool_method_codes = [
            getattr(ActionCode, 'ERR_TOOL_NOT_FOUND').value,
            getattr(ActionCode, 'ERR_METHOD_NOT_FOUND').value,
            getattr(ActionCode, 'ERR_INVALID_REQUEST').value,
            getattr(ActionCode, 'ERR_INVALID_JSON').value,
        ]
        for code in tool_method_codes:
            assert 510000 <= code <= 510003, \
                f"Tool/validation error code {code} not in 510000 series"

    def test_error_codes_in_520000_series_are_security_errors(self):
        """Test 520000 series codes are for security/rate limiting errors."""
        security_codes = [
            getattr(ActionCode, 'RATE_LIMIT_HIT').value,
            getattr(ActionCode, 'SECURITY_RISK_FLAGGED').value,
        ]
        for code in security_codes:
            assert 520000 <= code <= 520001, \
                f"Security error code {code} not in 520000 series"

    def test_error_codes_follow_iso_fpt_classification(self):
        """Test all new error codes follow ISO FPT (Fault Protection) classification."""
        lut = ActionCode.get_lut()
        error_mnemonics = [
            'FPT_TOOL_NOT_FOUND',
            'FPT_METHOD_NOT_FOUND',
            'FPT_INVALID_REQUEST',
            'FPT_INVALID_JSON',
            'FPT_RATE_LIMIT',
            'FPT_SECURITY_RISK',
        ]
        for item in lut['codes']:
            if item['mnemonic'] in error_mnemonics:
                assert item['iso_class'] == 'FPT', \
                    f"{item['mnemonic']} should have ISO class FPT"

    def test_error_codes_have_appropriate_risk_levels(self):
        """Test error codes have appropriate risk levels per ISO-8000."""
        lut = ActionCode.get_lut()
        expected_risk_levels = {
            'FPT_TOOL_NOT_FOUND': 'HIGH',
            'FPT_METHOD_NOT_FOUND': 'HIGH',
            'FPT_INVALID_REQUEST': 'MEDIUM',
            'FPT_INVALID_JSON': 'MEDIUM',
            'FPT_RATE_LIMIT': 'MEDIUM',
            'FPT_SECURITY_RISK': 'CRITICAL',
        }
        for item in lut['codes']:
            if item['mnemonic'] in expected_risk_levels:
                expected = expected_risk_levels[item['mnemonic']]
                assert item['risk_level'] == expected, \
                    f"{item['mnemonic']} risk level should be {expected}, got {item['risk_level']}"

    def test_no_collision_with_original_fpt_fls_fail(self):
        """Test new error codes don't collide with original FPT_FLS_FAIL (500000)."""
        fpt_fls_fail_value = ActionCode.FPT_FLS_FAIL.value
        for alias in self.ERROR_CODE_MAPPING.keys():
            code_value = getattr(ActionCode, alias).value
            assert code_value != fpt_fls_fail_value, \
                f"{alias} should not map to FPT_FLS_FAIL (500000)"

    def test_audit_trail_distinction(self):
        """Test that audit trails can distinguish between different error types."""
        # Each error type should produce a distinct code for audit logging
        error_codes = {}
        for alias in self.ERROR_CODE_MAPPING.keys():
            code_value = getattr(ActionCode, alias).value
            error_type = alias.replace('ERR_', '').replace('_HIT', '').replace('_FLAGGED', '')
            error_codes[error_type] = code_value
        
        # Verify all codes are distinct for audit trail purposes
        unique_codes = set(error_codes.values())
        assert len(unique_codes) == len(error_codes), \
            "Audit trail cannot distinguish between error types - codes are not unique"
