def calculate_compound_interest(monthly_deposit, annual_rate, years):
    """Calculate the future value of monthly deposits with compound interest."""
    monthly_rate = annual_rate / 12 / 100
    total_months = years * 12
    future_value = 0

    for month in range(1, total_months + 1):
        future_value = (future_value + monthly_deposit) * (1 + monthly_rate)

    return future_value


print("Compound interest calculator test file loaded.")
