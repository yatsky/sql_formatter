# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/00_core.ipynb (unless otherwise specified).

__all__ = ['MAIN_STATEMENTS', 'clean_query', 'preformat_statements', 'lowercase_query', 'format_partition_by',
           'format_select', 'format_from', 'format_join', 'format_on', 'format_where', 'format_statement_line',
           'format_statements', 'format_multiline_comments', 'format_simple_sql', 'format_sql']

# Cell
import re
from .utils import *

# Cell
MAIN_STATEMENTS = [
    "create.*?table",  # regex for all variants, e.g. CREATE OR REPLACE TABLE
    "create.*?view",  # regex for all variants, e.g. CREATE OR REPLACE VIEW
    "select distinct",
    "select",
    "from",
    "left join",
    "inner join",
    "outer join",
    "right join",
    "union",
    "on",
    "where",
    "group by",
    "order by",
    "over",  # special case: no newline, only capitalized
    "partition by",  # special case: no newline, only capitalized
]

# Cell
def clean_query(s):
    "Remove redundant whitespaces and mark comments boundaries and remove newlines afterwards in query `s`"
    s = remove_redundant_whitespaces(s)  # remove too many whitespaces but no newlines
    s = mark_comments(s)  # mark comments with special tokens [C], [CS] and [CI]
    s = replace_newline_chars(s)  # remove newlines but not in the comments
    s = remove_whitespaces_newline(s)  # remove whitespaces after and before newline
    s = remove_whitespaces_comments(s)  # remove whitespaces after and before [C], [CS] and [CI]
    s = remove_redundant_whitespaces(s)  # remove too many whitespaces but no newlines
    return s

# Cell
def preformat_statements(s):
    """Write a newline in `s` for all `statements` and
    uppercase them but not if they are inside a comment"""
    statements = MAIN_STATEMENTS
    s = clean_query(s)  # clean query and mark comments
    split_s = split_comment_select(s)  # split by comment and non comment
    # compile regex before loop
    create_re = re.compile("create", flags=re.I)
    select_re = re.compile("select", flags=re.I)
    for statement in statements:
        if create_re.match(statement):  # special case CREATE with AS capitalize as well
            create_sub = re.compile(rf"\s*({statement} )(.*) as\b", flags=re.I)
            split_s = [{
                "string": create_sub.sub(
                    lambda pat: "\n" + pat.group(1).upper() + pat.group(2) + " AS",
                    sdict["string"],
                    ) if not sdict["comment"] else sdict["string"],
                    "comment": sdict["comment"],
                    "select": sdict["select"]
                } for sdict in split_s]
        else:  # normal main statements
            non_select_region_re = re.compile(rf"\s*\b({statement})\b", flags=re.I)
            select_region_statement_re = re.compile(rf"\b({statement})\b", flags=re.I)
            split_s = [{
                "string": non_select_region_re.sub("\n" + statement.upper(), sdict["string"])
                    if not sdict["comment"] and not sdict["select"]  # no comment, no select region
                    else non_select_region_re.sub("\n" + statement.upper(), sdict["string"])
                    if not sdict["comment"] and sdict["select"] and select_re.match(statement) # no comment, select region and select statement
                    else select_region_statement_re.sub(statement.upper(), sdict["string"])
                    if not sdict["comment"] and sdict["select"] and not select_re.match(statement) # no comment, select region and no select statement
                    else sdict["string"],
                "comment": sdict["comment"],
                "select": sdict["select"]
                } for sdict in split_s]
    s = "".join([sdict["string"] for sdict in split_s])
    s = remove_whitespaces_newline(s)  # remove whitespaces before and after newline
    return s

