import ast
from ..Grammar.typhon_ast import (
    get_let_pattern_body,
    get_pos_attributes,
    is_let_else,
    set_is_var,
    set_is_let_else,
    LetPatternInfo,
)
from .visitor import TyphonASTTransformer, flat_append
from contextlib import contextmanager
from dataclasses import dataclass
from .utils.jump_away import is_body_jump_away
from ..Grammar.syntax_errors import raise_let_missing_else_error


class IfMultipleLetTransformer(TyphonASTTransformer):
    """
        if (let <pattern1> = <subject1>, <pattern2> = <subject2>, ...,
                <patternN> = <subjectN>[;<cond>]) {
            <body>
        } else {
            <orelse>
        }

    --> (temporary represented now)

        if True: # multiple_let_pattern_body set to <body>
            match <subject1>:
                case <pattern1>:
                    match <subject2>:
                        case <pattern2>:
                            ...
                                match <subjectN>:
                                    case <patternN> if <cond>:
                                        <body>
                                    case _:
                                        pass
                            ...
                        case _:
                            pass
                case _:
                    pass
        else:
            <orelse>

    --> (transformation here)
        when <body> jumps away:
        match <subject1>:
            case <pattern1>:
                        ...
                            match <subjectN>:
                                case <patternN> if <cond>:
                                    <body>
                                case _:
                                    pass
                        ...
            case _:
                pass
        <orelse> # Unconditional execution of orelse

        when <body> does not jump away:
        <else_flag> = True
        match <subject1>:
            case <pattern1>:
                        ...
                            match <subjectN>:
                                case <patternN> if <cond>:
                                    <else_flag> = False
                                    <body>
                                case _:
                                    pass
                        ...
            case _:
                pass
        if <else_flag>: # Only when body did not execute
            <orelse>
    """

    def visit_IfLet(self, node: ast.If, info: LetPatternInfo) -> list[ast.stmt]:
        body = info.body
        pos = get_pos_attributes(node)
        # When jump away, does not need flag control.
        jump_away = is_body_jump_away(body)
        if jump_away:
            result: list[ast.stmt] = node.body  # Inside if True
            if node.orelse:
                result.extend(node.orelse)
            return result
        # Need flag control.
        # <else_flag> = True
        else_flag_name = self.new_temp_variable_name()
        else_flag_assign = ast.Assign(
            targets=[ast.Name(id=else_flag_name, ctx=ast.Store(), **pos)],
            value=ast.Constant(value=True),
            **pos,
        )
        set_is_var(else_flag_assign)
        # <else_flag> = False
        else_flag_set_false = ast.Assign(
            targets=[ast.Name(id=else_flag_name, ctx=ast.Store(), **pos)],
            value=ast.Constant(value=False),
            **pos,
        )
        body.insert(0, else_flag_set_false)
        result: list[ast.stmt] = [else_flag_assign]
        result.extend(node.body)
        if node.orelse:
            result.append(
                # if <else_flag>:
                ast.If(
                    test=ast.Name(id=else_flag_name, ctx=ast.Load(), **pos),
                    body=node.orelse,
                    orelse=[],
                    **pos,
                )
            )
        return result

    """
        let <pattern1> = <subject1>, <pattern2> = <subject2>, ...,
            <patternN> = <subjectN>
        else { # else clause is required unless all patterns are irrefutable
            <orelse> # If exists, must jump away.
        }
        <body>

    --> (temporary represented now)

        if True: # multiple_let_pattern_body set to <body>
            match <subject1>:
                case <pattern1>:
                    match <subject2>:
                        case <pattern2>:
                            ...
                                match <subjectN>:
                                    case <patternN>:
                                        <body>
                                    case _:
                                        pass
                                        (raise TypeError) # If else does not exist
                            ...
                        case _:
                            pass
                            (raise TypeError) # If else does not exist
                case _:
                    pass
                    (raise TypeError) # If else does not exist
        else: # If exists
            <orelse>

    --> (transformation here)

        The case when <body> does jumps away:

        match <subject1>:
            case <pattern1>:
                ...
                    match <subjectN>:
                        case <patternN>:
                            <body>
                        case _:
                            pass
                            (raise TypeError) # If else does not exist
                ...
            case _:
                pass
        <orelse> # Unconditional execution of orelse

        The case when <body> does not jump away:

        <else_flag> = True
        match <subject1>:
            case <pattern1>:
                ...
                    match <subjectN>:
                        case <patternN>:
                            <else_flag> = False
                            <body>
                        case _:
                            pass
                            (raise TypeError) # If else does not exist
                ...
            case _:
                pass
                (raise TypeError) # If else does not exist
        if <else_flag>: # Only when body did not execute
            <orelse> # If exists
    """

    def visit_LetElse(self, node: ast.If, info: LetPatternInfo) -> list[ast.stmt]:
        pos = get_pos_attributes(node)
        orelse = node.orelse
        if not orelse:
            if info.is_all_pattern_irrefutable:
                return node.body  # Simply return inside if True
            else:
                raise_let_missing_else_error(
                    "let pattern is irrefutable, possibly fails to match. else clause of let-else statement is required.",
                    **pos,
                )
        # With orelse, same as IfLet.
        return self.visit_IfLet(node, info)

    def visit_If(self, node: ast.If):
        self.generic_visit(node)  # Visit children first
        info = get_let_pattern_body(node)
        if info is None:  # Not a if-let nor let-else
            return node
        if is_let_else(node):
            return self.visit_LetElse(node, info)
        else:
            return self.visit_IfLet(node, info)


