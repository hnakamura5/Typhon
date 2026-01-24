def _typh_cc_m0_0():
    for x in range(0, 5):
        for y in range(0, 5):
            if x < y:

                def _typh_cc_f1_0():
                    try:
                        return y // x
                    except:
                        return 0

                def _typh_cc_f1_1():
                    try:
                        return y // x
                    except:
                        return None
                yield (_typh_cc_f1_0() if x < 3 else _typh_vr_f1_2_ if (_typh_vr_f1_2_ := _typh_cc_f1_1()) is not None else 0)
comp = _typh_cc_m0_0()
_typh_cn_m0_1_v: int
for _typh_cn_m0_1_v in comp:
    print(_typh_cn_m0_1_v)
'stdout\n0\n0\n0\n0\n2\n3\n4\n1\n2\n1\n'