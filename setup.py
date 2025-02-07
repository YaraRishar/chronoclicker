from cx_Freeze import setup, Executable

executables = [Executable("main.py")]

setup(name="Chronoclicker",
      version="1.4",
      description="Selenium-based CatWar autoclicker",
      executables=executables)
