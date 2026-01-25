from sys import argv
from handler import serve_api

"""
TODO:
    1. Get request body data. DONE.
    2. Create ensure body keys decorator. DONE.
    3. Get request params in url (GET Method). DONE. And decoding.
    4. Handle exceptions to return hints of errors and properly status code..
    5. Create middleware decorator.
"""

if len(argv) < 3 or not argv[2].isnumeric():
    print("WRONG USAGE!")
    print("python3 <file> ip port")
    exit(1)

serve_api(argv[1], int(argv[2]))
