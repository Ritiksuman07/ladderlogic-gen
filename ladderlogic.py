import argparse
import sys
import re

# Supported platforms
PLATFORMS = ['siemens', 'allen-bradley', 'mitsubishi', 'omron']

# --- Expression Parsing ---
class ExprNode:
    def __init__(self, kind, value=None, left=None, right=None):
        self.kind = kind  # 'AND', 'OR', 'NOT', 'VAR', 'CMP', 'TIMER', 'COUNTER'
        self.value = value  # For VAR: name, for CMP: (left, op, right), for TIMER/COUNTER: (type, name, param)
        self.left = left
        self.right = right

    def __repr__(self):
        if self.kind == 'VAR':
            return self.value
        elif self.kind == 'CMP':
            l, op, r = self.value
            return f'({l} {op} {r})'
        elif self.kind == 'NOT':
            return f'NOT({self.left})'
        elif self.kind in ('TIMER', 'COUNTER'):
            t, n, p = self.value
            return f'{t} {n}, {p}'
        else:
            left = self.left if self.left is not None else ''
            right = self.right if self.right is not None else ''
            return f'({left} {self.kind} {right})'

# Tokenizer for logic expressions
TOKEN_REGEX = re.compile(r'\s*(\(|\)|AND|OR|NOT|[A-Za-z_][A-Za-z0-9_]*|[<>]=?|==|!=|\d+\.?\d*|,|TON|TOF|CTU|CTD|\d+s|\d+ms)')

CMP_OPS = {'>', '<', '>=', '<=', '==', '!='}
TIMER_TYPES = {'TON', 'TOF'}
COUNTER_TYPES = {'CTU', 'CTD'}


def tokenize(expr):
    tokens = TOKEN_REGEX.findall(expr)
    return [t for t in tokens if t.strip()]

# Recursive descent parser for logic expressions
# Grammar:
# expr   := or_expr
# or_expr := and_expr (OR and_expr)*
# and_expr := not_expr (AND not_expr)*
# not_expr := NOT not_expr | atom
# atom   := VAR | CMP | '(' expr ')'

def parse_expr(tokens):
    def parse_atom(idx):
        if tokens[idx] == '(':  # Parenthesized
            node, idx = parse_or(idx + 1)
            if tokens[idx] != ')':
                raise ValueError('Mismatched parentheses')
            return node, idx + 1
        # Comparison
        if (idx + 2 < len(tokens)) and (tokens[idx+1] in CMP_OPS):
            left = tokens[idx]
            op = tokens[idx+1]
            right = tokens[idx+2]
            node = ExprNode('CMP', (left, op, right))
            return node, idx + 3
        # Variable
        node = ExprNode('VAR', tokens[idx])
        return node, idx + 1

    def parse_not(idx):
        if idx < len(tokens) and tokens[idx] == 'NOT':
            child, idx = parse_not(idx + 1)
            return ExprNode('NOT', left=child), idx
        return parse_atom(idx)

    def parse_and(idx):
        left, idx = parse_not(idx)
        while idx < len(tokens) and tokens[idx] == 'AND':
            right, idx = parse_not(idx + 1)
            left = ExprNode('AND', left=left, right=right)
        return left, idx

    def parse_or(idx):
        left, idx = parse_and(idx)
        while idx < len(tokens) and tokens[idx] == 'OR':
            right, idx = parse_and(idx + 1)
            left = ExprNode('OR', left=left, right=right)
        return left, idx

    node, idx = parse_or(0)
    if idx != len(tokens):
        raise ValueError('Unexpected tokens at end')
    return node

# --- Parsing logic lines ---
def parse_logic_line(line):
    """
    Parse a single line of logic description.
    Example: IF Start AND NOT Stop THEN Motor
    Returns: (ExprNode, [outputs]) or (ExprNode, [timer/counter])
    """
    line = line.strip()
    if not line or not line.lower().startswith('if'):
        return None
    try:
        cond_part, then_part = line[2:].split('THEN', 1)
        conditions = cond_part.strip()
        then_part = then_part.strip()
        # Timer/Counter detection: e.g., TON Timer1, 5s
        timer_match = re.match(r'(TON|TOF)\s+([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([0-9]+(ms|s))', then_part)
        counter_match = re.match(r'(CTU|CTD)\s+([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([0-9]+)', then_part)
        if timer_match:
            ttype, tname, tparam, _ = timer_match.groups()
            tokens = tokenize(conditions)
            expr = parse_expr(tokens)
            return (expr, [ExprNode('TIMER', (ttype, tname, tparam))])
        elif counter_match:
            ctype, cname, cparam, _ = counter_match.groups()
            tokens = tokenize(conditions)
            expr = parse_expr(tokens)
            return (expr, [ExprNode('COUNTER', (ctype, cname, cparam))])
        else:
            outputs = [o.strip() for o in then_part.split(',')]
            tokens = tokenize(conditions)
            expr = parse_expr(tokens)
            return (expr, outputs)
    except Exception:
        return None

