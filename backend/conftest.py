"""Test isolation: every pytest run gets a throwaway DB.

Sets BRIDGE_DB before any test module imports `app`/`db`, so the suite can
never pollute (or resurrect rows in) the user's real bridge.db. Uploads dir
stays real; tests clean up the files they create.
"""

import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="bridge-test-")
os.environ["BRIDGE_DB"] = os.path.join(_tmp, "test.db")
