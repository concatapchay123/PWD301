from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath("src"))

from pwd301 import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
