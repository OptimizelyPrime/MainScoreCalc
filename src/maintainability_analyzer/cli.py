import argparse
import json
from maintainability_analyzer import analyze

def main():
    parser = argparse.ArgumentParser(description="Analyze source code for maintainability metrics.")
    parser.add_argument("file", help="The path to the source code file to analyze.")
    parser.add_argument("-l", "--language", help="The programming language of the source code. If not provided, it will be guessed from the file extension.")

    args = parser.parse_args()

    with open(args.file, 'r') as f:
        source_code = f.read()

    try:
        results = analyze(source_code, language=args.language, filepath=args.file)
    except ValueError as e:
        print(f"Error: {e}")
        return

    print(json.dumps(results, indent=4))

if __name__ == "__main__":
    main()
