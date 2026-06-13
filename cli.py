import sys
from jsrunner.runtime import run_js

def main():
    if len(sys.argv) < 2:
        print("Usage: python cli.py <file.js>")
        sys.exit(1)
    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    run_js(src)

if __name__ == "__main__":
    main()
