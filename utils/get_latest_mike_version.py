from packaging.version import Version
import subprocess

out = subprocess.check_output(["mike", "list"], text=True)
versions = []

for line in out.splitlines():
    s = line.strip()
    if not s or s.startswith("alias:"):
        continue
    name = s.split()[0]
    if name == "latest":
        continue
    try:
        pv = Version(name)
        if pv.is_devrelease or not pv.is_prerelease:
            versions.append((pv, name))
    except Exception:
        pass

devs = [(pv, name) for pv, name in versions if pv.is_devrelease]
stables = [(pv, name) for pv, name in versions if not pv.is_prerelease and not pv.is_devrelease]

chosen = ""
if devs:
    chosen = max(devs)[1]
elif stables:
    chosen = max(stables)[1]

print(chosen)
