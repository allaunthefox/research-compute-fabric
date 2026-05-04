# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Coverage tests for nodupe/core/api/codes.py."""

import os
from unittest.mock import mock_open, patch

import pytest

from nodupe.core.api.codes import ActionCode, _load_lut


def test_load_lut_missing_file():
    """Test _load_lut when the file is missing (line 18)."""
    with patch("nodupe.core.api.codes.Path.exists", return_value=False):
        result = _load_lut()
        assert result == {"codes": []}

def test_get_description():
    """Test ActionCode.get_description (line 91)."""
    # Assuming FIA_UAU_INIT exists in lut.json
    desc = ActionCode.get_description(ActionCode.FIA_UAU_INIT)
    assert desc != "Unknown Action"
    
    # Test unknown code
    assert ActionCode.get_description(999999) == "Unknown Action"

def test_get_category():
    """Test ActionCode.get_category (lines 94-114)."""
    # Test mapped category
    cat = ActionCode.get_category(ActionCode.FIA_UAU_INIT)
    # FIA is not in the mapping (OAIS, FDP, FCS, ML, FRU, FCO) so it should return GENERAL
    assert cat == "GENERAL"
    
    # Test OAIS mapping
    # We need to find an OAIS code in lut.json. Assuming OAIS_SIP_INGEST is there.
    if hasattr(ActionCode, "OAIS_SIP_INGEST"):
        assert ActionCode.get_category(ActionCode.OAIS_SIP_INGEST) == "ARCHIVE"

    # Test unknown code
    assert ActionCode.get_category(999999) == "GENERAL"

def test_to_jsonrpc_code():
    """Test ActionCode.to_jsonrpc_code (lines 118-120)."""
    assert ActionCode.to_jsonrpc_code(530000) == -32603
    assert ActionCode.to_jsonrpc_code(500000) == -32000
    assert ActionCode.to_jsonrpc_code(100000) == -32099

def test_get_lut():
    """Test ActionCode.get_lut."""
    lut = ActionCode.get_lut()
    assert "codes" in lut
