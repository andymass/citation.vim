# -*- coding: utf-8 -*-

"""
Tests your citation database in the console

Example *nix style commands:
python test.py /your/bibtext/file bibtex key
python test.py /your/zotero/path zotero key "searchstring" 4
"""

import sys
import os.path
module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
sys.path.insert(0, module_path)
from citation_vim.citation import Citation, Context, Builder

context = Context()

# Load command line args
context.bibtex_file = sys.argv[1]
context.zotero_path = sys.argv[1]
context.mode = sys.argv[2]
context.cache_path = ""
context.source_field = sys.argv[4] 
if context.mode == 'zotero':
    context.searchkeys = sys.argv[5].split()
    context.zotero_version = int(sys.argv[6])

context.collection = ''
context.source = 'citation'
context.key_format = "{author}{date}{Title}"
context.desc_format = u"{}∶ {} \"{}\" -{}- ({})"
context.desc_fields = ["type", "key", "title", "author", "date"]
context.et_al_limit = 5
context.wrap_chars = "[]"
context.cache = False
builder = Builder(context)
items = builder.build_source()
for field, desc, file, combined in items:
    print("\nField: ")
    print(field)
    print("\nDescription: ")
    print(desc)
    print("\nFile: ")
    print(file)
    print("\nCombined: ")
    print(combined)
