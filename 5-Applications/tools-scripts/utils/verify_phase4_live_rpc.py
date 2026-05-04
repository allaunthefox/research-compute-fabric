#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
"""Verification for Phase 4: Live RPC Integration.

This script mocks RPC responses to verify the full 'Live Fetching' loop
in the OmniToken action bot.
"""

import json
import unittest
from unittest.mock import patch, MagicMock
import httpx

# Import the components
from scripts.rpc_bytecode_fetcher import RPCBytecodeFetcher
from scripts.legal_omnitoken_action_bot import canal_route_reason

class TestPhase4(unittest.TestCase):

    def setUp(self):
        self.fetcher = RPCBytecodeFetcher(config_path="4-Infrastructure/config/rpc_endpoints.json")
        self.sample_address = "0x1234567890123456789012345678901234567890"
        self.sample_bytecode = "0x6060604052600436106100415760003560e01c806306661abd1461004657"

    @patch("httpx.Client.post")
    def test_fetch_success(self, mock_post):
        """Verify successful bytecode fetching via mock RPC."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"jsonrpc": "2.0", "result": self.sample_bytecode, "id": 1}
        mock_post.return_value = mock_response

        bytecode = self.fetcher.fetch_bytecode(self.sample_address, "ethereum")
        self.assertEqual(bytecode, self.sample_bytecode)
        print(f"PASS: Successfully fetched mock bytecode for {self.sample_address}")

    @patch("httpx.Client.post")
    def test_fetch_fail_rpc_error(self, mock_post):
        """Verify fail-closed behavior on RPC error."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"jsonrpc": "2.0", "error": {"code": -32000, "message": "Server error"}, "id": 1}
        mock_post.return_value = mock_response

        bytecode = self.fetcher.fetch_bytecode(self.sample_address, "ethereum")
        self.assertIsNone(bytecode)
        print("PASS: Correctly returned None on RPC error (Fail-Closed)")

    @patch("httpx.Client.post")
    def test_bot_integration_live_fetch(self, mock_post):
        """Verify the bot correctly triggers live fetching when bytecode is missing."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"jsonrpc": "2.0", "result": self.sample_bytecode, "id": 1}
        mock_post.return_value = mock_response

        candidate = {
            "payout_intent_id": "test-live-001",
            "target_contract_address": self.sample_address,
            "target_chain": "ethereum"
        }
        
        reason = canal_route_reason(candidate, fetcher=self.fetcher)
        # Should NOT be None if fetching worked and analysis ran
        self.assertIsNotNone(reason)
        # Should be a STRUCTURAL_GRAIN_REVIEW or similar given the sample bytecode
        self.assertIn("Structural", reason["message"])
        print("PASS: Bot correctly integrated with Live RPC Fetcher")

if __name__ == "__main__":
    unittest.main()
