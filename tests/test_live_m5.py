"""Unit & integration test cho M5 (chonoi.live HUD, /assets/ static serving, gather hái bụi/bắt cá & quan modes)."""

import json
import threading
import unittest
import urllib.error
import urllib.request

from chonoi.contract import load_contract
from chonoi.inventory import read_inventory
from chonoi.live import LiveGame, LiveServer


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, r.headers.get("Content-Type", ""), r.read()


def _post(url, obj):
    req = urllib.request.Request(
        url,
        data=json.dumps(obj).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read()
        e.close()
        return e.code, json.loads(body or b"{}")


class LiveM5Test(unittest.TestCase):
    def test_gather_hud_and_static_assets_serving(self):
        tuning = load_contract()["tuning"]
        game = LiveGame("gather", tuning, {}, seed=1)
        server = LiveServer(game, port=0)
        server.start()
        try:
            base = f"http://127.0.0.1:{server.port}"
            # 1. HTML HUD chứa đầy đủ cấu hình ASSET_MANIFEST và 2 chế độ drawGather / drawQuan
            code, ctype, html = _get(base + "/")
            self.assertEqual(code, 200)
            self.assertIn("text/html", ctype)
            self.assertIn(b"ASSET_MANIFEST", html)
            self.assertIn(b"drawGather", html)
            self.assertIn(b"drawQuan", html)

            # 2. Phục vụ ảnh nền gather_bg.png từ /assets/gather_bg.png
            code, ctype, img_bytes = _get(base + "/assets/gather_bg.png")
            self.assertEqual(code, 200)
            self.assertEqual(ctype, "image/png")
            self.assertTrue(img_bytes.startswith(b"\x89PNG"), "Phải là dữ liệu PNG hợp lệ")

            # 3. Chặn path traversal hoặc file không tồn tại
            for bad_path in ("/assets/khong_ton_tai.png", "/assets/../index.html"):
                with self.assertRaises(urllib.error.HTTPError) as ctx:
                    _get(base + bad_path)
                self.assertEqual(ctx.exception.code, 404)
                ctx.exception.close()

            # 4. Kiểm tra các trường snapshot buổi sáng (gather) cho HUD
            code, _, body = _get(base + "/state")
            self.assertEqual(code, 200)
            st = json.loads(body)
            self.assertEqual(st["mode"], "gather")
            for field in ("time_left_ticks", "player", "hold", "hold_capacity", "nodes", "fish", "meta", "events"):
                self.assertIn(field, st)
            for p_field in ("pos", "oxygen_ticks", "oxygen_max_ticks", "hp", "hp_max", "zero_oxy_ticks", "catch_cd_ticks", "at_surface"):
                self.assertIn(p_field, st["player"])
        finally:
            server.stop()

    def test_gather_live_harvest_node_and_catch_fish(self):
        """Kiểm chứng hái bụi ở mặt nước (E / interact) và bắt cá dưới nước (Space / catch) qua chonoi.live."""
        tuning = load_contract()["tuning"]
        scenario = {
            "player": {"pos": [12.0, 0.0]},
            "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12.0, 0.0], "regrow_ticks": 0}],
            "fish": [{"id": "F1", "kind": "ca_linh", "pos": [12.0, 2.0], "heading_deg": 0}],
        }
        game = LiveGame("gather", tuning, scenario, seed=1)
        server = LiveServer(game, port=0)
        server._thread = threading.Thread(target=server.httpd.serve_forever, daemon=True)
        server._thread.start()
        try:
            base = f"http://127.0.0.1:{server.port}"
            # 1. Ở mặt nước (d=0 <= 0.5), nhấn E (interact=True) tại N1 [12, 0] để hái bông điên điển
            code, _ = _post(base + "/input", {"move": [0, 0], "interact": True, "catch": False})
            self.assertEqual(code, 200)
            with game._lock:
                game._tick_once()
            _post(base + "/input", {"move": [0, 0], "interact": False, "catch": False})

            _, _, body1 = _get(base + "/state")
            st1 = json.loads(body1)
            self.assertEqual(st1["hold"], ["bong_dien_dien"])
            self.assertFalse(st1["nodes"][0]["ready"])
            self.assertGreater(st1["nodes"][0]["regrow_ticks"], 0)

            # 2. Lặn xuống độ sâu d > 0.5 gần đàn cá F1 [12, 2.0] rồi nhấn Space (catch=True)
            with game._lock:
                game.session.sim.pos = [12.0, 2.0]
            code, _ = _post(base + "/input", {"move": [0, 0], "interact": False, "catch": True})
            self.assertEqual(code, 200)
            with game._lock:
                game._tick_once()
            _post(base + "/input", {"move": [0, 0], "interact": False, "catch": False})

            _, _, body2 = _get(base + "/state")
            st2 = json.loads(body2)
            self.assertEqual(st2["hold"], ["bong_dien_dien", "ca_linh", "ca_linh", "ca_linh"])
            self.assertEqual(st2["fish"], [])
            self.assertEqual(st2["player"]["catch_cd_ticks"], 30)
        finally:
            server.httpd.shutdown()
            server.httpd.server_close()

    def test_quan_live_hud_state_and_inputs(self):
        tuning = load_contract()["tuning"]
        inv = read_inventory("docs/contracts/inventory.sample.json")
        scenario = {
            "player": {"pos": [2.0, 8.0]},
            "customers": [
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "ca_loc_nuong_trui",
                    "order_tick": 0,
                    "state": "waiting",
                    "patience_ticks_left": 3600,
                    "eat_ticks_left": 0,
                    "order_status": "reserved",
                    "reserved": {"ca_loc": 1},
                    "base_price": 60,
                    "tip": 0,
                }
            ],
        }
        game = LiveGame("quan", tuning, scenario, seed=1, inventory=inv)
        server = LiveServer(game, port=0)
        server._thread = threading.Thread(target=server.httpd.serve_forever, daemon=True)
        server._thread.start()
        try:
            base = f"http://127.0.0.1:{server.port}"
            code, _, body = _get(base + "/state")
            self.assertEqual(code, 200)
            st0 = json.loads(body)
            self.assertEqual(st0["mode"], "quan")
            self.assertIn("menu", st0["meta"])
            self.assertEqual(st0["stock"], {"bong_sung": 2, "ca_loc": 1})
            self.assertEqual(len(st0["customers"]), 1)
            self.assertEqual(st0["customers"][0]["order_status"], "reserved")

            # Gửi lệnh nhấn E (interact) tại bếp B1 để bắt đầu nấu
            code, resp = _post(base + "/input", {"move": [0, 0], "interact": True, "catch": False})
            self.assertEqual(code, 200)
            self.assertTrue(resp.get("ok"))
            with game._lock:
                game._tick_once()
            _post(base + "/input", {"move": [0, 0], "interact": False, "catch": False})

            _, _, body1 = _get(base + "/state")
            st1 = json.loads(body1)
            self.assertEqual(st1["stoves"][0]["state"], "cooking")
            self.assertEqual(st1["customers"][0]["order_status"], "assigned")
            self.assertEqual(st1["stock"], {"bong_sung": 2})

            # POST /restart khôi phục lại trạng thái ban đầu
            code, _ = _post(base + "/restart", {})
            self.assertEqual(code, 200)
            _, _, body_reset = _get(base + "/state")
            st_reset = json.loads(body_reset)
            self.assertEqual(st_reset["tick"], 0)
            self.assertEqual(st_reset["stoves"][0]["state"], "idle")
        finally:
            server.httpd.shutdown()
            server.httpd.server_close()


if __name__ == "__main__":
    unittest.main()
