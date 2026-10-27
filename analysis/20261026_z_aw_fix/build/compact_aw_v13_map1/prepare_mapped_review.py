"""Prepare a read-only map2/map1 topology review using the existing graph helper."""
from pathlib import Path
import ast
O=Path(__file__).resolve().parent
parent=O.parent/'compact_aw_v13/inspect_mapped_age.py'
target=O/'inspect_mapped_age.py';assert not target.exists()
text=parent.read_text()
changes={"for tag in ['v12','v13']:":"for tag in ['v13','v13_map1']:",
         "if tag=='v13':assert len(sources)==3":"assert len(sources)==3",
         "assert len(targets)==(4 if tag=='v13' else 2)":"assert len(targets)==4"}
for before,after in changes.items():
    assert text.count(before)==1;text=text.replace(before,after)
ast.parse(text);target.write_text(text,encoding='utf8')
print('Prepared read-only actual map2/map1 topology comparison.')
