import ast

from Typhon.Grammar.typhon_ast import (
    get_empty_pos_attributes,
    get_generated_name_original_map,
    make_record_type,
)
from Typhon.LanguageServer._utils.demangle import replace_mangled_names
from Typhon.Transform.record_to_dataclass import record_to_dataclass


def test_replace_mangled_record_type_with_type_args() -> None:
    mapping = {
        "_typh_cl_m0_1_": "{| x: _typh_record_type_arg_0_, y: _typh_record_type_arg_1_ |}"
    }

    text = 'Type "_typh_cl_m0_1_[int, str]" is not assignable.'

    assert (
        replace_mangled_names(text, mapping)
        == 'Type "{| x: int, y: str |}" is not assignable.'
    )


def test_replace_mangled_record_type_with_nested_type_args() -> None:
    mapping = {
        "_typh_cl_m0_2_": "{| x: _typh_record_type_arg_0_, y: _typh_record_type_arg_1_ |}"
    }

    text = "_typh_cl_m0_2_[list[T | None], tuple[str, int] | None]"

    assert replace_mangled_names(text, mapping) == "{| x: [T?], y: (str, int)? |}"


def test_record_type_transform_stores_demangle_template() -> None:
    pos = get_empty_pos_attributes()
    record_type = make_record_type(
        fields=[
            (
                ast.Name(id="x", ctx=ast.Load(), **pos),
                ast.Name(id="int", ctx=ast.Load(), **pos),
            ),
            (
                ast.Name(id="y", ctx=ast.Load(), **pos),
                ast.Name(id="str", ctx=ast.Load(), **pos),
            ),
        ],
        **pos,
    )

    module = ast.Module(body=[ast.Expr(value=record_type, **pos)], type_ignores=[])

    record_to_dataclass(module)
    mapping = get_generated_name_original_map(module)

    templates = [
        value
        for key, value in mapping.items()
        if key.startswith("_typh_cl_") and "_typh_record_type_arg_" in value
    ]

    assert templates
    assert (
        templates[0] == "{| x: _typh_record_type_arg_0_, y: _typh_record_type_arg_1_ |}"
    )
