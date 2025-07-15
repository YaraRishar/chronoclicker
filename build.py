import sys
import os
import subprocess


platform = sys.platform
command = [
    sys.executable, "-m", "nuitka",
    "--onefile",
    "--follow-imports",
    "--include-data-files=config.json=config.json",
    "--include-data-files=gamedata.json=gamedata.json",
    "--include-data-files=aliases.json=aliases.json",
    "--include-data-files=README.md=README.md",
    "--include-data-dir=resources=resources",
    "main.py"
]

if platform == "win32":
    command.extend([
        "--windows-icon-from-ico=icon.ico",
        "--windows-disable-console",
    ])

subprocess.run(command)
