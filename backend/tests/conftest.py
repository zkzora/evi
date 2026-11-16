import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Isolate tests from the real database and from real provider keys.
os.environ["EVI_DATA_DIR"] = tempfile.mkdtemp(prefix="evi-test-")
os.environ["SERV_API_KEY"] = ""
os.environ["REPPO_API_KEY"] = ""
os.environ["EVI_EXECUTION_ENABLED"] = "true"   # tests use fake transports; gate tests flip this explicitly
os.environ.pop("EVI_ALLOW_PAID_RUNS", None)
# A generous TEST allowance so fake-transport tests can reach provider code; test_allowance.py sets its own windows/limits.
os.environ["EVI_ALLOWANCE_ID"] = "test-suite"
os.environ["EVI_ALLOWANCE_START"] = "2000-01-01T00:00:00Z"
os.environ["EVI_ALLOWANCE_END"] = ""
os.environ["EVI_ALLOWANCE_SERV_CALLS"] = "1000000"
os.environ["EVI_ALLOWANCE_REPPO_EVALS"] = "1000000"
