# Windows Deployment (master audit 3)

**Actual Windows execution: NOT TESTED.** This audit ran in a Linux cloud container. No Windows machine, `cmd.exe` or PowerShell was available, and the user's laptop was not attached. Nothing below claims a Windows run.

## What was verified, and how

| Check | Method | Result |
|---|---|---|
| `setup.bat` and `setup.ps1` find Python 3.12 (`py -3.12`, else `python` if it is 3.12), with a clear message otherwise | static review | as designed |
| `setup_environment.py`: refuses non-3.12; checks the project files; creates or **reuses** `.venv`; never deletes a `.venv` of another version; installs the pinned requirements; verifies imports; reports dataset availability | executed on Linux (fresh copy: 25 s; re-run reused `.venv` in 5 s) | PASS (Linux) |
| `run.bat` and `run.ps1`: change to the script folder, check `.venv`, call the launcher with arguments | static review; `test_windows_scripts_call_the_project_entry_points` | PASS (static) |
| `run_application.py`: preflight; port check; existing-instance reuse; **binds 127.0.0.1**; waits for `/_stcore/health`; prints the URL; opens the browser; Ctrl+C stops it | executed on Linux; `tests/integration/test_launcher.py` | PASS (Linux) |
| All `.bat` files use CRLF line endings (cmd.exe) | `test_windows_batch_files_use_crlf_line_endings` | PASS |
| Windows dependency resolution (wheels only, win_amd64, CPython 3.12) | `reports/verification/requirements-windows-resolved.txt` (earlier audit) | resolved; not installed on Windows |
| Paths: the app uses `pathlib` and project-relative paths; the browser tasks use `os.tmpdir()` | code review | no hard-coded POSIX paths in the app |

## Exact commands for the laptop

Run each command in a Command Prompt opened in `CRM\personal-financial-ai-analyzer`.

1. **Python:** install Python 3.12 64-bit from python.org and tick "Add python.exe to PATH". Check it:

   ```bat
   py -3.12 --version
   ```

2. **Setup:** expect `Environment ready.`

   ```bat
   setup.bat
   ```

3. **Tests:** expect 0 failed. Without the dataset, 4 data-dependent tests skip.

   ```bat
   test.bat
   ```

4. **Start:** opens http://localhost:8501.

   ```bat
   run.bat
   ```

5. **Laptop benchmark** (HW1 P5): writes `reports\laptop_benchmark.json`.

   ```bat
   benchmark.bat
   ```

**Stop and restart:** press Ctrl+C in the `run.bat` window, then run `run.bat` again. If the app is still running, `run.bat` reuses it. If another program uses port 8501, start on another port:

```bat
run.bat --port 8502
```

## Values to report after the laptop run

* Python version (from `setup.bat`);
* `test.bat` counts;
* whether `run.bat` printed `Dashboard ready: http://localhost:8501`;
* whether the 8 pages work with the demo data;
* `reports\laptop_benchmark.json`.

Until then, gates **O** (Windows setup) and **P** (Windows execution) stay **NOT TESTED**.
