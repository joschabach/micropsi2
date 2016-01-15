:: ugh, I have no idea what I'm doing.
@ECHO OFF
pip install virtualenv

IF NOT EXIST env\Scripts\activate.bat (
    :: virtualenv not created, creating
    ECHO creating virtualenv environment
    virtualenv env
    IF %ERRORLEVEL% NEQ 0 (
        ECHO could not create virtualenv environment
        EXIT /b 1
    )
)

:: we have what we need.
ECHO found pip, found virtualenv. installing dependencies.

env\Scripts\pip install -r requirements.txt

IF %ERRORLEVEL% NEQ 0 (
    ECHO error installing requirements
    EXIT /b 1
)

ECHO all done!
