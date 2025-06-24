import os
import sys

# Add project root to sys.path so 'src' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import re
from typing import Any, List, Tuple

from src.instructor.base_models import AliasEnum
from src.instructor.filter_models import AgeFilter, BooleanFilter, BooleanProperty, ComparisonProperty, DateFilter, FilterResponse, LogicalFilter, NIHSSFilter, OperatorProperty, SexFilter, SexProperty, StrokeFilter, StrokeProperty
from src.instructor.metric_models import KPI, Distribution, GroupProperty, Metric, MetricResponse, MetricsCollection
from src.instructor.models import MetricCalculatorResponse


def parse_cli_command(command: str) -> dict[str, Any]:
    command = command.strip()
    if command.startswith("/query"):
        command = command[len("/query") :].strip()

    # Regex to split on flags while keeping them
    tokens = re.split(r"(?= -)", command)
    base_args = tokens[0].strip().split()

    args: dict[str, Any] = {
        "metrics": base_args,
        "filter": None,
        "group": None,
        "distribution": [],
        "stats": False,
    }

    for token in tokens[1:]:
        token = token.strip()
        if token.startswith("-filter"):
            args["filter"] = token[len("-filter") :].strip()
        elif token.startswith("-group"):
            args["group"] = token[len("-group") :].strip()
        elif token.startswith("-distribution"):
            dist_raw = token[len("-distribution") :].strip()
            args["distribution"] = dist_raw.split()
        elif token.startswith("-stats"):
            args["stats"] = True

    return args


Token = Tuple[str, str]

TOKEN_REGEX = [
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("COMMA", r","),
    ("OPERATOR", r"\b(?:AND|OR|NOT)\b"),
    ("COMPARISON", r"(==|!=|>=|<=|>|<)"),
    ("IDENT", r"[A-Z_]+"),
    ("NUMBER", r"\d+"),
    ("STRING", r"[A-Z_]+"),  # for enum-like values
    ("SKIP", r"\s+"),
]


def tokenize(input_str: str) -> List[Token]:
    pattern = "|".join(f"(?P<{name}>{regex})" for name, regex in TOKEN_REGEX)
    scanner = re.compile(pattern)
    tokens: List[Token] = []

    for match in scanner.finditer(input_str):
        kind = match.lastgroup
        value = match.group()
        if kind is not None and kind != "SKIP":
            tokens.append((kind, value))

    return tokens


class FilterParser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else ("EOF", "")

    def consume(self, expected_type: str | None = None) -> Token:
        token = self.peek()
        if expected_type and token[0] != expected_type:
            raise SyntaxError(f"Expected token {expected_type}, got {token} at position {self.pos}")
        self.pos += 1
        return token

    def parse(self) -> LogicalFilter:
        return self.filter()

    def filter(self) -> LogicalFilter:
        op_token = self.consume("OPERATOR")
        self.consume("LPAREN")
        children = self.expr_list()
        self.consume("RPAREN")
        return LogicalFilter(operator=OperatorProperty(op_token[1]), children=children)

    def expr_list(self) -> List[Any]:
        children = [self.expr()]
        while self.peek()[0] == "COMMA":
            self.consume("COMMA")
            children.append(self.expr())
        return children

    def expr(self) -> Any:
        token = self.peek()
        if token[0] == "OPERATOR":
            return self.filter()
        else:
            return self.condition()

    def condition(self):
        ident_token = self.consume("IDENT")
        ident_str = ident_token[1].upper()

        comp_token = self.consume("COMPARISON")
        comparison = ComparisonProperty.from_value(comp_token[1])

        value_token = self.consume()
        value_str = value_token[1]

        # Integer filters
        if ident_str == "AGE":
            return AgeFilter(operator=comparison, value=int(value_str))
        elif ident_str == "NIHSS":
            return NIHSSFilter(operator=comparison, value=int(value_str))

        # Date filters (only support DISCHARGEDATE for now)
        elif ident_str == "DISCHARGEDATE":
            return DateFilter(operator=comparison, value=value_str)

        # Enum filters
        try:
            return SexFilter(value=SexProperty.from_value(value_str))
        except ValueError:
            pass

        try:
            return StrokeFilter(value=StrokeProperty.from_value(value_str))
        except ValueError:
            pass

        try:
            return BooleanFilter(property=BooleanProperty.from_value(ident_str), value=value_str.lower() == "true")
        except ValueError:
            pass

        raise ValueError(f"Unknown identifier or unsupported filter: {ident_str}")


def parse_filter_string(input_str: str) -> LogicalFilter:
    tokens = tokenize(input_str)
    parser = FilterParser(tokens)
    return parser.parse()


ALL_ENUMS: list[type[AliasEnum]] = [BooleanProperty, SexProperty, StrokeProperty]


def resolve_enum_type(identifier: str):
    for enum_cls in ALL_ENUMS:
        try:
            return enum_cls.from_value(identifier), enum_cls
        except ValueError:
            continue
    return None, None


def parse_metrics(metrics: list[str], distribution: list[str], stats: bool) -> list[Metric]:
    # Parse distribution into a lookup: {"DTN": Distribution(...)}
    dist_map: dict[str, Distribution] = {}
    for dist_spec in distribution:
        try:
            kpi_str, bin_count, lower, upper = dist_spec.split(":")
            dist_map[kpi_str.upper()] = Distribution(
                bin_count=int(bin_count),
                lower=int(lower),
                upper=int(upper),
            )
        except Exception as e:
            raise ValueError(f"Invalid distribution spec '{dist_spec}': {e}")

    result: list[Metric] = []
    for name in metrics:
        try:
            kpi = KPI.from_value(name)
            metric = Metric(kpi=kpi, stats=stats, distribution=dist_map.get(kpi.value))
            result.append(metric)
        except ValueError as e:
            raise ValueError(f"Unknown KPI/metric '{name}': {e}")

    return result


def build_metric_response(metrics: list[str], distribution: list[str], stats: bool, group: str | None) -> MetricResponse:
    parsed_metrics = parse_metrics(metrics, distribution, stats)

    group_by = None
    if group:
        try:
            group_by = GroupProperty.from_value(group)
        except ValueError:
            raise ValueError(f"Unknown group: {group}")

    return MetricResponse(
        metricsCollection=MetricsCollection(
            metrics=parsed_metrics,
            group_by=group_by,
        )
    )


def build_filter_response(filter_string: str | None) -> FilterResponse:
    if filter_string:
        logical_filter = parse_filter_string(filter_string)
        return FilterResponse(logicalFilter=logical_filter)
    else:
        return FilterResponse(logicalFilter=None)


def parse_cli_to_metric_response(cli_command: str) -> MetricCalculatorResponse:
    args = parse_cli_command(cli_command)

    metric_response = build_metric_response(metrics=args["metrics"], distribution=args["distribution"], stats=args["stats"], group=args["group"])

    filter_response = build_filter_response(args["filter"])

    return MetricCalculatorResponse(
        MetricResponse=metric_response,
        FilterResponse=filter_response,
    )


if __name__ == "__main__":
    from pprint import pprint

    cli_input = " ".join(sys.argv[1:]).strip()

    if not cli_input:
        print("Usage:")
        print("  python cli_token_parser.py /query AGE DTN -filter 'AND(AGE>=50, SEX==MALE)' -stats -distribution DTN:10:0:120 -group FIRST_CONTACT_PLACE")
        sys.exit(1)

    try:
        response = parse_cli_to_metric_response(cli_input)
        print("\n✅ Parsed MetricCalculatorResponse:\n")
        pprint(response.model_dump(mode="json"), width=120)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
