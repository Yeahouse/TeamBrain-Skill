"""Read-only presence checks for explicitly named MCP variables; never read values."""
import argparse
import json
import os
import re
import subprocess


def inspect(names):
    if not names or any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", n) for n in names):
        return {"status": "invalid_variable_names"}
    persistent_names = None
    if os.name == "nt":
        # GetValueNames retrieves registry names only, never registry values.
        command = "$k=[Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Environment'); try { if ($null -eq $k) { '[]' } else { ConvertTo-Json -Compress -InputObject @($k.GetValueNames()) } } finally { if ($null -ne $k) { $k.Dispose() } }"
        try:
            result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10)
            if result.returncode == 0:
                parsed = json.loads(result.stdout.decode("utf-8-sig"))
                if isinstance(parsed, list) and all(isinstance(n, str) for n in parsed):
                    persistent_names = {n.casefold() for n in parsed}
        except (OSError, ValueError, subprocess.TimeoutExpired):
            pass
    return {"status": "ok", "scope": "current_child_process_and_windows_user_names_only",
            "values_read": False, "validity": "not_checked",
            "user_registry_scope": "execution_identity_not_necessarily_desktop_user",
            "variables": [{"name": n, "process_name_present": n in os.environ,
                           "user_persistent_name_present": None if persistent_names is None else n.casefold() in persistent_names}
                          for n in dict.fromkeys(names)]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("names", nargs="+")
    print(json.dumps(inspect(parser.parse_args().names), ensure_ascii=True, indent=2))
