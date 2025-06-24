import sys
from cx_Freeze import setup, Executable

base = None
if sys.platform == "win32":
    base = "Win32GUI"

executables = [Executable("main.py", icon="icon.png", target_name="chronoclicker", base=base)]
files = ["config.json", "gamedata.json", "README.md", ["resources/", "resources"]]

setup(name="Chronoclicker",
      version="2.3",
      description="Selenium-based CatWar autoclicker",
      executables=executables,
      options={
            "build_exe": {
                  "include_files": files
            }
      }
)
