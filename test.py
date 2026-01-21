from sys import argv
from handler import serve_api


if len(argv) < 3 or not argv[2].isnumeric():
    print("WRONG USAGE!")
    print("python3 <file> ip port")
    exit(1)

serve_api(argv[1], int(argv[2]))
