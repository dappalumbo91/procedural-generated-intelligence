from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pgi.engine import unfold
from pgi.journal import append_journal
from pgi.model import Request, Rule
from pgi.packs.base import add_lines
from pgi.scenes import covered_rain, demo_text, ice_and_dusk, warm_rain
from pgi.version import RULE_VERSION


def run(request: Request, **kwargs):
    kwargs.setdefault("use_store", False)
    return unfold(request, **kwargs)


def signature(session) -> tuple:
    return tuple((claim.rule_id, claim.atom, claim.because) for claim in session.claims)


def risk_order(text: str) -> tuple[str, ...]:
    found = []
    for line in text.splitlines():
        if "[causal.risk_" in line:
            found.append(line.split("[", 1)[1].split("]", 1)[0])
    return tuple(found)


class UnfoldTests(unittest.TestCase):
    def test_derived_seed_is_stable_and_fact_order_does_not_matter(self) -> None:
        first = run(Request(ask="why is the path risky?", facts=("rain", "above freezing")))
        second = run(Request(ask="why is the path risky?", facts=("above_freezing", "rain")))
        third = run(Request(ask="why is the path risky?", facts=("rain", "above_freezing"), seed=first.seed))
        self.assertEqual(first.seed, second.seed)
        self.assertEqual(first.text(lod=2), second.text(lod=2))
        self.assertEqual(first.text(lod=2), third.text(lod=2))
        self.assertEqual(first.rule_version, RULE_VERSION)

    def test_rule_version_changes_a_derived_seed_only(self) -> None:
        plain = Request(ask="why is the path risky?", facts=("rain", "above_freezing"))
        self.assertNotEqual(
            run(plain, rule_version="pgi-0.1.0").seed,
            run(plain, rule_version="pgi-9.9.9").seed,
        )
        pinned = Request(ask="why is the path risky?", facts=("rain", "above_freezing"), seed=5)
        self.assertEqual(run(pinned, rule_version="a").seed, 5)
        self.assertEqual(signature(run(pinned, rule_version="a")), signature(run(pinned, rule_version="b")))

    def test_seed_reorders_reasons_and_keeps_the_claim_set(self) -> None:
        signatures = set()
        orders = set()
        for seed in range(12):
            session = run(ice_and_dusk(seed=seed))
            signatures.add(signature(session))
            orders.add(risk_order(session.text(lod=1)))
        self.assertEqual(len(signatures), 1)
        self.assertGreater(len(orders), 1)

    def test_warm_rain_chain(self) -> None:
        session = run(warm_rain())
        self.assertEqual(
            [claim.rule_id for claim in session.claims],
            ["causal.wet_from_rain", "causal.slip_water", "causal.risk_traction"],
        )
        self.assertEqual(session.open_gaps, ())
        self.assertEqual(session.clashes, ())

    def test_detail_variant_follows_the_seed(self) -> None:
        seen = set()
        for seed in range(24):
            text = run(warm_rain(seed=seed)).text(lod=2)
            surface = "cuts friction" in text
            film = "carries the step" in text
            self.assertNotEqual(surface, film)
            self.assertNotIn("cuts friction", run(warm_rain(seed=seed)).text(lod=1))
            seen.add("surface" if surface else "film")
        self.assertEqual(seen, {"surface", "film"})

    def test_lod_zero_is_an_outline_and_zoom_opens_one_node(self) -> None:
        session = run(warm_rain(lod=0))
        outline = session.text(lod=0)
        self.assertIn("Ground condition follows", outline)
        self.assertNotIn("wet(ground)", outline)
        self.assertNotIn("Rain wets open ground", outline)
        close = session.text(lod=1)
        self.assertIn("wet(ground) because rain", close)
        self.assertNotIn("cuts friction", close)
        self.assertNotIn("carries the step", close)
        zoomed = session.text(lod=1, zoom={"causal.slip_water": 2})
        self.assertTrue(("cuts friction" in zoomed) or ("carries the step" in zoomed))
        self.assertNotIn("frozen film", zoomed)
        self.assertEqual(signature(session), signature(run(warm_rain(lod=2))))

    def test_covered_path_stays_dry(self) -> None:
        session = run(covered_rain())
        atoms = {claim.atom for claim in session.claims}
        self.assertIn("dry(ground)", atoms)
        self.assertIn("settled(no_traction_risk)", atoms)
        self.assertNotIn("wet(ground)", atoms)
        self.assertNotIn("risk(path)", atoms)
        self.assertEqual(session.clashes, ())
        self.assertIn("covered(path)", session.text(lod=1))

    def test_freezing_uses_ice_not_the_water_rule(self) -> None:
        session = run(Request(ask="why is the path risky?", facts=("rain", "freezing"), seed=1))
        ids = {claim.rule_id for claim in session.claims}
        self.assertIn("causal.slip_ice", ids)
        self.assertIn("causal.icy", ids)
        self.assertNotIn("causal.slip_water", ids)

    def test_sight_and_cover_can_both_stand(self) -> None:
        session = run(
            Request(ask="why is the path risky?", facts=("covered path", "dusk"), seed=1)
        )
        atoms = {claim.atom for claim in session.claims}
        self.assertIn("settled(no_traction_risk)", atoms)
        self.assertIn("risk(path)", atoms)
        self.assertEqual(session.clashes, ())

    def test_contested_givens_retract_dependents(self) -> None:
        session = run(
            Request(
                ask="why is the path risky?",
                facts=("wet ground", "dry ground", "above freezing"),
                seed=1,
            )
        )
        self.assertEqual(session.claims, ())
        self.assertIn("Contested claims blocked a settled answer.", session.open_gaps)
        self.assertIn("above_freezing", session.request.facts)
        self.assertNotIn("above_freezing", session.retracted)
        self.assertIn("slippery(path)", session.retracted)
        self.assertIn("risk(path)", session.retracted)
        text = session.text(lod=0)
        self.assertIn("dry(ground) contradicts wet(ground)", text)
        self.assertNotIn("slippery(path) because", text)

    def test_derived_contradiction_retracts_the_chain(self) -> None:
        rules = (
            Rule("t.wet", "domain", "ground", "Call it wet", "wet(ground)", ("rain",)),
            Rule("t.dry", "domain", "ground", "Call it dry", "dry(ground)", ("rain",)),
            Rule("t.slip", "domain", "path", "Call it slippery", "slippery(path)", ("wet(ground)",)),
            Rule("t.risk", "domain", "answer", "Call it a risk", "risk(path)", ("slippery(path)",)),
        )
        session = run(
            Request(ask="why is the path risky?", facts=("rain",), seed=1),
            packs=(),
            extra_rules=rules,
            extra_pairs=(("wet(ground)", "dry(ground)"),),
        )
        self.assertEqual(session.claims, ())
        self.assertIn("wet(ground)", session.retracted)
        self.assertIn("slippery(path)", session.retracted)
        self.assertIn("risk(path)", session.retracted)
        self.assertTrue(session.open_gaps)

    def test_clean_support_survives_a_tainted_one(self) -> None:
        rules = (
            Rule("t.wet", "domain", "ground", "Call it wet", "wet(ground)", ("rain",)),
            Rule("t.dry", "domain", "ground", "Call it dry", "dry(ground)", ("bug",)),
            Rule("t.icy", "domain", "ground", "Ice", "icy(ground)", ("freeze_ok",)),
            Rule("t.from_wet", "domain", "path", "From wet", "slippery(path)", ("wet(ground)",)),
            Rule("t.from_ice", "domain", "path", "From ice", "slippery(path)", ("icy(ground)",)),
        )
        session = run(
            Request(ask="check", facts=("rain", "bug", "freeze_ok"), seed=1, domain="quiet"),
            packs=(),
            extra_rules=rules,
            extra_pairs=(("wet(ground)", "dry(ground)"),),
        )
        ids = [claim.rule_id for claim in session.claims]
        self.assertIn("t.from_ice", ids)
        self.assertIn("t.icy", ids)
        self.assertNotIn("t.from_wet", ids)
        self.assertNotIn("t.wet", ids)
        self.assertNotIn("t.dry", ids)

    def test_explicit_domain_blocks_the_other_pack(self) -> None:
        session = run(
            Request(
                ask="why is the path risky?",
                facts=("rain", "above_freezing"),
                domain="arithmetic",
                seed=1,
            )
        )
        self.assertEqual(session.claims, ())
        self.assertIn("No answer rule fired from the given facts.", session.open_gaps)

    def test_unknown_ask_stays_open(self) -> None:
        session = run(Request(ask="tell me a story about a dragon", seed=1))
        self.assertEqual(session.claims, ())
        self.assertIn("No answer rule fired from the given facts.", session.open_gaps)

    def test_addition_is_exact_and_procedural(self) -> None:
        session = run(Request(ask="What is 17 plus 13?", seed=4))
        self.assertEqual(session.claims[0].atom, "value(30)")
        self.assertNotIn("30", session.text(lod=0))
        places = session.text(lod=2)
        self.assertIn("value(30) is the exact result", places)
        for line in add_lines(17, 13):
            self.assertIn(line, places)
        self.assertNotIn("wet(ground)", places)
        other = run(Request(ask="What is 17 plus 13?", seed=9))
        self.assertEqual(session.text(lod=2), other.text(lod=2).replace(f"seed {other.seed}", f"seed {session.seed}"))

    def test_subtraction_and_negatives(self) -> None:
        minus = run(Request(ask="15 - 7", seed=1))
        self.assertEqual(minus.claims[0].atom, "value(8)")
        self.assertIn("write 8", minus.text(lod=2))
        negative = run(Request(ask="what is -5 plus 3?", seed=1))
        self.assertEqual(negative.claims[0].atom, "value(-2)")
        self.assertIn("The result is the exact integer -2.", negative.text(lod=2))

    def test_leading_carry(self) -> None:
        session = run(Request(ask="999 + 1", seed=1))
        self.assertEqual(session.claims[0].atom, "value(1000)")
        self.assertIn("leading carry 1", session.text(lod=2))

    def test_asserted_wrong_sum_is_a_dead_end(self) -> None:
        session = run(Request(ask="what is 17 plus 13?", facts=("value(31)",), seed=1))
        self.assertEqual(session.claims, ())
        self.assertIn("value(30)", session.retracted)
        self.assertIn("value(31)", session.retracted)
        text = session.text(lod=2)
        self.assertIn("Retracted", text)
        self.assertIn("17 + 13 = 30", text)
        self.assertNotIn("value(30) is the exact result", text)
        self.assertIn("Contested claims blocked a settled answer.", session.open_gaps)

    def test_chained_addition_is_exact(self) -> None:
        session = run(Request(ask="17 + 13 + 1", seed=1))
        self.assertEqual(session.claims[0].atom, "value(31)")
        self.assertNotIn("31", session.text(lod=0))
        detail = session.text(lod=2)
        self.assertIn("Int.add: 17 + 13 = 30", detail)
        self.assertIn("Int.add: 30 + 1 = 31", detail)

    def test_local_store_rule_fires(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "local.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "id": "local.loose",
                            "title": "Loose gravel makes the path slippery",
                            "stage": "path",
                            "requires": ["loose(ground)"],
                            "produces": "slippery(path)",
                            "variants": ["Gravel rolls under the foot.", "The stones shift as weight lands."],
                        }
                    ]
                ),
                encoding="utf-8",
            )
            session = unfold(
                Request(ask="why is the path risky?", facts=("loose gravel",), seed=1),
                store_path=path,
            )
        ids = {claim.rule_id for claim in session.claims}
        self.assertIn("local.loose", ids)
        self.assertIn("causal.risk_traction", ids)
        detail = session.text(lod=2)
        self.assertTrue(("Gravel rolls" in detail) or ("stones shift" in detail))

    def test_malformed_store_raises(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "local.json"
            path.write_text(json.dumps([{"id": "broken"}]), encoding="utf-8")
            with self.assertRaises(ValueError):
                unfold(Request(ask="why is the path risky?", facts=("rain",)), store_path=path)

    def test_duplicate_rule_id_raises(self) -> None:
        rule = Rule("causal.wet_from_rain", "domain", "ground", "Again", "wet(ground)", ("rain",))
        with self.assertRaises(ValueError):
            run(warm_rain(), extra_rules=(rule,))

    def test_journal_appends_one_record(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "journal.jsonl"
            session = run(warm_rain(seed=3))
            append_journal(path, session)
            rows = path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(rows), 1)
        record = json.loads(rows[0])
        self.assertEqual(record["seed"], 3)
        self.assertEqual(record["rule_version"], RULE_VERSION)
        self.assertEqual([item["atom"] for item in record["claims"]], ["wet(ground)", "slippery(path)", "risk(path)"])

    def test_demo_prints(self) -> None:
        text = demo_text()
        self.assertIn("PGI", text)
        self.assertIn("value(30)", text)
        self.assertIn("contradicts", text)


if __name__ == "__main__":
    unittest.main()
