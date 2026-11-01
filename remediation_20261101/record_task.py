"""Record a final CPU audit/document task using the current interpreter."""
import sys
from common import AUDIT,run
r=run(sys.argv[1],[sys.executable,'-u',AUDIT/sys.argv[2],*sys.argv[3:]],required=False)
raise SystemExit(r['exit_code'] if r['exit_code'] is not None else 1)
