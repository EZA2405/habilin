"""Reproduce the real sandbox tools without a model or browser dependency."""
import argparse
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from habilin.core import EstateAgent, Principal, digest


def replay():
    with tempfile.TemporaryDirectory() as directory:
        agent = EstateAgent(Path(directory)/"estate.db")
        operator = Principal("demo-operator", "operator", "EST-001")
        professional = Principal("demo-cpa", "professional", "EST-001")
        owner = Principal("demo-owner", "owner", "EST-001")
        case = agent.advance(operator)
        packet_hash = digest(case["packet"])
        agent.tool(professional, "professional_approve", packet_hash=packet_hash, confirmed=True)
        agent.tool(owner, "owner_approve", packet_hash=packet_hash, confirmed=True, code=agent.issue_code())
        assert agent.advance(operator)["stage"] == "filing_unknown"
        assert agent.advance(operator)["stage"] == "payment_pending"
        case = agent.advance(operator)
        assert case["stage"] == "completed" and case["balance_centavos"] == 85_000_000
        with agent.connection() as db:
            assert db.execute("SELECT count(*) FROM payments").fetchone()[0] == 1
            assert db.execute("SELECT count(*) FROM submissions").fetchone()[0] == 1
        return {"recorded_at":datetime.now(timezone.utc).isoformat(), "mode":"offline tool replay; no model call", "case":case}


if __name__ == "__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path,required=True);args=parser.parse_args()
    result=replay();args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2))
    print("Verified: one filing, one settled PHP150,000 sandbox payment; eCAR/title transfer remain open.")
