from cx_Freeze import setup, Executable

executables = [Executable("main.py")]

setup(name="Chronoclicker",
      version="1.3.3",
      description="Selenium-based CatWar autoclicker",
      executables=executables)
