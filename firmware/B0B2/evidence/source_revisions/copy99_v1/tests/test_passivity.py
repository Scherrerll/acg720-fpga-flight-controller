"""Independent diagnostic write/driver audit, with negative mutation tests.

This complements token projection and the cycle miter. It lexes Verilog and
walks lvalues (including selections/concatenations/function return writes),
rather than assuming everything inside a DIAG_TAP region is harmless.
It is deliberately a strict subset audit, not a whole-netlist equivalence claim.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROTECTED = ("imu_checked_guard_pipelined.v",
             "ano_attitude_estimator.v", "imu_pipeline_pipelined.v")
IDENT = re.compile(r"[A-Za-z_$][\w$]*\Z")
LEX = re.compile(r'"(?:\\.|[^"\\])*"|\\[^\s]+|[A-Za-z_$][\w$]*|'
                 r"\d+'[sS]?[bBoOdDhH][\da-fA-F_xXzZ?]+|\d+|"
                 r"===|!==|<<<|>>>|<<=|>>=|<=|>=|==|!=|&&|\|\||\+\+|--|"
                 r"\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<|>>|\+:|-:|[^\s]")
DECL = {"input", "output", "inout", "wire", "reg", "logic", "integer", "parameter", "localparam", "genvar"}
QUAL = {"wire", "reg", "logic", "signed", "unsigned", "integer", "automatic", "static"}
PURE_SYSTEM = {"$signed", "$unsigned", "$clog2", "$bits", "$size", "$high", "$low"}
CONTROL_CALLS = {"if", "for", "while", "case", "casex", "casez", "repeat", "wait"}


class PassivityError(AssertionError):
    pass


def lex(text):
    text = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
    return LEX.findall(text)


def close(tokens, start):
    pairs = {"(": ")", "[": "]", "{": "}"}
    stack = [pairs[tokens[start]]]
    for index in range(start + 1, len(tokens)):
        token = tokens[index]
        if token in pairs:
            stack.append(pairs[token])
        elif token in pairs.values():
            if not stack or token != stack.pop():
                raise PassivityError("unbalanced diagnostic syntax")
            if not stack:
                return index
    raise PassivityError("unclosed diagnostic syntax")


def declarations(tokens):
    """Return declared names and input/output directions, skipping RHS/ranges."""
    names, directions = set(), {}
    index = 0
    while index < len(tokens):
        if tokens[index] not in DECL:
            index += 1
            continue
        direction = tokens[index] if tokens[index] in {"input", "output", "inout"} else None
        cursor = index + 1
        while cursor < len(tokens):
            while cursor < len(tokens) and tokens[cursor] in QUAL:
                cursor += 1
            while cursor < len(tokens) and tokens[cursor] == "[":
                cursor = close(tokens, cursor) + 1
            if cursor >= len(tokens) or not IDENT.fullmatch(tokens[cursor]):
                break
            name = tokens[cursor]
            names.add(name)
            if direction:
                directions[name] = direction
            cursor += 1
            # Unpacked dimensions and initializer expressions can contain reads.
            while cursor < len(tokens) and tokens[cursor] not in {",", ";", ")"}:
                if tokens[cursor] in {"(", "[", "{"}:
                    cursor = close(tokens, cursor) + 1
                else:
                    cursor += 1
            if cursor >= len(tokens) or tokens[cursor] != ",":
                break
            cursor += 1
            if cursor < len(tokens) and tokens[cursor] in DECL:
                break
        index = max(index + 1, cursor)
    return names, directions


def lvalue(tokens, end):
    """Parse a lvalue ending at end; index expression names are reads, not writes."""
    if end < 0:
        return None
    token = tokens[end]
    if token == "}":
        depth, start = 1, end - 1
        while start >= 0 and depth:
            if tokens[start] == "}": depth += 1
            if tokens[start] == "{": depth -= 1
            start -= 1
        start += 1
        if depth:
            return None
        roots, item_end = [], end - 1
        while item_end > start:
            item = lvalue(tokens, item_end)
            if item is None:
                raise PassivityError("unsupported concatenated write target")
            item_start, item_roots = item
            roots.extend(item_roots)
            if item_start == start + 1:
                break
            if tokens[item_start - 1] != ",":
                raise PassivityError("unsupported concatenated write target")
            item_end = item_start - 2
        return start, roots
    cursor = end
    while cursor >= 0 and tokens[cursor] == "]":
        depth, cursor = 1, cursor - 1
        while cursor >= 0 and depth:
            if tokens[cursor] == "]": depth += 1
            if tokens[cursor] == "[": depth -= 1
            cursor -= 1
        if depth:
            return None
    if cursor < 0 or not IDENT.fullmatch(tokens[cursor]):
        return None
    start = cursor
    while start >= 2 and tokens[start - 1] == "." and IDENT.fullmatch(tokens[start - 2]):
        start -= 2
    if start != cursor:
        raise PassivityError("hierarchical write target: " + "".join(tokens[start:end + 1]))
    return start, [tokens[cursor]]


def function_names(tokens):
    names = set()
    for index, token in enumerate(tokens):
        if token not in {"function", "task"}:
            continue
        cursor = index + 1
        while cursor < len(tokens) and tokens[cursor] not in {";", "("}:
            if tokens[cursor] == "[": cursor = close(tokens, cursor) + 1
            else: cursor += 1
        candidates = [t for t in tokens[index + 1:cursor] if IDENT.fullmatch(t) and t not in QUAL]
        if not candidates:
            raise PassivityError("unsupported function/task declaration")
        end_keyword = "endfunction" if token == "function" else "endtask"
        try:
            body_end = tokens.index(end_keyword, cursor)
        except ValueError as exc:
            raise PassivityError("unclosed function/task") from exc
        # Output/inout/ref arguments can modify caller state even when the
        # callee's formal name is diagnostic. This strict subset rejects them;
        # pure function return assignments are audited as ordinary lvalues.
        if any(t in {"output", "inout", "ref"} for t in tokens[cursor:body_end]):
            raise PassivityError("side-effecting function/task argument")
        names.add(candidates[-1])
    return names


def audit_tokens(tokens, allowed, port_directions, instances=()):
    """Check all write roots and output/inout actuals against an explicit set."""
    writes = []
    functions = function_names(tokens)
    for name in functions:
        if name not in allowed:
            raise PassivityError("unowned function/task output: " + name)
    for index, token in enumerate(tokens):
        if token in {"force", "release", "deassign", "alias"}:
            raise PassivityError("unsupported state-affecting construct: " + token)
        if token in {"=", "<=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>="}:
            target = lvalue(tokens, index - 1)
            if target is None:
                if token == "<=":  # relational expression, e.g. if ((x) <= y)
                    continue
                raise PassivityError("unsupported assignment lvalue")
            start, roots = target
            if token == "<=" and start and tokens[start - 1] not in {";", "begin", "end", "else", ":", ")"}:
                continue  # relational <= inside a condition/RHS
            for name in roots:
                if name not in allowed:
                    raise PassivityError("unowned write target: " + name)
                writes.append(name)
        if token in {"++", "--"}:
            target = lvalue(tokens, index - 1)
            if target is None and index + 1 < len(tokens) and IDENT.fullmatch(tokens[index + 1]):
                target = (index + 1, [tokens[index + 1]])
            if not target or any(name not in allowed for name in target[1]):
                raise PassivityError("unowned increment/decrement")
            writes.extend(target[1])
        if token == "." and index + 2 < len(tokens) and tokens[index + 2] == "(":
            port = tokens[index + 1]
            if port not in port_directions:
                raise PassivityError("unrecognized added port: " + port)
            end = close(tokens, index + 2)
            if port_directions[port] in {"output", "inout"}:
                actual = tokens[index + 3:end]
                if actual:
                    target = lvalue(actual, len(actual) - 1)
                    if not target or target[0] != 0 or any(name not in allowed for name in target[1]):
                        raise PassivityError("output drives unowned net: " + port)
                    writes.extend(target[1])
        if IDENT.fullmatch(token) and index + 1 < len(tokens) and tokens[index + 1] == "(":
            previous = tokens[index - 1] if index else ""
            if previous not in {".", "module"} and token not in CONTROL_CALLS | PURE_SYSTEM | functions | set(instances):
                raise PassivityError("unreviewed function/task/instance call: " + token)
    return writes


def audit_sources():
    regions, directions = [], {}
    # The deliberately replaced input policy is not a passive projection.
    # Its diagnostic ABI still supplies port directions for pipeline wiring.
    _, policy_ports = declarations(lex((ROOT / "source/core/imu_temporal_check_pipelined.v").read_text()))
    directions.update({name: direction for name, direction in policy_ports.items()
                       if name.startswith("diag_")})
    for name in PROTECTED:
        text = (ROOT / "source/core" / name).read_text()
        found = re.findall(r"// DIAG_TAP_BEGIN\n(.*?)// DIAG_TAP_END", text, flags=re.S)
        if len(found) != text.count("// DIAG_TAP_BEGIN") or len(found) != text.count("// DIAG_TAP_END"):
            raise PassivityError("unbalanced marker regions: " + name)
        for region in found:
            tokens = lex(region)
            names, ports = declarations(tokens)
            if any(not name.startswith("diag_") for name in names):
                raise PassivityError("unowned diagnostic declaration in " + name)
            directions.update(ports)
            regions.append((name, tokens))
    tap_tokens = lex((ROOT / "source/core/imu_diagnostic_tap.v").read_text())
    tap_names, tap_ports = declarations(tap_tokens)
    directions.update(tap_ports)
    result = {}
    for name, tokens in regions:
        names, _ = declarations(tokens)
        # Existing diagnostic declarations may live in a different marked region.
        allowed = {t for _, region in regions for t in region if IDENT.fullmatch(t) and t.startswith("diag_")}
        functions = function_names(tokens)
        if any(not function.startswith("diag_") for function in functions):
            raise PassivityError("unowned diagnostic function/task")
        allowed.update(functions)
        writes = audit_tokens(tokens, allowed, directions, instances={"diagnostic_tap"})
        result[name] = result.get(name, 0) + len(writes)
    # The new module owns local state only. Its input ports are reads, never writes.
    tap_allowed = tap_names - {name for name, direction in tap_ports.items() if direction == "input"}
    result["imu_diagnostic_tap.v"] = len(audit_tokens(tap_tokens, tap_allowed, tap_ports))
    summary_tokens = lex((ROOT / "source/sik_imu_diagnostic.v").read_text())
    summary_names, summary_ports = declarations(summary_tokens)
    summary_allowed = summary_names - {name for name, direction in summary_ports.items()
                                      if direction == "input"}
    result["sik_imu_diagnostic.v"] = len(audit_tokens(summary_tokens, summary_allowed, summary_ports))
    return result


class PassivityTests(unittest.TestCase):
    def audit(self, source, allowed=("diag_q", "diag_bus", "diag_fn")):
        return audit_tokens(lex(source), set(allowed), {"diag_out": "output", "diag_in": "input"})

    def test_actual_sources(self):
        print("DIAG_WRITE_AUDIT", audit_sources())

    def test_direct_control_write_rejected(self):
        with self.assertRaises(PassivityError): self.audit("always @(posedge clk) control_q <= diag_q;")

    def test_part_select_control_write_rejected(self):
        with self.assertRaises(PassivityError): self.audit("always @(posedge clk) begin control_q[index +: 8] <= diag_q; end")

    def test_concat_control_write_rejected(self):
        with self.assertRaises(PassivityError): self.audit("assign {diag_q, control_q[7:0]} = diag_bus;")

    def test_function_output_control_write_rejected(self):
        with self.assertRaises(PassivityError): self.audit("function [7:0] control_fn; begin control_fn = diag_q; end endfunction")

    def test_function_body_control_write_rejected(self):
        with self.assertRaises(PassivityError): self.audit("function [7:0] diag_fn; begin control_q[0] = 1; diag_fn = diag_q; end endfunction")

    def test_function_output_argument_side_effect_rejected(self):
        with self.assertRaises(PassivityError):
            self.audit("function void diag_fn(output reg diag_q); diag_q=0; endfunction diag_fn(control_q);")

    def test_task_output_argument_side_effect_rejected(self):
        with self.assertRaises(PassivityError):
            self.audit("task diag_fn; output diag_q; begin diag_q=0; end endtask diag_fn(control_q);")

    def test_function_ref_argument_side_effect_rejected(self):
        with self.assertRaises(PassivityError):
            self.audit("function void diag_fn(ref logic diag_q); diag_q=0; endfunction diag_fn(control_q);")

    def test_hierarchical_write_rejected(self):
        with self.assertRaises(PassivityError): self.audit("always @(posedge clk) diag_helper.control_q <= 0;")

    def test_added_output_control_driver_rejected(self):
        with self.assertRaises(PassivityError): self.audit(".diag_out(control_q[7:0])")

    def test_external_task_side_effect_rejected(self):
        with self.assertRaises(PassivityError): self.audit("always @(posedge clk) control_task(diag_q);")

    def test_diag_selected_lvalues_and_function_allowed(self):
        self.audit("function [7:0] diag_fn; begin diag_fn=diag_q; end endfunction\n"
                   "always @(posedge clk) if(control_q <= 3) diag_bus[control_index +: 8] <= diag_fn();\n"
                   "assign {diag_q,diag_bus[7:0]} = control_bus; .diag_out(diag_bus[3:0]) .diag_in(control_q)")

    def test_increment_control_rejected(self):
        with self.assertRaises(PassivityError): self.audit("always @(posedge clk) control_q++;")


if __name__ == "__main__":
    unittest.main(verbosity=2)
