"""Run a task's `check:` commands (deterministic verification) and store the evidence."""
import subprocess
import time

import safety
import store


def run_check(cmd, cwd, timeout, tail_chars):
    start = time.time()
    try:
        proc = subprocess.Popen(cmd, shell=True, cwd=str(cwd), env=safety.scrubbed_env(),
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, errors="replace", start_new_session=True)
    except OSError as exc:
        return {"cmd": cmd, "exit": None, "ok": False, "timed_out": False,
                "seconds": 0, "output_tail": f"cannot start: {exc}"}
    timed_out = False
    try:
        out, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            import os, signal
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            proc.kill()
        out, _ = proc.communicate()
    code = None if timed_out else proc.returncode
    return {"cmd": cmd, "exit": code, "ok": code == 0, "timed_out": timed_out,
            "seconds": round(time.time() - start, 2),
            "output_tail": safety.tail(safety.redact(out or ""), tail_chars)}


def verify_task(ctx, task, cwd, repro_before=False):
    """repro_before=True: the repro must FAIL on current main (proves the bug exists)."""
    cfg = ctx.cfg
    d = ctx.runs(task.id)
    t, tail = cfg["check_timeout"], cfg["output_tail_chars"]
    meta = store.head_info(cwd)
    if repro_before:
        if not task.repro:
            raise SystemExit(f"{task.id} has no Repro check")
        res = run_check(task.repro, cwd, t, tail)
        reproduced = not res["ok"]
        path = store.write(d, "repro", {"reproduced": reproduced, "result": res, **meta})
        return {"ok": reproduced, "path": path, "results": [res], "label": "repro-before"}
    results = []
    if task.repro:
        r = run_check(task.repro, cwd, t, tail)
        r["criterion"] = "REPRO"
        results.append(r)
    for c in task.criteria:
        if not c["check"]:
            results.append({"criterion": c["id"], "cmd": None, "ok": False, "exit": None,
                            "timed_out": False, "seconds": 0,
                            "output_tail": "criterion has no check command"})
            continue
        r = run_check(c["check"], cwd, t, tail)
        r["criterion"] = c["id"]
        results.append(r)
    ok = bool(results) and all(r["ok"] for r in results)
    path = store.write(d, "verify", {"ok": ok, "results": results, **meta})
    return {"ok": ok, "path": path, "results": results, "label": "verify"}
