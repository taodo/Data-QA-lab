# Task 0 verification

Verified on Python 3.12.14, Linux:

- `python -m unittest discover -s tests/unit -v`: 10 tests passed.
- `python -m backend.app.main check`: 1 lab loaded.
- `python -m backend.app.main labs`: expected Lab 001 fields returned.
- Delivery ZIP extracted to a clean directory; CLI and tests rerun successfully.

Windows PowerShell instructions are provided but were not executed on a Windows machine. PostgreSQL/Docker/API/UI have not been implemented or tested at this checkpoint.

Run commands from the project root. An initial test attempt from the parent directory failed to import the backend package; running the documented command from the root resolved it.
