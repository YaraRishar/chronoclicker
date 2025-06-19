from cx_Freeze import setup, Executable

executables = [Executable("main.py", icon="icon.png", target_name="chronoclicker")]
files = ["config.json", "gamedata.json", "README.md", ["resources/", "resources"]]

setup(name="Chronoclicker",
      version="2.2",
      description="Selenium-based CatWar autoclicker",
      executables=executables,
      options={
            "build_exe": {
                  "include_files": files
            }
      }
      )
