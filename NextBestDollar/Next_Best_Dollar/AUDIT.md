# Next Best Dollar — first product iteration

## Existing foundation
Python/Tkinter desktop app with local SQLite storage. Five main pages: Dashboard, Profile, Goals, Plan and Research. Profile includes personal, behavioral and financial questionnaires. Plan includes monthly allocation, account projections and a life/debt timeline. Financial records include categorized monthly income/spending, cash accounts, emergency savings, debts with APR/minimums, investments and benefits. No external dependencies are required beyond Python with Tk support.

## Priority gaps and changes
1. **No central next-dollar guidance.** Added a deterministic recommendation module and dashboard card with an explanation and direct editing action. Uses current saved facts, rejects invalid recommendation inputs, supports legacy debt records, and never changes balances.
2. **Surplus appeared automatically investable.** Renamed it “Left to assign” and clarified upcoming savings, debt and goals still need consideration.
3. **First-run direction was weak.** Added a three-step welcome and direct entry into the existing financial questionnaire. Personal/behavioral completion is not required for the first recommendation.
4. **Dashboard could exceed window height.** Added a scrolling container and two-column metric layout. Added a readable spending category breakdown alongside the existing chart.
5. **Main navigation buttons required a mouse.** Enabled Tab focus, Enter and Space activation with a focus indicator.

## Recommendation policy and limits
After checking data and cash flow: illustrate a one-month designated emergency buffer, then extra payments on highest-APR debt at or above 8%, then a three-month reserve, then ask the user to review goals and benefits. Amounts are limited to monthly surplus and the relevant gap; debt suggestions exclude minimums already budgeted. These targets and the cutoff are product assumptions, not universal financial rules. Existing allocation scenarios remain independently editable and are not automatically populated from recommendations.

The engine does not model overdue bills, loan forgiveness, promotional rates, payoff interest, payroll matching formulas, taxes, or a complete priority ordering for every household. It does not recommend securities. Users should review upcoming bills, employer benefits and special loan terms before acting. Goals are user-selected rather than automatically ranked.

Background principles: [CFPB emergency savings guide](https://www.consumerfinance.gov/an-essential-guide-to-building-an-emergency-fund/) and [CFPB debt action plan](https://files.consumerfinance.gov/f/documents/cfpb_your-money-your-goals_debt-action-plan_tool_2018-11.pdf). The numeric assumptions above are not attributed to these sources.

## Validation
12 automated tests pass: empty setup, zero/negative cash flow, reserve caps, checking vs. emergency cash, debt minimum accounting, highest-rate selection, payoff cap, larger reserves, malformed numbers, legacy debts, no state mutation and existing allocation cash conservation. All Python modules compile.

A native GUI smoke launch was attempted with an isolated temporary database. The local GUI process exited with code 134 before opening a window and without an error message; visual layout and click-through behavior remain unverified in this environment. No claim of full end-to-end validation is made.

## Next priorities
- Verify the native interface on macOS at minimum and standard window sizes, including keyboard navigation and all financial save/edit flows.
- Make reserve targets and debt-priority preferences editable in a dedicated recommendation settings flow.
- Collect irregular bills, urgent obligations and income variability explicitly.
- Audit existing IRA-year rules and projection assumptions before extending financial guidance.
- Improve storage error handling, backup/recovery and encryption before broader distribution. Current database is unencrypted and resides beside the app; never commit or share it.
- Consider a preview-and-confirm CSV import with duplicate handling. Bank linking remains out of scope.

## Running and preserving data
Open Launch_Mac.command or run `python3 main.py` from this folder with a Tk-enabled Python installation. Existing README.txt describes the earlier allocation/timeline features.

This package contains no personal database. Back up an existing next_best_dollar.db before replacing app code; preserve it beside main.py. No schema changes were introduced. Changes are local to this package and have not been pushed to GitHub.

Run checks with `python3 -m unittest discover -s tests -v`.
