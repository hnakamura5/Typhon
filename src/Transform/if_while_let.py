import ast
from ..Grammar.typhon_ast import get_let_pattern_body, get_pos_attributes, set_is_var
from .visitor import TyphonASTTransformer, flat_append
from contextlib import contextmanager


def _is_body_jumping(body: list[ast.stmt]) -> bool:
    if not body:
        return False
    last_stmt = body[-1]
    return isinstance(last_stmt, (ast.Break, ast.Continue, ast.Return, ast.Raise))


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
        else:
            <orelse>

    --> (transformation here)

        <else_flag> = True
        match <subject1>:
            case <pattern1>:
                match <subject2>:
                    case <pattern2>:
                        ...
                            match <subjectN>:
                                case <patternN> if <cond>:
                                    <body>
                                    # Only when last of body does not jump away.
                                    <else_flag> = False
        if <else_flag>:
            <orelse>
    """

    def visit_If(self, node: ast.If):
        self.generic_visit(node)
        body = get_let_pattern_body(node)
        if body is None:
            return node
        pos = get_pos_attributes(node)
        # <else_flag> = True
        else_flag_name = self.new_temp_variable_name()
        else_flag_assign = ast.Assign(
            targets=[ast.Name(id=else_flag_name, ctx=ast.Store(), **pos)],
            value=ast.Constant(value=True),
            **pos,
        )
        set_is_var(else_flag_assign)
        if not _is_body_jumping(body):
            # <else_flag> = False
            else_flag_set_false = ast.Assign(
                targets=[ast.Name(id=else_flag_name, ctx=ast.Store(), **pos)],
                value=ast.Constant(value=False),
                **pos,
            )
            body.append(else_flag_set_false)
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
        body = get_let_pattern_body(node)
        if body is None:
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
        if not _is_body_jumping(body):
            # <continue_flag> = True at end of body
            continue_flag_set_true = ast.Assign(
                targets=[ast.Name(id=continue_flag_name, ctx=ast.Store(), **pos)],
                value=ast.Constant(value=True),
                **pos,
            )
            body.append(continue_flag_set_true)
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
