import re
from typing import Optional, Dict, Any, List, Tuple
from .config.sums import SumType, SumTypeMetaclass
from .util import maybe_dotted
import logging


log = logging.getLogger(__name__)


# A replacement marker in a pattern must begin with an uppercase or
# lowercase ASCII letter or an underscore, and can be composed only
# of uppercase or lowercase ASCII letters, underscores, and numbers.
# For example: a, a_b, and b9 are all valid replacement marker names, but 0a is not.
ROUTE_PATTERN_OPEN_BRACES_RE = re.compile('(?P<start_brace>\{).*')
ROUTE_PATTERN_CLOSING_BRACES_RE = re.compile('\}.*')
EMBEDDED_SUM_TYPE_RE = re.compile('\<(?P<sum_type>[a-zA-Z0-9_.:]+)\>')


def _extract_braces_expression(line: str, starting_braces_re, open_braces_re, closing_braces_re):
    """ This function is taken from Plim package: https://pypi.python.org/pypi/Plim/

    :param line: may be empty
    :param starting_braces_re:
    :param open_braces_re:
    :param closing_braces_re:
    """
    match = starting_braces_re.match(line)
    if not match:
        return None

    open_brace = match.group('start_brace')
    buf = [open_brace]
    tail = line[len(open_brace):]
    braces_counter = 1

    while tail:
        current_char = tail[0]
        if closing_braces_re.match(current_char):
            braces_counter -= 1
            buf.append(current_char)
            if braces_counter:
                tail = tail[1:]
                continue
            return ''.join(buf), tail[1:]

        if open_braces_re.match(current_char):
            braces_counter += 1
            buf.append(current_char)
            tail = tail[1:]
            continue

        buf.append(current_char)
        tail = tail[1:]
    raise Exception("Unexpected end of a route pattern: {}".format(line))


extract_pattern = lambda line: _extract_braces_expression(
    line,
    ROUTE_PATTERN_OPEN_BRACES_RE,
    ROUTE_PATTERN_OPEN_BRACES_RE,
    ROUTE_PATTERN_CLOSING_BRACES_RE
)


def normalize_route_pattern(pattern: str) -> Tuple[str, str, Dict[str, SumType]]:
    buf = []
    rules = {}
    name_parts = {}
    while pattern:
        result = extract_pattern(pattern)
        if result:
            extracted, pattern = result
            if ':' in extracted:
                # Remove braces from the extracted result "{pattern[:rule]}"
                pattern_name, rule = extracted[1:-1].split(':', 1)
                embedded_sum_type = EMBEDDED_SUM_TYPE_RE.match(rule)
                if embedded_sum_type:
                    sum_type = maybe_dotted(embedded_sum_type.group('sum_type'))
                    rules[pattern_name] = sum_type
                    url_part = '{{{}}}'.format(pattern_name)
                else:
                    url_part = extracted
                    name_parts[extracted] = pattern_name
            else:
                url_part = extracted

            buf.append(url_part)
            continue

        buf.append(pattern[0])
        pattern = pattern[1:]

    # Parsing is done. Now join everything together
    final_pattern = ''.join(buf)
    route_name = final_pattern
    for pattern, name in name_parts.items():
        route_name = route_name.replace(pattern, '{%s}' % name, 1)
    return route_name, final_pattern, rules


def complete_route_pattern(pattern: str, rules: Dict[str, SumType]) -> str:
    """
    :param pattern: URL pattern
    """
    buf = []
    while pattern:
        result = extract_pattern(pattern)
        if result:
            result, pattern = result
            # Remove braces from the result "{pattern[:rule]}"
            result = result[1:-1]
            if ':' in result:
                # pattern in a "pattern_name:rule" form
                match_group_name, rule = result.split(':', 1)
            else:
                # pattern in a "pattern_name" form
                match_group_name = result
                rule = rules.get(match_group_name)
                if not rule:
                    # Use default pattern
                    rule = '[^/]+'
                elif isinstance(rule, SumTypeMetaclass):
                    # Compose SumType's regex
                    rule = '(?:{})'.format('|'.join([str(v) for v in rule.values()]))

            result = "{{{match_group_name}:{rule}}}".format(
                match_group_name=match_group_name,
                rule=rule
            )
            buf.append(result)
            continue

        buf.append(pattern[0])
        pattern = pattern[1:]

    # Parsing is done. Now join everything together
    buf = ''.join(buf)
    return buf
