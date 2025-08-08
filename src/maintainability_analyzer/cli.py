import argparse
import json
from maintainability_analyzer import analyze

def main():
    parser = argparse.ArgumentParser(description="Analyze source code for maintainability metrics.")
    parser.add_argument("file", help="The path to the source code file to analyze.")
    parser.add_argument("-l", "--language", help="The programming language of the source code. If not provided, it will be guessed from the file extension.")

    args = parser.parse_args()

    language = args.language
    if not language:
        if args.file.endswith('.py'):
            language = 'python'
        elif args.file.endswith('.cpp') or args.file.endswith('.hpp'):
            language = 'cpp'
        elif args.file.endswith('.c') or args.file.endswith('.h'):
            language = 'c'
        elif args.file.endswith('.java'):
            language = 'java'
        else:
            print("Could not guess the language from the file extension. Please provide it with the -l/--language flag.")
            return

    with open(args.file, 'r') as f:
        source_code = f.read()

    results = analyze(source_code, language)

    print(json.dumps(results, indent=4))

if __name__ == "__main__":
    main()
