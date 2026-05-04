import os
import tempfile

from nodupe.tools.database.features import DatabaseShardingTool


def test_sharding_describe_and_cli_create_list(tmp_path, capsys):
    tool = DatabaseShardingTool(config={"db_path": str(tmp_path)})

    # describe_usage should contain Usage
    desc = tool.describe_usage()
    assert "Usage" in desc

    # running standalone with no args should return 1 and print usage
    rc = tool.run_standalone([])
    captured = capsys.readouterr()
    assert rc == 1
    assert "Usage" in captured.out

    # create a shard via CLI
    rc = tool.run_standalone(["create", "s1"])
    assert rc == 0
    # listing should include the created shard
    rc = tool.run_standalone(["list"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "s1" in captured.out
