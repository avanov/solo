import re


# A replacement marker in a pattern must begin with an uppercase or
# lowercase ASCII letter or an underscore, and can be composed only
# of uppercase or lowercase ASCII letters, underscores, and numbers.
# For example: a, a_b, _b, and b9 are all valid replacement marker names, but 0a is not.
ROUTE_PATTERN_OPEN_BRACES_RE = re.compile('(?P<start_brace>\{).*')
ROUTE_PATTERN_CLOSING_BRACES_RE = re.compile('\}.*')


def _extract_braces_expression(line, starting_braces_re, open_braces_re, closing_braces_re):
    """
    This function is taken from Plim package: https://pypi.python.org/pypi/Plim/

    :param line: may be empty
    :type line: str
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
            return u''.join(buf), tail[1:]

        if open_braces_re.match(current_char):
            braces_counter += 1
            buf.append(current_char)
            tail = tail[1:]
            continue

        buf.append(current_char)
        tail = tail[1:]
    raise Exception("Unexpected end of a route definition: {}".format(line))


extract_pattern = lambda line: _extract_braces_expression(
    line,
    ROUTE_PATTERN_OPEN_BRACES_RE,
    ROUTE_PATTERN_OPEN_BRACES_RE,
    ROUTE_PATTERN_CLOSING_BRACES_RE
)
