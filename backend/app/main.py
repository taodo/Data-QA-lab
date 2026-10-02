"""Foundation CLI; real API and pipeline execution arrive in later tasks."""
import argparse
import json
from dataclasses import asdict
from backend.app.services.lab_catalog import load_labs

def main():
    parser = argparse.ArgumentParser(description="Data QA Lab foundation")
    parser.add_argument("command", choices=["labs", "check"])
    args = parser.parse_args()
    labs = load_labs()
    if args.command == "labs":
        print(json.dumps([asdict(lab) for lab in labs], indent=2, ensure_ascii=False))
    else:
        if not labs:
            raise SystemExit("No lab definitions found")
        print(f"Foundation OK: {len(labs)} lab definition(s). Pipeline not implemented yet.")

if __name__ == "__main__":
    main()
