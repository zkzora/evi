"""Spending allowance: window, cumulative limits, atomic reservation, unknown outcomes, restart persistence.
Fake transports only (each counts the requests that would have left the machine); no provider calls."""
import threading
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

from evi import allowance, api, db, providers
from evi.config import settings


def _set(monkeypatch, **kw):
    for k, v in kw.items():
        monkeypatch.setattr(settings.__class__, k, property(lambda s, v=v: v))


def _iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


NOW = datetime.now(timezone.utc)


def _allow(monkeypatch, aid, *, start=NOW - timedelta(hours=1), end=None, serv=3, reppo=1):
    monkeypatch.setenv("EVI_ALLOWANCE_ID", aid)
    monkeypatch.setenv("EVI_ALLOWANCE_START", _iso(start))
    monkeypatch.setenv("EVI_ALLOWANCE_END", _iso(end) if end else "")
    monkeypatch.setenv("EVI_ALLOWANCE_SERV_CALLS", str(serv))
    monkeypatch.setenv("EVI_ALLOWANCE_REPPO_EVALS", str(reppo))


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    _set(monkeypatch, execution_enabled=True, serv_api_key="test-key", reppo_api_key="test-key")
    c = db.connect(tmp_path / "evi.sqlite3")
    db.init(c)
    yield c
    c.close()


