#!/usr/bin/env python

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"

TOTAL_INDEX = 0
MONTH_INDEX = 1

ParsedDate = tuple[int, int, int]
TransactionValue = float | str | ParsedDate
TransactionRecord = dict[str, TransactionValue]
CategorySums = dict[str, float]
CommandParts = list[str]

ZERO_AMOUNT = float(0)
DATE_PARTS_COUNT = 3
DATE_DAY_TEXT_LENGTH = 2
DATE_MONTH_TEXT_LENGTH = 2
DATE_YEAR_TEXT_LENGTH = 4
MIN_MONTH_NUMBER = 1
MAX_MONTH_NUMBER = 12
CATEGORY_PARTS_COUNT = 2
INCOME_COMMAND_PARTS_COUNT = 3
COST_CATEGORIES_COMMAND_PARTS_COUNT = 2
COST_COMMAND_MIN_PARTS_COUNT = 4
STATS_COMMAND_PARTS_COUNT = 2

DAYS_IN_MONTH_TEMPLATE = (
    31,
    28,
    31,
    30,
    31,
    30,
    31,
    31,
    30,
    31,
    30,
    31,
)


EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
}


financial_transactions_storage: list[TransactionRecord] = []


def is_leap_year(year: int) -> bool:
    """
    Для заданного года определяет: високосный (True) или невисокосный (False).

    :param int year: Проверяемый год
    :return: Значение високосности.
    :rtype: bool
    """
    return year % 400 == 0 or (year % 4 == 0 and year % 100 != 0)


def split_date_parts(maybe_dt: str) -> tuple[str, str, str] | None:
    parts = maybe_dt.split("-")
    if len(parts) != DATE_PARTS_COUNT:
        return None
    return parts[0], parts[1], parts[2]


def has_valid_date_lengths(parts: tuple[str, str, str]) -> bool:
    day_length = len(parts[0]) == DATE_DAY_TEXT_LENGTH
    month_length = len(parts[1]) == DATE_MONTH_TEXT_LENGTH
    year_length = len(parts[2]) == DATE_YEAR_TEXT_LENGTH
    return day_length and month_length and year_length


def has_only_digits(parts: tuple[str, str, str]) -> bool:
    return all(part.isdigit() for part in parts)


def build_date(parts: tuple[str, str, str]) -> ParsedDate:
    day = int(parts[0])
    month = int(parts[1])
    year = int(parts[2])
    return day, month, year


def get_days_in_month(year: int) -> list[int]:
    days_in_month = list(DAYS_IN_MONTH_TEMPLATE)
    if is_leap_year(year):
        days_in_month[1] = 29
    return days_in_month


def is_valid_date(date_value: ParsedDate) -> bool:
    day, month, year = date_value
    if month < MIN_MONTH_NUMBER or month > MAX_MONTH_NUMBER:
        return False
    days_in_month = get_days_in_month(year)
    return 1 <= day <= days_in_month[month - 1]


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    """
    Парсит дату формата DD-MM-YYYY из строки.

    :param str maybe_dt: Проверяемая строка
    :return: typle формата (день, месяц, год) или None, если дата неправильная.
    :rtype: tuple[int, int, int] | None
    """
    parsed_date = None
    parts = split_date_parts(maybe_dt)
    if parts is not None and has_valid_date_lengths(parts) and has_only_digits(parts):
        candidate_date = build_date(parts)
        if is_valid_date(candidate_date):
            parsed_date = candidate_date
    return parsed_date


def has_valid_amount_separators(amount_string: str) -> bool:
    return amount_string.count(".") <= 1


def normalize_amount_string(amount_string: str) -> str:
    normalized_string = amount_string.replace(",", ".")
    return normalized_string.removeprefix("+")


def is_valid_amount_text(amount_text: str) -> bool:
    if amount_text == "" or amount_text.endswith("."):
        return False
    digits_text = amount_text.replace(".", "")
    return digits_text.isdigit()


def extract_amount(amount_string: str) -> float | None:
    if amount_string == "":
        return None

    normalized_string = normalize_amount_string(amount_string)
    if not has_valid_amount_separators(normalized_string):
        return None

    unsigned_string = normalized_string.removeprefix("-")
    if not is_valid_amount_text(unsigned_string):
        return None

    return float(normalized_string)


def split_category_name(category_name: str) -> tuple[str, str] | None:
    parts = category_name.split("::")
    if len(parts) != CATEGORY_PARTS_COUNT:
        return None
    return parts[0], parts[1]