# Cell
def lowercase_query(s):
    "Lowercase query but let comments and text in quotes untouched"
    k = 0  # indicator for position
    comment_open1 = False # comment indicator for /* */ comments
    comment_open2 = False  # comment indicator for -- comments
    quote_open1 = False  # quote '
    quote_open2 = False # quote "
    split_s = []  # container for splitted string
    for i, c in enumerate(s):
        if (
            s[i:i+2] == "/*" and
            not comment_open1 and
            not comment_open2 and
            not quote_open1 and
            not quote_open2
        ):  # if there is an opening comment /*
            split_s.append({
                "string": s[k:i], # up to opening comment can be lowercased
                "lowercase": True
            })
            k = i  # update string start
            comment_open1 = True
        elif (
            s[i:i+2] == "*/" and
            comment_open1 and
            not comment_open2 and
            not quote_open1 and
            not quote_open2
        ):  # if there is a closing comment */
            split_s.append({
                "string": s[k:i],
                "lowercase": False
            })
            k = i  # update string start
            comment_open1 = False
        elif (
            s[i:i+2] == "--" and
            not comment_open1 and
            not comment_open2 and
            not quote_open1 and
            not quote_open2
        ):  # if there is an opening comment --
            split_s.append({
                "string": s[k:i],
                "lowercase": True
            })
            k = i  # update string start
            comment_open2 = True
        elif (
            c == "\n" and
            not comment_open1 and
            comment_open2 and
            not quote_open1 and
            not quote_open2
        ):  # if the -- comment ends
            split_s.append({
                "string": s[k:i],
                "lowercase": False
            })
            k = i  # update string start
            comment_open2 = False
        elif (
            c == "'" and
            not comment_open1 and
            not comment_open2 and
            not quote_open1 and
            not quote_open2
        ):  # if opening quote '
            split_s.append({
                "string": s[k:i],
                "lowercase": True
            })
            k = i  # update string start
            quote_open1 = True
        elif (
            c == "'" and
            not comment_open1 and
            not comment_open2 and
            quote_open1 and
            not quote_open2
        ):  # if closing quote '
            split_s.append({
                "string": s[k:i],
                "lowercase": False
            })
            k = i  # update string start
            quote_open1 = False
        elif (
            c == '"' and
            not comment_open1 and
            not comment_open2 and
            not quote_open1 and
            quote_open2
        ):  # if opening quote "
            split_s.append({
                "string": s[k:i],
                "lowercase": True
            })
            k = i  # update string start
            quote_open2 = True
        elif (
            c == '"' and
            not comment_open1 and
            not comment_open2 and
            not quote_open1 and
            quote_open2
        ):  # if closing quote "
            split_s.append({
                "string": s[k:i],
                "lowercase": False
            })
            k = i  # update string start
            quote_open2 = False
    split_s.append({
        "string": s[k:],
        "lowercase": True
    })  # append remainder
    # lowercase everything not in comments or in quotes
    split_s = [
        elem["string"].lower() if elem["lowercase"] else elem["string"]
        for elem in split_s
    ]
    s = "".join(split_s)
    return s

# Cell
def format_partition_by(s, base_indentation):
    "Format PARTITION BY line in SELECT (DISTINCT)"
    orderby_involved = bool(re.search("order by", s, flags=re.I))
    if orderby_involved:
        split_s = re.split("(partition by.*)(order by.*)", s, flags=re.I)  # split PARTITION BY
    else:
        split_s = re.split("(partition by.*)", s, flags=re.I)  # split PARTITION BY
    split_s = [sp for sp in split_s if sp != ""]
    begin_s = split_s[0]
    partition_by = split_s[1]
    indentation = base_indentation + len(begin_s) + 13
    # add newline after each comma (no comments) and indentation
    partition_by = add_newline_indentation(partition_by, indentation=indentation)
    # add new line and indentation after order by
    if orderby_involved:
        partition_by = "".join([partition_by, " "] + split_s[2:])
    partition_by = re.sub(
        r"\s(order by.*)", "\n" + " " * (base_indentation + len(begin_s)) + r"\1",
        partition_by,
        flags=re.I
    )
    # combine begin of string with formatted partition by
    s = begin_s + partition_by
    s = s.strip()
    return s

# Cell
def format_select(s):
    "Format SELECT statement line `s`"
    # remove [C] at end of SELECT
    if re.search(r"\[C\]$", s):
        s = re.sub(r"\[C\]$", "", s)
    # if comma is found at the end of select statement then remove comma
    if re.search(r"[\w\d]+,\s*$", s, flags=re.I):
        s = re.sub(r"([\w\d]+)(,+)(\s*)$", r"\1", s, flags=re.I)
    elif re.search(r"[\w\d]+,\s*--[\w\d\s]*$", s, flags=re.I):
        s = re.sub(r"([\w\d]+)(,+)(\s*)(--.*)$", r"\1 \4", s, flags=re.I)
    elif re.search(r"[\w\d]+,\s*\/\*.*\*\/$", s, flags=re.I):
        s = re.sub(r"([\w\d]+)(,+)(\s*)(\/\*.*\*\/)$", r"\1 \4", s, flags=re.I)
    s = add_whitespaces_between_symbols(s)  # add whitespaces between symbols
    # check whether there is a SELECT DISTINCT
    indentation = 16 if re.search("^select distinct", s, flags=re.I) else 7
    s = add_newline_indentation(s, indentation=indentation)  # add newline after each comma (no comments) and indentation
    s = re.sub(r"\[C\]\[CS\]", "[C]", s)  # replace [C][CS] by [C]
    s = re.sub(r"\[C\]", "\n" + " " * indentation, s)  # replace [C] by newline
    s = re.sub(r"\[CS\]", "\n" + " " * indentation, s)  # replace [CS] by newline
    s = re.sub(r"(then.*?) ((?:when|else).*?)", r"\1\n\2", s, flags=re.I)  # add newline before when or else
    split_s = s.split("\n")
    split_s_out = []
    case_extra_indentation = 0
    # compile regex before loop
    case_when_re = re.compile("case when", flags=re.I)
    when_else_re = re.compile("^(?:when|else)", flags=re.I)
    for line in split_s:
        strip_line = line.strip()
        case_when_search = case_when_re.search(strip_line)
        if case_when_search:
            case_extra_indentation = case_when_search.start()
        if when_else_re.match(strip_line):
            split_s_out.append(" " * (12 + case_extra_indentation) + strip_line)
        else:
            split_s_out.append(line)
    s = "\n".join(split_s_out)
    s = s.strip()
    # format partition by
    begin_s = s[0:indentation]
    split_s = s[indentation:].split("\n" + (" " * indentation))
    partition_by_re = re.compile("partition by", flags=re.I)
    split_s = [
        format_partition_by(line, base_indentation=indentation)
        if partition_by_re.search(line) else line
        for line in split_s
    ]
    s = begin_s + ("\n" + (" " * indentation)).join(split_s)
    return s

