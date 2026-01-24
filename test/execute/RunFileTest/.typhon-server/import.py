from pathlib import Path
import re
my_dir = Path(__file__).parent.parent
with open(my_dir / 'import.typh', 'r') as _typh_cn_m0_0_f:
    _typh_cn_m0_1_content = _typh_cn_m0_0_f.read()
    _typh_cn_m0_2_matches = re.findall('import (?P<name>\\w+)\\n', _typh_cn_m0_1_content)
    for _typh_cn_m0_3_m in _typh_cn_m0_2_matches:
        print(_typh_cn_m0_3_m)
'stdout\nPath\nre\n'