def is_existing_category(category_name: str) -> bool:
    parts = split_category_name(category_name)
    if parts is None:
        return False
    common_category, target_category = parts
    if common_category not in EXPENSE_CATEGORIES:
        return False
    return target_category in EXPENSE_CATEGORIES[common_category]


def extract_target_category(category_name: str) -> str:
    parts = split_category_name(category_name)
    if parts is None:
        return category_name
    return parts[1]


def format_detail_amount(value: float) -> str:
    result = f"{value:.10f}".rstrip("0").rstrip(".")
    return result or "0"


def to_sortable_date(date_value: ParsedDate) -> tuple[int, int, int]:
    return date_value[2], date_value[1], date_value[0]


def is_date_on_or_before(date_value: ParsedDate, target_date: ParsedDate) -> bool:
    return to_sortable_date(date_value) <= to_sortable_date(target_date)


def is_same_month(date_value: ParsedDate, target_date: ParsedDate) -> bool:
    same_month = date_value[1] == target_date[1]
    same_year = date_value[2] == target_date[2]
    return same_month and same_year

def get_record_amount(record: TransactionRecord) -> float | None:
    raw_amount = record.get("amount")
    if isinstance(raw_amount, int | float):
        return float(raw_amount)
    return None


def get_record_date(record: TransactionRecord) -> ParsedDate | None:
    raw_date = record.get("date")
    if not isinstance(raw_date, tuple):
        return None
    if not is_integer_date_tuple(raw_date):
        return None
    return raw_date[0], raw_date[1], raw_date[2]


def get_record_category(record: TransactionRecord) -> str | None:
    raw_category = record.get("category")
    if isinstance(raw_category, str):
        return raw_category
    return None


def is_cost_record(record: TransactionRecord) -> bool:
    return get_record_category(record) is not None


def is_integer_date_tuple(raw_date: tuple[object, ...]) -> bool:
    if len(raw_date) != DATE_PARTS_COUNT:
        return False
    return all(isinstance(date_part, int) for date_part in raw_date)


def get_record_amount_and_date(record: TransactionRecord) -> tuple[float, ParsedDate] | None:
    amount = get_record_amount(record)
    date_value = get_record_date(record)
    if amount is None or date_value is None:
        return None
    return amount, date_value


def update_period_totals(
    totals: list[float],
    amount: float,
    date_value: ParsedDate,
    stats_date: ParsedDate,
) -> bool:
    if not is_date_on_or_before(date_value, stats_date):
        return False
    totals[TOTAL_INDEX] += amount
    if not is_same_month(date_value, stats_date):
        return False
    totals[MONTH_INDEX] += amount
    return True


def update_income_totals(totals: list[float], record: TransactionRecord, stats_date: ParsedDate) -> None:
    if is_cost_record(record):
        return
    amount_and_date = get_record_amount_and_date(record)
    if amount_and_date is None:
        return
    amount, date_value = amount_and_date
    update_period_totals(totals, amount, date_value, stats_date)


def calculate_income_totals(stats_date: ParsedDate) -> tuple[float, float]:
    totals = [ZERO_AMOUNT, ZERO_AMOUNT]
    for record in financial_transactions_storage:
        update_income_totals(totals, record, stats_date)
    return totals[TOTAL_INDEX], totals[MONTH_INDEX]


def add_category_sum(category_sums: CategorySums, category_name: str, amount: float) -> None:
    current_sum = category_sums.get(category_name, ZERO_AMOUNT)
    category_sums[category_name] = current_sum + amount


def update_cost_totals(
    totals: list[float],
    category_sums: CategorySums,
    record: TransactionRecord,
    stats_date: ParsedDate,
) -> None:
    category_name = get_record_category(record)
    if category_name is None:
        return
    amount_and_date = get_record_amount_and_date(record)
    if amount_and_date is None:
        return
    amount, date_value = amount_and_date
    if update_period_totals(totals, amount, date_value, stats_date):
        add_category_sum(category_sums, extract_target_category(category_name), amount)


def calculate_cost_totals(stats_date: ParsedDate) -> tuple[float, float, CategorySums]:
    totals = [ZERO_AMOUNT, ZERO_AMOUNT]
    category_sums: CategorySums = {}
    for record in financial_transactions_storage:
        update_cost_totals(totals, category_sums, record, stats_date)
    return totals[TOTAL_INDEX], totals[MONTH_INDEX], category_sums


def format_stats_date(stats_date: ParsedDate) -> str:
    day = stats_date[0]
    month = stats_date[1]
    year = stats_date[2]
    return f"{day:02d}-{month:02d}-{year:04d}"


