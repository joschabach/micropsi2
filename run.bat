@ECHO OFF
IF NOT EXIST env\Scripts\activate.bat (
    python start_micropsi_server.py
) ELSE (
    env\Scripts\activate.bat
    env\Scripts\python start_micropsi_server.py
)