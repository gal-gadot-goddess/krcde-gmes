"""A YouTube auth failure must never kill Instagram/Facebook publishing."""
import unittest
from unittest.mock import MagicMock

import config
import engine
import publish_youtube


def _refresh_error(msg):
    try:
        from google.auth.exceptions import RefreshError
        return RefreshError(msg)
    except Exception:
        return RuntimeError(msg)


class PublishResilienceTest(unittest.TestCase):
    def test_youtube_invalid_scope_returns_none(self):
        config.YT_CLIENT_ID = "id"
        config.YT_CLIENT_SECRET = "sec"
        config.YT_REFRESH_TOKEN = "tok"
        import google.oauth2.credentials as cred_mod
        import googleapiclient.discovery as disc_mod
        import googleapiclient.http as http_mod

        cred_mod.Credentials = MagicMock()
        req = MagicMock()
        req.execute.side_effect = _refresh_error(
            "('invalid_scope: Bad Request', {'error': 'invalid_scope'})")
        yt = MagicMock()
        yt.videos.return_value.insert.return_value = req
        disc_mod.build = MagicMock(return_value=yt)
        http_mod.MediaFileUpload = MagicMock()

        try:
            got = publish_youtube.publish(
                "dummy.mp4",
                {"title": "t", "description": "d", "hashtags": "#h", "tags": ["t"]},
            )
        finally:
            import importlib
            importlib.reload(cred_mod)
            importlib.reload(disc_mod)
            importlib.reload(http_mod)
        self.assertIsNone(got)

    def test_safe_publish_isolates_channel_failure(self):
        def boom(*args):
            raise RuntimeError("nope")

        self.assertIsNone(engine._safe_publish("youtube", boom))
        self.assertEqual(engine._safe_publish("youtube", lambda: "vid123"), "vid123")


if __name__ == "__main__":
    unittest.main()
