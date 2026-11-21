import json
import math
import unittest
from pathlib import Path

from helpers import ROOT, Workdir, close, dist, events, frames, read_jsonl, run_headless, snapshots, write_json


class GatherM2Phase2(unittest.TestCase):
    def setUp(self):
        contract = json.loads((Path(ROOT) / "game.contract.json").read_text(encoding="utf-8"))
        self.tuning = dict(contract["tuning"]["gather"])
        # Cấu hình v1.1 cho Phase 2
        self.tuning.update({
            "fish_speed": 1.5,
            "fish_turn_ticks": 120,
            "fish_max": 12,
            "fish_spawn_ticks": 360,
            "fish_spawn_clearance": 1.0,
            "fish_x": [4.0, 96.0],
            "fish_depths": {"ca_linh": [3.0, 12.0], "ca_loc": [8.0, 20.0], "ca_keo": [22.0, 28.0]},
            "fish_spawn_x": [15.0, 30.0, 45.0, 60.0, 75.0, 90.0],
            "fish_spawn_depths": {"ca_linh": [5.0, 10.0], "ca_loc": [10.0, 16.0], "ca_keo": [24.0, 27.0]},
            "fish_weights": {"ca_linh": 0.4, "ca_loc": 0.3, "ca_keo": 0.3},
            "fish_yield": {"ca_linh": 3, "ca_loc": 1, "ca_keo": 2},
        })

    def run_gather(self, workdir, ticks, scenario, *inputs, inventory_out=None):
        scenario_path = write_json(workdir.path("scenario.json"), {"gather": scenario})
        out = workdir.path("out.jsonl")
        args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--out", out,
                "--scenario", scenario_path, "--snapshot-every", "1"]
        if inputs:
            args.extend(["--inputs", write_json(workdir.path("inputs.json"), frames(*inputs))])
        if inventory_out:
            args.extend(["--inventory-out", inventory_out])
        code, stderr = run_headless(*args)
        self.assertEqual(code, 0, stderr)
        return read_jsonl(out)

    def test_ac_p2_m2_01_fish_swims_at_correct_speed(self):
        """AC-P2-M2-01: Cá bơi đúng tốc độ 1.5 m/s sau 60 tick (di chuyển được 1.5 m)."""
        from chonoi.rng import Streams
        from chonoi.ids import IdAllocator
        from chonoi.sim.gather import GatherSim
        from chonoi.inputs import InputState

        sim = GatherSim(
            {"gather": self.tuning, "quan": {"reputation_initial": 3.0}},
            {"player": {"pos": [2, 0]}, "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15.0, 5.0], "heading_deg": 0.0}]},
            Streams(1),
            IdAllocator()
        )
        inp = InputState((0.0, 0.0), set(), set())
        for _ in range(60):
            sim.step(inp)
        # Ban đầu tại [15.0, 5.0], hướng 0° (+x), sau 60 tick phải đến x = 16.5
        self.assertAlmostEqual(sim.fish[0]["pos"][0], 16.5, places=3)
        self.assertAlmostEqual(sim.fish[0]["pos"][1], 5.0, places=3)

    def test_ac_p2_m2_02_fish_turns_at_tick_120(self):
        """AC-P2-M2-02: Đổi hướng ở bước bơi thứ 120."""
        from chonoi.rng import Streams
        from chonoi.ids import IdAllocator
        from chonoi.sim.gather import GatherSim
        from chonoi.inputs import InputState

        sim = GatherSim(
            {"gather": self.tuning, "quan": {"reputation_initial": 3.0}},
            {"player": {"pos": [2, 0]}, "fish": [{"id": "F1", "kind": "ca_linh", "pos": [50.0, 8.0], "heading_deg": 0.0}]},
            Streams(42),
            IdAllocator()
        )
        inp = InputState((0.0, 0.0), set(), set())
        for _ in range(120):
            sim.step(inp)
        # Trong 120 tick đầu: heading giữ nguyên 0°
        self.assertEqual(sim.fish[0]["age_ticks"], 120)
        # Tick 121: trước khi di chuyển, cá rút heading mới từ seed
        sim.step(inp)
        self.assertNotEqual(sim.fish[0]["heading_deg"], 0.0)

    def test_ac_p2_m2_03_elastic_reflection_at_boundary(self):
        """AC-P2-M2-03: Phản xạ đàn hồi khi chạm biên x = 96."""
        from chonoi.rng import Streams
        from chonoi.ids import IdAllocator
        from chonoi.sim.gather import GatherSim
        from chonoi.inputs import InputState

        # Đặt cá ở 95.98 m, hướng 0° (+x). Vận tốc 1.5/60 = 0.025 m/tick.
        # Sau 1 tick: x_raw = 96.005 > 96.0 -> phản xạ về 96.0 - 0.005 = 95.995, heading đổi sang 180°
        sim = GatherSim(
            {"gather": self.tuning, "quan": {"reputation_initial": 3.0}},
            {"player": {"pos": [2, 0]}, "fish": [{"id": "F1", "kind": "ca_linh", "pos": [95.98, 5.0], "heading_deg": 0.0}]},
            Streams(1),
            IdAllocator()
        )
        inp = InputState((0.0, 0.0), set(), set())
        sim.step(inp)
        self.assertLessEqual(sim.fish[0]["pos"][0], 96.0)
        self.assertAlmostEqual(sim.fish[0]["pos"][0], 95.995, places=3)
        self.assertAlmostEqual(sim.fish[0]["heading_deg"], 180.0, places=3)

    def test_ac_p2_m2_04_fish_spawn_at_interval_360(self):
        """AC-P2-M2-04: Sinh cá theo chu kỳ 360 tick và phát event fish_spawned."""
        from chonoi.rng import Streams
        from chonoi.ids import IdAllocator
        from chonoi.sim.gather import GatherSim
        from chonoi.inputs import InputState

        sim = GatherSim(
            {"gather": self.tuning, "quan": {"reputation_initial": 3.0}},
            {"player": {"pos": [2, 0]}, "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15.0, 5.0], "heading_deg": 0.0}]},
            Streams(42),
            IdAllocator()
        )
        inp = InputState((0.0, 0.0), set(), set())
        all_events = []
        for _ in range(360):
            all_events.extend(sim.step(inp))
        spawn_events = [e for e in all_events if e[0] == "fish_spawned"]
        self.assertEqual(len(spawn_events), 1)
        self.assertEqual(spawn_events[0][0], "fish_spawned")
        self.assertIn("id", spawn_events[0][1])
        self.assertIn("kind", spawn_events[0][1])
        self.assertIn("pos", spawn_events[0][1])
        self.assertEqual(len(sim.fish), 2)

    def test_ac_p2_m2_05_spawn_capped_at_max(self):
        """AC-P2-M2-05: Không sinh cá khi đã chạm trần fish_max = 12."""
        from chonoi.rng import Streams
        from chonoi.ids import IdAllocator
        from chonoi.sim.gather import GatherSim
        from chonoi.inputs import InputState

        twelve_fish = [{"id": f"F{i}", "kind": "ca_linh", "pos": [float(i * 5 + 10), 5.0], "heading_deg": 0.0}
                       for i in range(12)]
        sim = GatherSim(
            {"gather": self.tuning, "quan": {"reputation_initial": 3.0}},
            {"player": {"pos": [2, 0]}, "fish": twelve_fish},
            Streams(1),
            IdAllocator()
        )
        inp = InputState((0.0, 0.0), set(), set())
        all_events = []
        for _ in range(360):
            all_events.extend(sim.step(inp))
        spawn_events = [e for e in all_events if e[0] == "fish_spawned"]
        self.assertEqual(len(spawn_events), 0)
        self.assertEqual(len(sim.fish), 12)

    def test_ac_p2_m2_06_spawn_clearance_greater_than_one_meter(self):
        """AC-P2-M2-06: Đàn cá mới sinh cách mọi đàn đang sống > 1.0 m."""
        from chonoi.rng import Streams
        from chonoi.ids import IdAllocator
        from chonoi.sim.gather import GatherSim
        from chonoi.inputs import InputState

        sim = GatherSim(
            {"gather": self.tuning, "quan": {"reputation_initial": 3.0}},
            {"player": {"pos": [2, 0]}, "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15.0, 5.0], "heading_deg": 0.0}]},
            Streams(99),
            IdAllocator()
        )
        inp = InputState((0.0, 0.0), set(), set())
        for _ in range(360):
            sim.step(inp)
        new_fish = sim.fish[-1]
        for f in sim.fish[:-1]:
            d = math.dist(new_fish["pos"], f["pos"])
            self.assertGreater(d, 1.0)

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_ac_p2_m2_07_gather_new_keo_neo_node(self):
        """AC-P2-M2-07: Hái bông kèo nèo tại nút N5 thu được keo_neo."""
        with Workdir() as workdir:
            rows = self.run_gather(
                workdir, 2,
                {
                    "player": {"pos": [76, 0]},
                    "nodes": [{"id": "N5", "kind": "keo_neo", "pos": [76, 0], "regrow_ticks": 0}],
                    "fish": [],
                    "hold": [],
                },
                {"tick": 0, "interact": True},
            )
        evs = events(rows, "gather")
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["data"], {"node_id": "N5", "kind": "keo_neo", "amount": 1})
        snaps = snapshots(rows)
        self.assertEqual(snaps[1]["hold"], ["keo_neo"])

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_ac_p2_m2_08_catch_new_ca_keo_species(self):
        """AC-P2-M2-08: Bắt cá kèo (ca_keo) thu được sản lượng yield = 2."""
        with Workdir() as workdir:
            rows = self.run_gather(
                workdir, 2,
                {
                    "player": {"pos": [15, 25]},
                    "nodes": [],
                    "fish": [{"id": "F1", "kind": "ca_keo", "pos": [15, 25], "heading_deg": 0}],
                    "hold": [],
                },
                {"tick": 0, "catch": True},
            )
        evs = events(rows, "fish_caught")
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["data"], {"fish_id": "F1", "kind": "ca_keo", "yield": 2})
        snaps = snapshots(rows)
        self.assertEqual(snaps[1]["hold"], ["ca_keo", "ca_keo"])

    def test_ac_p2_m2_09_random_fish_false_stays_stationary(self):
        """AC-P2-M2-09: Cờ random_fish: false giữ cá đứng yên và không sinh cá mới."""
        from chonoi.rng import Streams
        from chonoi.ids import IdAllocator
        from chonoi.sim.gather import GatherSim
        from chonoi.inputs import InputState

        sim = GatherSim(
            {"gather": self.tuning, "quan": {"reputation_initial": 3.0}},
            {"player": {"pos": [2, 0]}, "random_fish": False, "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15.0, 5.0], "heading_deg": 0.0}]},
            Streams(1),
            IdAllocator()
        )
        inp = InputState((0.0, 0.0), set(), set())
        for _ in range(400):
            sim.step(inp)
        # Cá đứng yên tại [15.0, 5.0]
        self.assertEqual(sim.fish[0]["pos"], [15.0, 5.0])
        # Không sinh thêm cá
        self.assertEqual(len(sim.fish), 1)

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_ac_p2_m2_10_inventory_with_new_ingredients(self):
        """AC-P2-M2-10: File kho chấp nhận 6 loại nguyên liệu, bao gồm ca_keo và keo_neo."""
        with Workdir() as workdir:
            inv_path = workdir.path("out_kho_p2.json")
            self.run_gather(
                workdir, 1,
                {
                    "player": {"pos": [2, 0]},
                    "hold": ["ca_keo", "keo_neo", "ca_loc", "ca_linh", "bong_sung", "bong_dien_dien"],
                    "nodes": [],
                    "fish": [],
                },
                {"tick": 0, "interact": True},  # dock
                inventory_out=inv_path,
            )
            data = json.loads(Path(inv_path).read_text(encoding="utf-8"))
        self.assertEqual(data, {
            "items": {
                "bong_dien_dien": 1,
                "bong_sung": 1,
                "ca_keo": 1,
                "ca_linh": 1,
                "ca_loc": 1,
                "keo_neo": 1,
            }
        })