def build_month_result(month_income: float, month_cost: float) -> str:
    month_delta = month_income - month_cost
    if month_delta < 0:
        loss_amount = abs(month_delta)
        return f"This month, the loss amounted to {loss_amount:.2f} rubles."
    return f"This month, the profit amounted to {month_delta:.2f} rubles."


def build_category_lines(category_sums: CategorySums) -> list[str]:
    lines = ["", "Details (category: amount):"]
    sorted_categories = sorted(category_sums)
    for index, category_name in enumerate(sorted_categories, start=1):
        lines.append(f"{index}. {category_name}: {format_detail_amount(category_sums[category_name])}")
    return lines


def build_stats_lines(
    report_date: ParsedDate,
    income_totals: tuple[float, float],
    cost_totals: tuple[float, float, CategorySums],
) -> list[str]:
    total_capital = income_totals[0] - cost_totals[0]
    lines = [
        f"Your statistics as of {format_stats_date(report_date)}:",
        f"Total capital: {total_capital:.2f} rubles",
        build_month_result(income_totals[1], cost_totals[1]),
        f"Income: {income_totals[1]:.2f} rubles",
        f"Expenses: {cost_totals[1]:.2f} rubles",
    ]
    lines.extend(build_category_lines(cost_totals[2]))
    return lines


def render_stats(report_date: ParsedDate) -> str:
    income_totals = calculate_income_totals(report_date)
    cost_totals = calculate_cost_totals(report_date)
    return "\n".join(build_stats_lines(report_date, income_totals, cost_totals))


def income_handler(amount: float, income_date: str) -> str:
    financial_transactions_storage.append({})

    if amount <= 0:
        return NONPOSITIVE_VALUE_MSG

    parsed_date = extract_date(income_date)
    if parsed_date is None:
        return INCORRECT_DATE_MSG

    financial_transactions_storage[-1]["amount"] = amount
    financial_transactions_storage[-1]["date"] = parsed_date
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    financial_transactions_storage.append({})

    if not is_existing_category(category_name):
        return NOT_EXISTS_CATEGORY

    if amount <= 0:
        return NONPOSITIVE_VALUE_MSG

    parsed_date = extract_date(income_date)
    if parsed_date is None:
        return INCORRECT_DATE_MSG

    financial_transactions_storage[-1]["category"] = category_name
    financial_transactions_storage[-1]["amount"] = amount
    financial_transactions_storage[-1]["date"] = parsed_date
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    categories: list[str] = []
    for common_category, targets in EXPENSE_CATEGORIES.items():
        categories.extend(f"{common_category}::{target_category}" for target_category in targets)
    return "\n".join(categories)


def stats_handler(report_date: str) -> str:
    parsed_date = extract_date(report_date)
    if parsed_date is None:
        return INCORRECT_DATE_MSG
    return render_stats(parsed_date)


def process_income_command(parts: CommandParts) -> str:
    if len(parts) != INCOME_COMMAND_PARTS_COUNT:
        return UNKNOWN_COMMAND_MSG
    amount = extract_amount(parts[1])
    if amount is None or amount <= 0:
        return NONPOSITIVE_VALUE_MSG
    return income_handler(amount, parts[2])


def process_cost_command(parts: CommandParts) -> str:
    if len(parts) == COST_CATEGORIES_COMMAND_PARTS_COUNT and parts[1] == "categories":
        return cost_categories_handler()
    if len(parts) < COST_COMMAND_MIN_PARTS_COUNT:
        return UNKNOWN_COMMAND_MSG

    category_name = " ".join(parts[1:-2]).strip()
    amount = extract_amount(parts[-2])
    current_date = parts[-1]

    if category_name == "":
        return UNKNOWN_COMMAND_MSG
    if amount is None or amount <= 0:
        return NONPOSITIVE_VALUE_MSG
    return cost_handler(category_name, amount, current_date)


def process_stats_command(parts: CommandParts) -> str:
    if len(parts) != STATS_COMMAND_PARTS_COUNT:
        return UNKNOWN_COMMAND_MSG
    return stats_handler(parts[1])


def process_line(raw_line: str) -> str:
    line = raw_line.strip()
    if line == "":
        return UNKNOWN_COMMAND_MSG

    parts = line.split()
    command = parts[0]

    match command:
        case "income":
            return process_income_command(parts)
        case "cost":
            return process_cost_command(parts)
        case "stats":
            return process_stats_command(parts)
        case _:
            return UNKNOWN_COMMAND_MSG


def run_process() -> None:
    with open(0) as input_stream:
        for raw_line in input_stream:
            print(process_line(raw_line))


def main() -> None:
    run_process()


if __name__ == "__main__":
    main()