class Counter:
    """Fake provider: counts requests that reached it."""
    def __init__(self, behaviour="ok"):
        self.n, self.behaviour = 0, behaviour

    def transport(self):
        def h(request):
            self.n += 1
            if self.behaviour == "read_timeout":
                raise httpx.ReadTimeout("slow", request=request)
            if self.behaviour == "http500":
                return httpx.Response(500, json={"error": "upstream"})
            if "agents/evals" in str(request.url):
                return httpx.Response(200, json={"id": f"ev{self.n}", "status": "QUEUED"})
            return httpx.Response(200, json={"id": "c1", "choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}]})
        return httpx.MockTransport(h)


def _serv(c, counter, job_id=None):
    return providers.serv_chat(c, purpose="test", messages=[{"role": "user", "content": "x"}], schema_name="s",
                               schema={"type": "object"}, run_id=None, job_id=job_id, transport=counter.transport())


def _reppo(c, counter, job_id="j"):
    return providers.reppo_submit(c, input_text="packet", job_id=job_id, transport=counter.transport())


def test_no_allowance_fails_closed_before_any_request(conn, monkeypatch):
    monkeypatch.delenv("EVI_ALLOWANCE_ID")
    f = Counter()
    with pytest.raises(allowance.AllowanceRefused) as e:
        _serv(conn, f)
    assert e.value.code == "no_allowance" and f.n == 0
    assert conn.execute("SELECT COUNT(*) FROM provider_calls").fetchone()[0] == 0


def test_window_not_started_and_expired_refuse_paid_work(conn, monkeypatch):
    f = Counter()
    _allow(monkeypatch, "future", start=NOW + timedelta(days=1))
    with pytest.raises(allowance.AllowanceRefused) as e:
        _serv(conn, f)
    assert e.value.code == "allowance_not_started"
    _allow(monkeypatch, "past", start=NOW - timedelta(days=8), end=NOW - timedelta(seconds=1))
    with pytest.raises(allowance.AllowanceRefused) as e:
        _reppo(conn, f)
    assert e.value.code == "allowance_expired" and "ended at" in e.value.message and f.n == 0


def test_no_end_means_no_time_limit_only_cumulative(conn, monkeypatch):
    _allow(monkeypatch, "open-ended", start=NOW - timedelta(days=400), end=None, serv=2)
    f = Counter()
    _serv(conn, f)
    _serv(conn, f)
    with pytest.raises(allowance.AllowanceRefused) as e:
        _serv(conn, f)
    assert e.value.code == "allowance_exhausted" and f.n == 2


def test_retries_count_and_connect_errors_are_released(conn, monkeypatch):
    _allow(monkeypatch, "retries", serv=2)
    bad = Counter("http500")
    with pytest.raises(providers.ProviderError) as e:          # reached SERV: counts
        _serv(conn, bad, job_id="job-a")
    assert e.value.retryable and not e.value.outcome_unknown

    def refuse(request):
        raise httpx.ConnectError("down", request=request)
    with pytest.raises(providers.ProviderError):                # never left: released
        providers.serv_chat(conn, purpose="test", messages=[], schema_name="s", schema={}, run_id=None, job_id="job-a",
                            transport=httpx.MockTransport(refuse))
    assert allowance.status(conn)["serv"]["used"] == 1
    _serv(conn, Counter(), job_id="job-a")                       # the retry is a new request and reserves again
    assert allowance.status(conn)["serv"]["used"] == 2
    with pytest.raises(allowance.AllowanceRefused):
        _serv(conn, Counter(), job_id="job-a")


def test_read_timeout_is_unknown_counted_and_not_retryable(conn, monkeypatch):
    _allow(monkeypatch, "timeouts", serv=5)
    with pytest.raises(providers.ProviderError) as e:
        _serv(conn, Counter("read_timeout"), job_id="job-t")
    assert e.value.outcome_unknown and not e.value.retryable     # worker finishes the job as outcome_unknown
    assert allowance.status(conn)["serv"]["used"] == 1


def test_open_reservation_after_crash_blocks_automatic_repeat(conn, monkeypatch):
    _allow(monkeypatch, "crash", serv=5, reppo=5)
    allowance.reserve(conn, "serv", "extract", "job-crashed")    # worker died before settling
    f = Counter()
    with pytest.raises(providers.ProviderError) as e:
        _serv(conn, f, job_id="job-crashed")
    assert e.value.outcome_unknown and e.value.code == "submission_unknown" and f.n == 0
    assert allowance.status(conn)["serv"]["used"] == 1           # the unknown request still counts
    _serv(conn, f, job_id="another-job")                         # other work is unaffected
    assert f.n == 1


def test_concurrent_reservations_never_exceed_the_limit(tmp_path, monkeypatch):
    _set(monkeypatch, execution_enabled=True)
    _allow(monkeypatch, "race", serv=5)
    path = tmp_path / "race.sqlite3"
    c0 = db.connect(path)
    db.init(c0)
    ok, refused, barrier = [], [], threading.Barrier(24)

    def worker(i):
        c = db.connect(path)
        barrier.wait()
        try:
            allowance.reserve(c, "serv", "race", f"job-{i}")
            ok.append(i)
        except allowance.AllowanceRefused:
            refused.append(i)
        finally:
            c.close()
    ts = [threading.Thread(target=worker, args=(i,)) for i in range(24)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len(ok) == 5 and len(refused) == 19
    assert c0.execute("SELECT COUNT(*) FROM allowance_reservations WHERE allowance_id='race'").fetchone()[0] == 5


def test_usage_survives_restart(tmp_path, monkeypatch):
    _set(monkeypatch, execution_enabled=True, serv_api_key="k", reppo_api_key="k")
    _allow(monkeypatch, "restart", serv=2, reppo=1)
    path = tmp_path / "persist.sqlite3"
    c = db.connect(path)
    db.init(c)
    _serv(c, Counter())
    _reppo(c, Counter())
    c.close()                                                    # "restart": new connection, config re-read from env
    c2 = db.connect(path)
    db.init(c2)
    s = allowance.status(c2)
    assert (s["serv"]["used"], s["reppo"]["used"]) == (1, 1) and s["reppo"]["code"] == "allowance_exhausted"
    _serv(c2, Counter())
    with pytest.raises(allowance.AllowanceRefused):
        _serv(c2, Counter())
    c2.close()


def test_calls_made_before_the_ledger_are_backfilled_once(conn, monkeypatch):
    start = NOW - timedelta(hours=2)
    _allow(monkeypatch, "backfill", start=start, serv=3)
    for i, when in enumerate([start - timedelta(minutes=5), start + timedelta(minutes=10), start + timedelta(minutes=20)]):
        conn.execute("INSERT INTO provider_calls (call_id, provider, purpose, outcome, created_at) VALUES (?,?,?,?,?)",
                     (f"old{i}", "serv", "extract", "ok", when.isoformat(timespec="milliseconds")))
    assert allowance.status(conn)["serv"]["used"] == 2           # estimate before the backfill is written
    _serv(conn, Counter())                                       # writes the backfill (2) + this reservation (1)
    s = allowance.status(conn)
    assert s["serv"]["used"] == 3 and s["serv"]["code"] == "allowance_exhausted"
    assert conn.execute("SELECT backfilled_calls FROM allowance_backfills WHERE allowance_id='backfill'").fetchone()[0] == 2


def test_api_refuses_paid_work_but_keeps_stored_results_and_verification(monkeypatch):
    _set(monkeypatch, execution_enabled=True, serv_api_key="k", reppo_api_key="k", session_jobs_per_hour=99)
    _allow(monkeypatch, "api-expired", start=NOW - timedelta(days=9), end=NOW - timedelta(days=1))
    with TestClient(api.app) as client:
        c = db.connect()
        db.init(c)
        c.execute("DELETE FROM jobs")
        c.execute("DELETE FROM worker_heartbeats")
        c.execute("INSERT INTO worker_heartbeats VALUES ('w', ?)", (db.now(),))
        h = client.get("/api/v1/health").json()["capabilities"]
        assert h["extraction"]["code"] == "allowance_expired" and h["extraction"]["state"] == "unavailable"
        assert h["evaluation"]["code"] == "allowance_expired" and "ended at" in h["extraction"]["reason"]
        assert h["allowance"]["end"] == _iso(NOW - timedelta(days=1))
        n = c.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        r = client.post("/api/v1/documents/verizon-fy2024/parse", json={})
        assert r.status_code == 403 and r.json()["error"]["code"] == "allowance_expired"
        assert c.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == n
        assert client.get("/api/v1/documents").status_code == 200
        assert "source_verification" in h and h["stored_results"]["available"] in (True, False)
        _allow(monkeypatch, "api-used", serv=0, reppo=0)
        h = client.get("/api/v1/health").json()["capabilities"]
        assert h["extraction"]["state"] == "budget_exhausted" and h["extraction"]["code"] == "allowance_exhausted"
        r = client.post("/api/v1/documents/verizon-fy2024/parse", json={})
        assert r.status_code == 403 and r.json()["error"]["code"] == "allowance_exhausted"
