import sys
from cx_Freeze import setup, Executable

base = None
if sys.platform == "win32":
    base = "gui"

executables = [Executable("main.py", icon="icon.ico", target_name="chronoclicker", base=base)]
files = ["config.json", "aliases.json", "gamedata.json", "README.md", ["resources/", "resources"]]

setup(name="Chronoclicker",
      version="3.0",
      description="Playwright-based CatWar autoclicker",
      executables=executables,
      options={
            "build_exe": {
                  "include_files": files
            }
      }
)
