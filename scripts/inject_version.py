"""Helper script used in Actions to inject build version into version.py if needed locally"""
import datetime, pathlib, sys

def main():
    build_ver = datetime.datetime.utcnow().strftime("%Y.%m.%d.%H%M")
    path = pathlib.Path(__file__).resolve().parent.parent / "version.py"
    path.write_text(f"__version__ = \"{build_ver}\"\n")
    print("Injected version", build_ver)

if __name__ == "__main__":
    sys.exit(main())
