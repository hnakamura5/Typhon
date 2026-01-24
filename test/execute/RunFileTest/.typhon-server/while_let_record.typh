from typing import runtime_checkable as _typh_bi_runtime_checkable
from typing import Protocol as _typh_bi_Protocol
from typing import Final as _typh_bi_Final
from dataclasses import dataclass as _typh_bi_dataclass

@_typh_bi_runtime_checkable
class _typh_cl_m0_5_[_typh_tv_m0_3_x, _typh_tv_m0_4_y](_typh_bi_Protocol):
    x: _typh_bi_Final[_typh_tv_m0_3_x]
    y: _typh_bi_Final[_typh_tv_m0_4_y]

@_typh_bi_dataclass(frozen=True, repr=False, unsafe_hash=True, kw_only=True)
class _typh_cl_m0_2_[_typh_tv_m0_0_x, _typh_tv_m0_1_y]:
    x: _typh_bi_Final[_typh_tv_m0_0_x]
    y: _typh_bi_Final[_typh_tv_m0_1_y]

    def __repr__(self):
        return f'{{|x={self.x!r}, y={self.y!r}|}}'
seq = (_typh_cl_m0_2_(x=_typh_cn_m0_7_i, y=_typh_cn_m0_8_j) for _typh_cn_m0_7_i in range(0, 3) for _typh_cn_m0_8_j in range(0, 3))
_typh_vr_m0_6_ = True
while _typh_vr_m0_6_:
    _typh_vr_m0_6_ = False
    match next(seq):
        case _typh_cl_m0_5_(x=0, y=_typh_cn_m0_9_y):
            print(f'x: 0, y: {_typh_cn_m0_9_y}')
            _typh_vr_m0_6_ = True
        case _:
            pass
'stdout\nx: 0, y: 0\nx: 0, y: 1\nx: 0, y: 2\n'