# --- Ladder Logic Generation ---
def expr_to_ladder(expr, platform, indent='     '):
    """
    Recursively convert ExprNode to ladder logic string for the given platform.
    """
    if expr.kind == 'VAR':
        return '[ ] ' + expr.value
    if expr.kind == 'NOT':
        child = expr_to_ladder(expr.left, platform, indent)
        if child is None:
            return None
        return '[/] ' + child
    if expr.kind == 'AND':
        left = expr_to_ladder(expr.left, platform, indent)
        right = expr_to_ladder(expr.right, platform, indent)
        if left is None or right is None:
            return None
        return left + '----' + right
    if expr.kind == 'OR':
        # For simplicity, represent OR as separate rungs
        # The caller should handle this
        return None
    if expr.kind == 'CMP':
        l, op, r = expr.value
        return f'[ ] {l} {op} {r}'
    return ''

def timer_counter_to_ladder(tc_expr, platform, indent='     '):
    # Platform-specific timer/counter rung
    if tc_expr.kind == 'TIMER':
        ttype, tname, tparam = tc_expr.value
        if platform == 'siemens':
            return f'{indent}{ttype} {tname} Time: {tparam}\n'
        elif platform == 'allen-bradley':
            return f'{indent}{ttype} {tname} Preset: {tparam}\n'
        elif platform == 'mitsubishi':
            return f'{indent}{ttype} {tname} K{tparam}\n'
        elif platform == 'omron':
            return f'{indent}{ttype} {tname} {tparam}\n'
        else:
            return f'{indent}{ttype} {tname} {tparam}\n'
    elif tc_expr.kind == 'COUNTER':
        ctype, cname, cparam = tc_expr.value
        if platform == 'siemens':
            return f'{indent}{ctype} {cname} Count: {cparam}\n'
        elif platform == 'allen-bradley':
            return f'{indent}{ctype} {cname} Preset: {cparam}\n'
        elif platform == 'mitsubishi':
            return f'{indent}{ctype} {cname} K{cparam}\n'
        elif platform == 'omron':
            return f'{indent}{ctype} {cname} {cparam}\n'
        else:
            return f'{indent}{ctype} {cname} {cparam}\n'
    return ''

def generate_ladder(expr, outputs, platform):
    # Handle OR at the top level as separate rungs
    if expr.kind == 'OR':
        left_ladder = generate_ladder(expr.left, outputs, platform)
        right_ladder = generate_ladder(expr.right, outputs, platform)
        ladders = []
        if left_ladder:
            ladders.append(left_ladder)
        if right_ladder:
            ladders.append(right_ladder)
        return '\n'.join(str(l) for l in ladders)
    rung_body = expr_to_ladder(expr, platform)
    if rung_body is None:
        return ''
    rung = f'// Rung\n|----{rung_body}----( )----|\n'
    # Check for timer/counter outputs
    tc_outputs = [o for o in outputs if isinstance(o, ExprNode) and o.kind in ('TIMER', 'COUNTER')]
    normal_outputs = [o for o in outputs if isinstance(o, str)]
    if normal_outputs:
        rung += '     ' + ', '.join(normal_outputs) + '\n'
    for tc in tc_outputs:
        rung += timer_counter_to_ladder(tc, platform)
    rung += '\n'
    return rung

# --- Main CLI ---
def main():
    parser = argparse.ArgumentParser(description='Logic Ladder Generator for PLCs')
    parser.add_argument('--input', '-i', required=True, help='Input logic description file')
    parser.add_argument('--platform', '-p', required=True, choices=PLATFORMS, help='Target PLC platform')
    parser.add_argument('--output', '-o', required=True, help='Output ladder logic file')
    args = parser.parse_args()

    try:
        with open(args.input, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f'Error reading input file: {e}')
        sys.exit(1)

    output_lines = []
    for line in lines:
        parsed = parse_logic_line(line)
        if not parsed:
            continue
        expr, outputs = parsed
        ladder = generate_ladder(expr, outputs, args.platform)
        output_lines.append(ladder)

    try:
        with open(args.output, 'w') as f:
            f.writelines(output_lines)
        print(f'Ladder logic generated for {args.platform} and saved to {args.output}')
    except Exception as e:
        print(f'Error writing output file: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main() 
