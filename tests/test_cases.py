import subprocess, sys, os, io
from contextlib import redirect_stdout
from jsrunner.runtime import run_js

BASE = os.path.join(os.path.dirname(__file__), "samples")

def capture_output(js_path):
    with open(js_path, "r", encoding="utf-8") as f:
        src = f.read()
    f = io.StringIO()
    with redirect_stdout(f):
        intrp = run_js(src)
    return f.getvalue().strip(), intrp.captured

def test_tc1():
    out, _ = capture_output(os.path.join(BASE, "tc1_odd_even.js"))
    assert out.strip().splitlines()[-1] == "7 is Odd"

def test_tc2():
    out, _ = capture_output(os.path.join(BASE, "tc2_triangle.js"))
    lines = out.strip().splitlines()
    assert lines == ["*", "**", "***", "****", "*****"]

def test_tc3():
    out, _ = capture_output(os.path.join(BASE, "tc3_armstrong.js"))
    lines = [l.strip() for l in out.strip().splitlines()]
    assert lines == ["true", "false"]

def test_tc4():
    out, _ = capture_output(os.path.join(BASE, "tc4_array_reverse.js"))
    lines = [l.strip() for l in out.strip().splitlines()]
    assert lines == ["Original: 1, 2, 3, 4, 5", "Reversed: 5, 4, 3, 2, 1"]

def test_tc5():
    out, _ = capture_output(os.path.join(BASE, "tc5_palindrome.js"))
    assert out.strip().splitlines()[-1] == "racecar is a Palindrome"