class WhileLetTransformer(TyphonASTTransformer):
    """
        while (let <pattern1> = <subject1>,
                   <pattern2> = <subject2>,
                   ...,
                   <patternN> = <subjectN>
                   [;<cond>]) {
            <body>
        } else {
            <orelse>
        }

    --> (temporary represented now)

        while True: # multiple_let_pattern_body set to <body>
            match <subject1>:
                case <pattern1>:
                    match <subject2>:
                        case <pattern2>:
                            ...
                                match <subjectN>:
                                    case <patternN> if <cond>:
                                        <body>
        else:
            <orelse>

    --> (transformation here)

        <continue_flag> = True
        while <continue_flag>:
            <continue_flag> = False
            match <subject1>:
                case <pattern1>:
                    match <subject2>:
                        case <pattern2>:
                            ...
                                match <subjectN>:
                                    case <patternN> if <cond>:
                                        <body>
                                        # Only when last of body does not jump away.
                                        <continue_flag> = True
        else:
            <orelse>
    """

    def visit_While(self, node: ast.While):
        self.generic_visit(node)
        info = get_let_pattern_body(node)
        if info is None:
            return node
        pos = get_pos_attributes(node)
        # <continue_flag> = True
        continue_flag_name = self.new_temp_variable_name()
        continue_flag_assign_true = ast.Assign(
            targets=[ast.Name(id=continue_flag_name, ctx=ast.Store(), **pos)],
            value=ast.Constant(value=True),
            **pos,
        )
        set_is_var(continue_flag_assign_true)
        if not is_body_jump_away(info.body):
            # <continue_flag> = True at end of body
            continue_flag_set_true = ast.Assign(
                targets=[ast.Name(id=continue_flag_name, ctx=ast.Store(), **pos)],
                value=ast.Constant(value=True),
                **pos,
            )
            info.body.append(continue_flag_set_true)
        # <continue_flag> = False at start of while body
        continue_flag_set_false = ast.Assign(
            targets=[ast.Name(id=continue_flag_name, ctx=ast.Store(), **pos)],
            value=ast.Constant(value=False),
            **pos,
        )
        result: list[ast.stmt] = [continue_flag_assign_true]
        result.append(
            ast.While(
                test=ast.Name(id=continue_flag_name, ctx=ast.Load(), **pos),
                body=[continue_flag_set_false] + node.body,
                orelse=node.orelse,
                **pos,
            )
        )
        return result


def if_while_let_transform(module: ast.Module):
    IfMultipleLetTransformer(module).run()
    WhileLetTransformer(module).run()
