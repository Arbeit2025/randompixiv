import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app as app_module  # noqa: E402

SAMPLE = {
    "pid": 12345678,
    "title": "テスト作品",
    "author": "テスト作者",
    "tags": ["風景", "空"],
    "r18": False,
    "image": "https://example.com/img.jpg",
    "url": "https://www.pixiv.net/artworks/12345678",
}


class RandomPixivTest(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()
        self._orig_fetch = app_module.fetch_random_work

    def tearDown(self):
        app_module.fetch_random_work = self._orig_fetch

    def test_healthz(self):
        res = self.client.get("/healthz")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["status"], "ok")

    def test_index_ok(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        body = res.get_data(as_text=True)
        self.assertIn("ランダムpixiv", body)
        self.assertIn("ランダムで作品を表示", body)

    def test_random_success(self):
        app_module.fetch_random_work = lambda: dict(SAMPLE)
        res = self.client.get("/random")
        self.assertEqual(res.status_code, 200)
        body = res.get_data(as_text=True)
        self.assertIn("テスト作品", body)
        self.assertIn("テスト作者", body)
        self.assertIn("https://example.com/img.jpg", body)
        self.assertIn("https://www.pixiv.net/artworks/12345678", body)
        self.assertIn("風景 / 空", body)

    def test_random_failure_shows_error(self):
        def boom():
            raise RuntimeError("network down")

        app_module.fetch_random_work = boom
        res = self.client.get("/random")
        self.assertEqual(res.status_code, 200)
        body = res.get_data(as_text=True)
        self.assertIn("作品を取得できませんでした", body)


class SafeFilterTest(unittest.TestCase):
    def test_is_safe(self):
        self.assertTrue(app_module._is_safe({"r18": False, "tags": ["風景"]}))
        self.assertFalse(app_module._is_safe({"r18": True, "tags": []}))
        self.assertFalse(app_module._is_safe({"r18": False, "tags": ["R-18"]}))

    def test_fetch_random_work_redraws_unsafe(self):
        draws = [
            {"pid": 1, "title": "a", "author": "", "tags": ["R-18"],
             "r18": False, "image": "", "url": ""},
            {"pid": 2, "title": "b", "author": "", "tags": [],
             "r18": False, "image": "", "url": ""},
        ]
        orig = app_module._fetch_one
        try:
            app_module._fetch_one = lambda: draws.pop(0)
            work = app_module.fetch_random_work()
        finally:
            app_module._fetch_one = orig
        self.assertEqual(work["pid"], 2)

    def test_fetch_random_work_gives_up(self):
        orig = app_module._fetch_one
        try:
            app_module._fetch_one = lambda: {
                "pid": 1, "title": "a", "author": "", "tags": [],
                "r18": True, "image": "", "url": "",
            }
            with self.assertRaises(ValueError):
                app_module.fetch_random_work()
        finally:
            app_module._fetch_one = orig


if __name__ == "__main__":
    unittest.main()
