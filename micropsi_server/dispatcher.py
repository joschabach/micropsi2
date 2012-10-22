import os
import usermanagement
from micropsi_core import runtime

RESOURCE_PATH = os.path.join(os.path.dirname(__file__), "..", "resources")

micropsi = runtime.MicroPsiRuntime(RESOURCE_PATH)
usermanager = usermanagement.UserManager(os.path.join(RESOURCE_PATH, "user-db.json"))
