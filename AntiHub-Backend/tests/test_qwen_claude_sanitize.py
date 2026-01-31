import unittest

from app.services.anthropic_adapter import AnthropicAdapter


class TestQwenClaudeSanitize(unittest.TestCase):
    def test_sanitize_drops_images_and_keeps_text(self) -> None:
        openai_req = {
            "model": "claude-3-5-sonnet",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "hello"},
                        {"type": "image_url", "image_url": {"url": "https://example.com/a.png"}},
                        {"type": "text", "text": "world"},
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": "https://example.com/b.png"}},
                    ],
                },
                {"role": "assistant", "content": "ok"},
            ],
        }

        sanitized = AnthropicAdapter.sanitize_openai_request_for_qwen(openai_req)
        messages = sanitized.get("messages")
        self.assertIsInstance(messages, list)

        # second message becomes empty after dropping images -> removed
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], "hello\nworld")
        self.assertEqual(messages[1]["content"], "ok")


if __name__ == "__main__":
    unittest.main()

