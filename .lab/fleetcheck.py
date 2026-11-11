#!/usr/bin/env python3
import os, re, subprocess, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)
passed = failed = 0
HOSTS = ["mf-u1", "mf-u2", "mf-d1", "mf-d2"]
UBUNTU, DEBIAN = HOSTS[:2], HOSTS[2:]


def check(desc, ok, hint=""):
    global passed, failed
    if ok:
        passed += 1; print("PASS  " + desc, flush=True)
    else:
        failed += 1; print("FAIL  " + desc + (("   -> " + hint) if hint else ""), flush=True)


def finish():
    print()
    print(("ALL CHECKS PASSED (%d/%d)" % (passed, passed)) if failed == 0 else ("%d check(s) failed, %d passed" % (failed, passed)))
    sys.exit(1 if failed else 0)


def sh(*a, timeout=900):
    r = subprocess.run(a, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout + r.stderr


def on(host, cmd):
    return sh("docker", "exec", host, "sh", "-c", cmd, timeout=60)


def recap(out):
    return {m[0]: {"ok": int(m[1]), "changed": int(m[2]), "unreachable": int(m[3]), "failed": int(m[4])}
            for m in re.findall(r"^(\S+)\s*:\s*ok=(\d+)\s+changed=(\d+)\s+unreachable=(\d+)\s+failed=(\d+)", out, re.M)}


print("== Your files ==")
try:
    import yaml
    plays = yaml.safe_load(open("site.yml")) or []
    gv = yaml.safe_load(open("group_vars/all.yml")) or {}
except Exception as e:
    check("site.yml and group_vars/all.yml are valid YAML", False, str(e)[:120]); finish()
check("site.yml has plays (and group_vars/all.yml is valid)", isinstance(plays, list) and len(plays) >= 3 and isinstance(gv, dict))


def tasks(items):
    for t in items or []:
        yield t
        for k in ("block", "rescue", "always"):
            if isinstance(t, dict) and k in t:
                yield from tasks(t[k])


alltasks = [t for p in plays if isinstance(p, dict) for s in ("pre_tasks", "tasks", "post_tasks", "handlers") for t in tasks(p.get(s)) if isinstance(t, dict)]
bad = [k for t in alltasks for k in t if k in ("shell", "ansible.builtin.shell", "raw", "ansible.builtin.raw", "script", "ansible.builtin.script")]
cmds = [t for t in alltasks if "command" in t or "ansible.builtin.command" in t]
check("no shell, raw or script; `command` only with changed_when: false", not bad and all(t.get("changed_when") is False for t in cmds))
check("group_by is used on the distribution fact", any(("group_by" in t or "ansible.builtin.group_by" in t) for t in alltasks))
check("a block with a rescue exists", any("rescue" in t for t in alltasks))
check("the tags packages, identity, report and os-specific are used", {"packages", "identity", "report", "os-specific"} <= {tg for t in alltasks for tg in ([t.get("tags")] if isinstance(t.get("tags"), str) else (t.get("tags") or []))} | {tg for p in plays if isinstance(p, dict) for tg in ([p.get("tags")] if isinstance(p.get("tags"), str) else (p.get("tags") or []))})
fu = gv.get("fleet_users") or []
check("fleet_users defines ana (sudo), bruno (no sudo) and chloe (sudo)", {u.get("name"): bool(u.get("sudo")) for u in fu if isinstance(u, dict)} == {"ana": True, "bruno": False, "chloe": True})

print("== Run it (twice) ==")
rc, out = sh("ansible-playbook", "site.yml")
r1 = recap(out)
check("the first run succeeds on all four servers", rc == 0 and set(r1) == set(HOSTS) and all(v["failed"] == 0 and v["unreachable"] == 0 for v in r1.values()), out[-600:])
if rc != 0:
    finish()
rc, out = sh("ansible-playbook", "site.yml")
r2 = recap(out)
check("the second run changes NOTHING (changed=0 everywhere)", rc == 0 and set(r2) == set(HOSTS) and all(v["changed"] == 0 for v in r2.values()), "changed: " + ", ".join("%s=%s" % (h, v["changed"]) for h, v in r2.items()))

print("== What the servers look like ==")
for h in HOSTS:
    rc, o = on(h, "dpkg -s htop jq curl >/dev/null 2>&1 && echo yes")
    ok1 = "yes" in o
    rc, o = on(h, "cat /etc/fleet-release")
    distro = "Ubuntu 24.04" if h in UBUNTU else "Debian 12.x"
    pat = r"Ubuntu 24\.04 - managed by Ansible" if h in UBUNTU else r"Debian 12(\.\d+)? - managed by Ansible"
    ok2 = re.fullmatch(pat, o.rstrip("\n")) is not None
    check("%s: htop, jq, curl installed and /etc/fleet-release says '%s - managed by Ansible'" % (h, distro), ok1 and ok2, o.strip()[:80])
for h in HOSTS:
    sudoers = on(h, "getent group sudo")[1]
    ok = all(on(h, "id -u " + u)[0] == 0 for u in ("ana", "bruno", "chloe")) and "ana" in sudoers and "chloe" in sudoers and "bruno" not in sudoers
    check("%s: users ana, bruno, chloe exist; ana and chloe are in sudo, bruno is not" % h, ok, sudoers.strip()[:80])
for h in UBUNTU:
    ok = on(h, "dpkg -s ufw >/dev/null 2>&1 && dpkg -s update-notifier-common >/dev/null 2>&1 && echo yes")[1].strip() == "yes"
    check("%s (Ubuntu): ufw and update-notifier-common are installed (and the rescue was not needed)" % h, ok and on(h, "test -f /var/log/ansible-fallback.log && echo yes")[1].strip() != "yes")
for h in DEBIAN:
    ok = on(h, "dpkg -s nftables >/dev/null 2>&1 && echo yes")[1].strip() == "yes" and on(h, "dpkg -s ufw >/dev/null 2>&1 && echo yes")[1].strip() != "yes"
    fb = on(h, "cat /var/log/ansible-fallback.log")[1]
    check("%s (Debian): nftables installed, no ufw, and the rescue recorded the fallback" % h, ok and fb.count("update-notifier-common is not available on %s" % h) == 1, fb.strip()[:100])

print("== Tags, limit and check mode ==")
rc, out = sh("ansible-playbook", "site.yml", "--limit", "mf-d*", "--tags", "packages")
r = recap(out)
check("--limit 'mf-d*' --tags packages runs on the two Debian servers only, changed=0", rc == 0 and set(r) == set(DEBIAN) and all(v["changed"] == 0 for v in r.values()), out[-300:])
rc, out = sh("ansible-playbook", "site.yml", "--check", "--diff")
r = recap(out)
check("--check --diff on the converged fleet predicts no change", rc == 0 and all(v["changed"] == 0 and v["failed"] == 0 for v in r.values()) and set(r) == set(HOSTS), out[-300:])
on("mf-u1", "rm -f /etc/fleet-release")
rc, out = sh("ansible-playbook", "site.yml", "--tags", "identity")
r = recap(out)
check("after someone deletes /etc/fleet-release on mf-u1, the playbook repairs exactly that server (changed=1 there, 0 elsewhere)", rc == 0 and r.get("mf-u1", {}).get("changed") == 1 and all(v["changed"] == 0 for h, v in r.items() if h != "mf-u1"), str({h: v["changed"] for h, v in r.items()}))
finish()
