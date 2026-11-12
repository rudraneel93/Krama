"""Krama API client: check that ordered columns follow a rule, and find the rows that break it.

Standard library only. Optional helpers for pandas and Great Expectations live in
``pim_client.pandas`` and ``pim_client.gx``.

    from pim_client import PIMClient
    pim = PIMClient(api_key="pim_...")            # or set PIM_API_KEY
    r = pim.check([1001, 1002, 1004, 1005, 1006, 1007, 1008, 1009, 1010, 1011])
    r.status    # "rule_with_breaks"
    r.breaks    # [Break(index=2, kind="jump", actual=1004, expected=1003)]
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from fractions import Fraction

__version__ = "0.1.0"
DEFAULT_URL = "https://getkrama.vercel.app/api"  # the hosted Krama API; override with PIM_API_URL
MAX_VALUES = 1000


class PIMError(Exception):
    def __init__(self, status: int, code: str, message: str, request_id: str | None = None):
        super().__init__(f"{status} {code}: {message}")
        self.status, self.code, self.message, self.request_id = status, code, message, request_id


@dataclass
class Break:
    index: int
    kind: str
    actual: float | int
    expected: float | int | Fraction


@dataclass
class CheckResult:
    status: str
    rule: str | None
    explanation: str | None
    breaks: list[Break]
    conforming_fraction: float | None
    n: int
    notes: list[str] = field(default_factory=list)
    request_id: str | None = None
    raw: dict = field(default_factory=dict, repr=False)

    @property
    def ok(self) -> bool:
        """True when the column follows a rule with no breaks."""
        return self.status == "follows_rule"


def _num(v):
    if isinstance(v, str) and "/" in v:
        return Fraction(v)
    return v


def _clean_values(values) -> list:
    out = []
    for i, v in enumerate(values):
        if hasattr(v, "item"):  # numpy / pandas scalars
            v = v.item()
        if isinstance(v, bool) or not isinstance(v, int | float):
            raise ValueError(f"value at position {i} is not a number: {v!r}")
        if isinstance(v, float) and v.is_integer() and abs(v) < 2 ** 53:
            v = int(v)
        out.append(v)
    return out


class PIMClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout: float = 30.0,
                 retries: int = 3):
        self.api_key = api_key or os.environ.get("PIM_API_KEY")
        if not self.api_key:
            raise ValueError("no API key: pass api_key= or set PIM_API_KEY")
        self.base_url = (base_url or os.environ.get("PIM_API_URL") or DEFAULT_URL).rstrip("/")
        self.timeout, self.retries = timeout, retries

    def _post(self, path: str, payload: dict) -> dict:
        return self._request("POST", path, payload)

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        data = None if payload is None else json.dumps(payload).encode()
        for attempt in range(self.retries + 1):
            req = urllib.request.Request(self.base_url + path, data=data, method=method, headers={
                "X-API-Key": self.api_key, "Content-Type": "application/json",
                "User-Agent": f"pim-client-python/{__version__}"})
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read())
            except urllib.error.HTTPError as e:
                try:
                    body = json.loads(e.read())
                except ValueError:
                    body = {}
                err = body.get("error", {})
                retryable = e.code == 503 or (e.code == 429 and err.get("code") == "rate_limited")
                if retryable and attempt < self.retries:
                    time.sleep(float(e.headers.get("Retry-After", 1)) * (attempt + 1))
                    continue
                raise PIMError(e.code, err.get("code", "error"), err.get("message", str(e)),
                               body.get("request_id")) from None
        raise AssertionError("unreachable")

    def check(self, values, max_break_fraction: float = 0.2) -> CheckResult:
        """Does this ordered column follow a rule? Which rows break it?"""
        vals = _clean_values(values)
        if len(vals) > MAX_VALUES:
            raise ValueError(f"at most {MAX_VALUES} values per call; use check_long() for longer columns")
        b = self._post("/v1/check", {"values": vals, "max_break_fraction": max_break_fraction})
        return CheckResult(status=b["status"], rule=b["rule"], explanation=b.get("explanation"),
                           breaks=[Break(x["index"], x["kind"], x["actual"], _num(x["expected"]))
                                   for x in b["breaks"]],
                           conforming_fraction=b.get("conforming_fraction"), n=b["n"],
                           notes=b.get("notes", []), request_id=b.get("request_id"), raw=b)

    def check_long(self, values, max_break_fraction: float = 0.2, chunk: int = MAX_VALUES,
                   overlap: int = 12) -> list[tuple[int, CheckResult]]:
        """Check a column longer than one call allows, in overlapping chunks.
        Returns (offset, result) per chunk; break indices are global."""
        vals = _clean_values(values)
        if not 0 <= overlap < chunk // 2:
            raise ValueError("overlap must be smaller than half the chunk")
        out, start, covered = [], 0, 0
        while start < len(vals):
            end = min(len(vals), start + chunk)
            r = self.check(vals[start:end], max_break_fraction)
            for b in r.breaks:
                b.index += start
            r.breaks = [b for b in r.breaks if b.index >= covered]  # overlap already reported
            covered = end
            out.append((start, r))
            if end == len(vals):
                break
            start = end - overlap
        return out

    def discover(self, values, steps: int = 8, **kw) -> dict:
        return self._post("/v1/discover", {"values": _clean_values(values), "steps": steps, **kw})

    def usage(self) -> dict:
        return self._request("GET", "/v1/usage")
