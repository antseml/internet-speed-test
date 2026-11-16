import contextlib
import http.server
import threading
import unittest

import speed_test


PAYLOAD = b"test payload" * 1024


class TestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Length", str(len(PAYLOAD)))
        self.end_headers()
        self.wfile.write(PAYLOAD)

    def log_message(self, format, *args):
        pass


class SpeedTestTests(unittest.TestCase):
    def test_downloads_full_response_requested_number_of_times(self):
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), TestHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}/file"

        try:
            with contextlib.redirect_stdout(None):
                measurements = speed_test.run_measurements(url, count=3, timeout=2)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

        self.assertEqual(len(measurements), 3)
        self.assertTrue(all(item.bytes_downloaded == len(PAYLOAD) for item in measurements))
        self.assertTrue(all(item.duration_seconds > 0 for item in measurements))

    def test_rejects_non_positive_count(self):
        self.assertEqual(speed_test.main(["https://example.com", "--count", "0"]), 2)


if __name__ == "__main__":
    unittest.main()
