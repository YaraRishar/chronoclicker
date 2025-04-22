from cx_Freeze import setup, Executable

executables = [Executable("main.py", icon="icon.png", target_name="chronoclicker")]
files = ["config.json", "gamedata.json", "icon.png", "README.md",
         "resources/readme_instruction.png", "resources/readme_instruction_raw.png"]

setup(name="Chronoclicker",
      version="2.1",
      description="Selenium-based CatWar autoclicker",
      executables=executables,
      options={
            "build_exe": {
                  "include_files": files
            }
      }
      )