# Cell
def format_from(s):
    "Format FROM statement line `s`"
    s = re.sub(  # add indentation
        r"(from )(.*)",
        r"\1  \2",
        s,
        flags=re.I
    )
    return s

# Cell
def format_join(s):
    "Format JOIN statement line `s`"
    s = "    " + s  # add indentation
    return s

# Cell
def format_on(s):
    "Format ON statement line `s`"
    s = add_whitespaces_between_symbols(s)  # add whitespaces between symbols in join
    s = s.replace("[C]", " ")
    s = "        " + s  # add indentation
    s = re.sub(r"and\s", r"and\n" + " " * 11, s, flags=re.I)  # add new line before every 'and' and indentation
    s = re.sub(r"or\s", r"or\n" + " " * 11, s, flags=re.I)  # add new line before every 'or' and indentation
    return s

# Cell
def format_where(s):
    "Format WHERE statement line `s`"
    s = add_whitespaces_between_symbols(s)  # add whitespaces between symbols
    s = s.replace("[C]", " ")
    s = re.sub(r"(where )", r"\1 ", s, flags=re.I)  # add indentation afer WHERE
    s = re.sub(r"\sand", r"\n   and", s, flags=re.I)  # add new line before every 'and' and indentation
    s = re.sub(r"\sor", r"\n    or", s, flags=re.I)  # add new line before every 'or' and indentation
    return s

# Cell
def format_statement_line(s):
    "Format statement line `s`"
    statement_funcs = {
        "select": format_select,
        "from": format_from,
        "left join": format_join,
        "right join": format_join,
        "inner join": format_join,
        "outer join": format_join,
        "on": format_on,
        "where": format_where,
    }
    for key, format_func in statement_funcs.items():
        if re.match(key, s, flags=re.I):
            s = format_func(s)
    return s

# Cell
def format_statements(s):
    "Format statements lines `s`"
    statement_lines = s.split("\n")
    formatted_lines = [
        format_statement_line(line) for line in statement_lines
    ]
    formatted_s = "\n".join(formatted_lines)
    return formatted_s

# Cell
def format_multiline_comments(s):
    "Format multiline comments by replacing multiline comment [CI] by newline and adding indentation"
    split_s = s.split("\n")
    split_out = []
    for sp in split_s:  # loop on query lines
        if re.search(r"\[CI\]", sp):
            indentation = re.search(r"\/\*", sp).start() + 3
            sp_indent = re.sub(r"\[CI\]", "\n" + " " * indentation, sp)
            split_out.append(sp_indent)
        else:
            split_out.append(sp)
    s = "\n".join(split_out)
    return s

# Cell
def format_simple_sql(s):
    "Format a simple SQL query without subqueries `s`"
    s = lowercase_query(s)  # everything lowercased but not the comments
    s = preformat_statements(s)  # add breaklines for the main statements
    s = format_statements(s)  # format statements
    s = re.sub(r"\[C\]", "", s)  # replace remaining [C]
    s = re.sub(r"\[CS\]", "\n", s)  # replace remaining [CS]
    s = re.sub(r"\s+\n", "\n", s)  # replace redundant whitespaces before newline
    s = format_multiline_comments(s)  # format multline comments
    s = s.strip()  # strip query
    return s

# Cell
def format_sql(s):
    "Format SQL query with subqueries `s`"
    s = format_simple_sql(s)  # basic query formatting
    # get first outer subquery positions
    subquery_pos = extract_outer_subquery(s)
    # loop over subqueries
    while subquery_pos is not None:
        # get split
        split_s = [
            s[0:subquery_pos[0]],
            s[subquery_pos[0]:(subquery_pos[1]+1)],
            s[(subquery_pos[1]+1):]
        ]
        # format subquery (= split_s[1])
        split_s[1] = format_subquery(split_s[1], split_s[0])
        # join main part and subquery
        s = "".join(split_s)
        # get first outer subquery positions
        subquery_pos = extract_outer_subquery(s)
    # remove whitespace between word and parenthesis
    s = re.sub(r"\s*\)", ")", s)
    return s