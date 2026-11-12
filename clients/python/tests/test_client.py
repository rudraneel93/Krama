"""Offline tests for pim_client against a small fake Krama API (no network, no engine)."""
import json
import statistics
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from pim_client import PIMClient, PIMError
from pim_client.cli import main as pim_check


class Fake(BaseHTTPRequestHandler):
    """Pretends the rule is a[n] = a[0] + step*n (step = median difference)."""
    busy_left = 0
    calls = 0

    def log_message(self, *a):
        pass

    def _send(self, code, body, headers=None):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.headers.get("X-API-Key") != "pim_good":
            return self._send(401, {"error": {"code": "unauthorized", "message": "invalid API key"}})
        self._send(200, {"plan": "free", "calls_used": Fake.calls})

    def do_POST(self):
        Fake.calls += 1
        if self.headers.get("X-API-Key") != "pim_good":
            return self._send(401, {"error": {"code": "unauthorized", "message": "invalid API key"}})
        if Fake.busy_left:
            Fake.busy_left -= 1
            return self._send(503, {"error": {"code": "server_busy", "message": "busy"}}, {"Retry-After": "0"})
        v = json.loads(self.rfile.read(int(self.headers["Content-Length"])))["values"]
        step = statistics.median(b - a for a, b in zip(v, v[1:], strict=False))
        breaks = [{"index": i, "kind": "value", "actual": x, "expected": v[0] + step * i}
                  for i, x in enumerate(v) if x != v[0] + step * i]
        self._send(200, {"status": "rule_with_breaks" if breaks else "follows_rule",
                         "rule": f"a[n] = a[n-1] + {step}", "explanation": f"Each element plus {step}.",
                         "breaks": breaks, "conforming_fraction": 1 - len(breaks) / len(v), "n": len(v),
                         "notes": [], "request_id": "test"})


@pytest.fixture(scope="module")
def url():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Fake)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


def test_check_parses_result(url):
    r = PIMClient("pim_good", url).check([10, 20, 30, 41, 50, 60])
    assert r.status == "rule_with_breaks" and not r.ok
    assert [(b.index, b.actual, b.expected) for b in r.breaks] == [(3, 41, 40)]


def test_numpy_like_and_float_ints_are_sent_as_ints(url):
    class Scalar:
        def __init__(self, v):
            self.v = v

        def item(self):
            return self.v
    r = PIMClient("pim_good", url).check([Scalar(1.0), 2.0, 3, 4.0, 5])
    assert r.ok


def test_bad_values_and_key(url):
    with pytest.raises(ValueError):
        PIMClient("pim_good", url).check([1, "2", 3])
    with pytest.raises(ValueError):
        PIMClient("pim_good", url).check([1, True, 3])
    with pytest.raises(PIMError) as e:
        PIMClient("pim_bad", url).check([1, 2, 3, 4])
    assert e.value.status == 401 and e.value.code == "unauthorized"


def test_retries_when_busy(url):
    Fake.busy_left = 2
    assert PIMClient("pim_good", url, retries=3).check([1, 2, 3, 4]).ok
    Fake.busy_left = 5
    with pytest.raises(PIMError) as e:
        PIMClient("pim_good", url, retries=1).check([1, 2, 3, 4])
    assert e.value.status == 503
    Fake.busy_left = 0


def test_check_long_reports_each_break_once(url):
    v = [3 * k for k in range(2500)]
    for i in (5, 995, 1000, 2400):  # 995 and 1000 fall inside a chunk overlap
        v[i] += 1
    chunks = PIMClient("pim_good", url).check_long(v)
    assert len(chunks) == 3
    assert sorted(b.index for _, r in chunks for b in r.breaks) == [5, 995, 1000, 2400]


def test_cli(url, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("PIM_API_KEY", "pim_good")
    f = tmp_path / "fees.csv"
    f.write_text("slab,fee\n" + "".join(f"{i},{500 + 125 * i if i != 7 else 999}\n" for i in range(20)))
    assert pim_check([str(f), "--column", "fee", "--order-by", "slab", "--api-url", url]) == 0
    assert "line 9: 999 but rule expects 1375" in capsys.readouterr().out
    assert pim_check([str(f), "--column", "fee", "--api-url", url, "--fail-on-breaks"]) == 1
    assert pim_check([str(f), "--column", "nope", "--api-url", url]) == 2
    capsys.readouterr()
    pim_check([str(f), "--column", "fee", "--api-url", url, "--json"])
    report = json.loads(capsys.readouterr().out)
    assert report[0]["breaks"][0]["line"] == 9
