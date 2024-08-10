#!/usr/bin/env python3

from testerng import Tester, Capability
from pathlib import Path
import os
import testerng
import testerng.plugins
import testerng.reporters


tests_dir = Path(__file__).parent
os.chdir(str(tests_dir))

t = Tester(str(tests_dir), tests_dir.parent, str(tests_dir.joinpath("results")))
t.add_plugin(testerng.reporters.DefaultTerminalReporter)

# ignore confidential path hiding ... it's just annoying here
t._confidential_paths.clear()

t.add_student_capabilities(Capability.NET_ADMIN, Capability.NET_RAW)
t.run(verbose=False)
