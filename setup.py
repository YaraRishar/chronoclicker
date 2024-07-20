from cx_Freeze import setup, Executable
import sys

base = "console" if sys.platform == "linux" else None

executables = [
    Executable("main.py", base=base, target_name="Chronoclicker")
]

setup(name="Chronoclicker",
      version="1.3.3",
      description="Selenium-based CatWar autoclicker",
      executables=executables)
