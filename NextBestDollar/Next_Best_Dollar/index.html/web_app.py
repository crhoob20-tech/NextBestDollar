"""NextBestDollar web transition, Python 3.11+.
Run: python -m streamlit run web_app.py
Deploy this file and requirements.txt together; no desktop or database imports.
Pure calculation functions below are verbatim snapshots of the existing desktop
sources. Keep these snapshots in sync when desktop calculation rules change.
Session memory is private per browser connection; JSON export/import restores it.
"""
import json
import math
from copy import deepcopy
from datetime import date

import pandas as pd
import altair as alt
import streamlit as st


# Verbatim from financial.py; source SHA256: 657bda201e2ba5101b70455b04af88af70dab0eb86c25218ccb0a3ab428eb4a8
CASH_TYPES = {"checking": "Checking", "savings": "Traditional savings", "hysa": "HYSA / money market", "other_cash": "Other liquid cash"}

INVESTMENT_TYPES = {"retirement_employer": "401(k) / 403(b)", "ira": "Traditional / Roth IRA", "brokerage": "Brokerage", "hsa": "HSA", "other_investments": "Other investments"}

def normalize_financial(saved):
    data = deepcopy(saved)
    for key in ("income", "spending", "accounts", "investments", "benefits"):
        data.setdefault(key, {})
    debts = data.get("debt", [])
    if isinstance(debts, dict):
        labels = {"credit_card": "Credit card", "student_loan": "Student loan", "auto_loan": "Auto loan", "personal_loan": "Personal loan", "mortgage": "Mortgage", "other_debt": "Other debt"}
        data["debt"] = [dict(item, type=labels.get(key, key), name=labels.get(key, key), provider="")
                        for key, item in debts.items() if isinstance(item, dict) and (item.get("balance", 0) or item.get("minimum_payment", 0))]
    else:
        data["debt"] = deepcopy(debts)
    if "account_entries" not in data:
        data["account_entries"] = []
        for group, types in (("accounts", CASH_TYPES), ("investments", INVESTMENT_TYPES)):
            for key, label in types.items():
                balance = data[group].get(key, 0)
                if balance:
                    data["account_entries"].append(dict(type=key, name=label, provider="", balance=balance))
    return data

def calculate_metrics(financial_data):
    income = financial_data["income"]
    spending = financial_data["spending"]
    accounts = financial_data["accounts"]
    debt = financial_data["debt"]
    investments = financial_data["investments"]
    benefits = financial_data["benefits"]

    monthly_income = (
        income.get("primary_take_home", 0)
        + income.get("other_recurring_income", 0)
        + income.get("variable_income", 0)
    )

    monthly_living_spending = sum(spending.values())

    monthly_debt_minimums = sum(
        item["minimum_payment"]
        for item in debt
    )

    monthly_total_outflow = (
        monthly_living_spending
        + monthly_debt_minimums
    )

    monthly_free_cash_flow = (
        monthly_income
        - monthly_total_outflow
    )

    liquid_cash = (
        accounts["checking"]
        + accounts["savings"]
        + accounts["hysa"]
        + accounts["other_cash"]
    )

    total_debt = sum(
        item["balance"]
        for item in debt
    )

    total_investments = sum(investments.values())

    net_financial_position = (
        liquid_cash
        + total_investments
        - total_debt
    )

    if monthly_total_outflow > 0:
        cash_months = liquid_cash / monthly_total_outflow
    else:
        cash_months = 0.0

    if monthly_total_outflow > 0:
        emergency_months = (
            accounts["emergency_fund"]
            / monthly_total_outflow
        )
    else:
        emergency_months = 0.0

    match_gap = max(
        0.0,
        benefits.get("employer_match", 0)
        - benefits.get("current_retirement_contribution", 0),
    )

    metrics = {
        "monthly_income": round(monthly_income, 2),
        "monthly_living_spending": round(monthly_living_spending, 2),
        "monthly_debt_minimums": round(monthly_debt_minimums, 2),
        "monthly_total_outflow": round(monthly_total_outflow, 2),
        "monthly_free_cash_flow": round(monthly_free_cash_flow, 2),
        "liquid_cash": round(liquid_cash, 2),
        "emergency_fund": round(accounts["emergency_fund"], 2),
        "cash_months": round(cash_months, 2),
        "emergency_fund_months": round(emergency_months, 2),
        "total_debt": round(total_debt, 2),
        "total_investments": round(total_investments, 2),
        "net_financial_position": round(net_financial_position, 2),
        "employer_match_gap_percent": round(match_gap, 2),
    }

    return metrics


# Verbatim from allocation.py; source SHA256: e715e748ccf250211822271274a6a8f70255b41e2bc490cd6ac620f4b3ce6a02
def allocate(income,expenses,loans,savings,roth,minimums=0):
    values=(income,expenses,loans,savings,roth,minimums)
    if not all(math.isfinite(x) and x>=0 for x in values):raise ValueError('Enter nonnegative, finite monthly amounts.')
    if loans<minimums:raise ValueError(f'Total loan/debt allocation must cover recorded minimums of ${minimums:,.2f}.')
    available=max(0,income-expenses)
    rows=[]
    for name,requested in [('Loans / debt',loans),('Savings',savings),('Roth IRA',roth)]:
        funded=min(available,requested);available-=funded
        rows.append((name,requested,funded))
    rows.append(('Brokerage investing',available,available))
    shortfall=max(0,expenses+loans+savings+roth-income)
    return dict(rows=rows,shortfall=shortfall,available_before_allocations=income-expenses,
                living_expenses_funded=min(income,expenses),unfunded_minimums=max(0,minimums-rows[0][2]))


# Verbatim from goals.py; source SHA256: d45bbd8f922da1a1ec86b4342500c2281a10c28415dda784c1a7f680ee9df4ba
TYPES = ['Pay off debt', 'Buy a home', 'Buy a car', 'Invest', 'Vacation', 'Children / family', 'Emergency fund', 'Other milestone']

def validate_goal(values):
    title = str(values.get('name', '')).strip()
    kind = values.get('type')
    if not title:
        raise ValueError('Give your goal a name.')
    if kind not in TYPES:
        raise ValueError('Select a goal type.')
    amounts = {}
    for key in ('target_amount', 'progress_amount'):
        raw = str(values.get(key, '')).strip().replace('$', '').replace(',', '')
        try:
            amount = float(raw or ('0' if key == 'progress_amount' else 'nan'))
        except ValueError:
            raise ValueError('Enter valid dollar amounts.')
        if not math.isfinite(amount) or amount < 0:
            raise ValueError('Amounts must be finite, nonnegative numbers.')
        amounts[key] = round(amount, 2)
    if amounts['target_amount'] <= 0:
        raise ValueError('The target amount must be greater than zero.')
    due = str(values.get('target_date', '')).strip()
    if due:
        try:
            date.fromisoformat(due)
        except ValueError:
            raise ValueError('Enter the date as YYYY-MM-DD, or leave it blank.')
    priority = values.get('priority', 'Medium')
    if priority not in ('High', 'Medium', 'Low'):
        raise ValueError('Choose High, Medium or Low priority.')
    return dict(name=title, type=kind, **amounts, target_date=due, priority=priority,
                notes=str(values.get('notes', '')).strip())

def goal_status(goal):
    target = goal.get('target_amount', 0)
    progress = goal.get('progress_amount', 0)
    remaining = max(0, target-progress)
    due = goal.get('target_date', '')
    if remaining == 0:
        return 'Complete'
    if due and date.fromisoformat(due) < date.today():
        return 'Target date passed'
    return 'In progress'


# Verbatim from forecasting.py; source SHA256: 6e173519949f9b509dc7faf5aef252cc169edb76867e10e99d0b1a08a363af00
def project(initial,monthly,years,annual,increase=0,employer=0):
    if not all(math.isfinite(x) for x in (initial,monthly,years,annual,increase,employer)):
        raise ValueError('Enter finite numbers.')
    if increase < -100 or increase > 100 or employer < 0 or initial<0 or monthly<0 or years<1 or years>60 or years!=int(years) or annual<=-100 or annual>100:
        raise ValueError('Use nonnegative balances, whole years from 1–60, and an annual return above -100% and at most 100%.')
    # Annual effective rate converted to its equivalent monthly rate.
    rate=(1+annual/100)**(1/12)-1
    balance=initial;rows=[];paid=initial
    for month in range(1,int(years)*12+1):
        contribution=(monthly+employer)*(1+increase/100)**((month-1)//12)
        balance=balance*(1+rate)+contribution
        paid+=contribution
        if month%12==0:
            rows.append((month//12,paid,balance-paid,balance))
    return rows


# Verbatim from storage.py; source SHA256: 24345f1bccbbe9012373a1472f2159e283012e027c38c13a2faa468a21781952
def default_state():
    return {
        "onboarding_complete": False,
        "personal_complete": False,
        "behavioral_complete": False,
        "financial_complete": False,

        "personal": {},
        "personal_scores": {},

        "behavioral": {},
        "behavior_scores": {},

        "financial": {},
        "financial_metrics": {},

        "goals": [],
        "next_best_actions": [],
    }

# Verbatim from suggestions.py; source SHA256: fdaf0cc2bc6ec65420dcbb19e65bb8db09a0933ddb2f98e797f3f1ea55c818d2
def suggested_goals(state):
    if not state.get('financial_complete'):
        return []
    f=normalize_financial(state.get('financial',{}))
    existing={g.get('type') for g in state.get('goals',[])}
    result=[]
    def add(kind,name,reason,target='',progress=0,priority='Medium'):
        if kind not in existing:
            result.append(dict(type=kind,name=name,reason=reason,target_amount=target,
                               progress_amount=progress,priority=priority,notes=''))
    debt=sum(d.get('balance',0) for d in f['debt'])
    if debt>0:
        add('Pay off debt','Build a debt payoff goal',f'You reported ${debt:,.2f} in debt. Review a payoff target and timeline alongside your required payments.',debt,priority='High')
    spending=sum(f['spending'].values())+sum(d.get('minimum_payment',0) for d in f['debt'])
    reserve=f['accounts'].get('emergency_fund',0)
    if spending>0 and reserve<spending:
        add('Emergency fund','Build a cash buffer',f'Your designated emergency savings (${reserve:,.2f}) is below one month of recorded outflows (${spending:,.2f}). Choose a reserve target that fits you.',progress=reserve)
    dependents=state.get('personal',{}).get('dependents',0)
    try: dependents=int(dependents)
    except (ValueError,TypeError): dependents=0
    if dependents>0:
        add('Children / family','Plan for family costs','You listed dependents. Consider a goal for care, education or another family expense.')
    if not result:
        add('Other milestone','Choose your next milestone','What would you like your money to make possible? Choose your own target and timeline.')
    return result


# Verbatim from onboarding.py; SHA256: 871b1ab754ba74febdc4ca7229588fbdcbb53731a0c0da734d1308d5709e86fd
def calculate_age(date_of_birth):
    today = date.today()

    years = today.year - date_of_birth.year

    if (today.month, today.day) < (
        date_of_birth.month,
        date_of_birth.day
    ):
        years -= 1

    return years

def calculate_personal_scores(personal):
    age = personal["age"]
    dependents = personal["dependents"]

    if age <= 25:
        time_horizon_capacity = 5.0
    elif age <= 35:
        time_horizon_capacity = 4.5
    elif age <= 45:
        time_horizon_capacity = 4.0
    elif age <= 55:
        time_horizon_capacity = 3.0
    elif age <= 65:
        time_horizon_capacity = 2.0
    else:
        time_horizon_capacity = 1.5

    income_stability_map = {
        "Very stable": 5.0,
        "Mostly stable": 4.0,
        "Somewhat variable": 3.0,
        "Highly variable": 2.0,
        "No current income": 1.0,
    }

    knowledge_map = {
        "Beginner": 1.0,
        "Basic": 2.0,
        "Intermediate": 3.5,
        "Advanced": 5.0,
    }

    if dependents == 0:
        household_flexibility = 5.0
    elif dependents == 1:
        household_flexibility = 4.0
    elif dependents == 2:
        household_flexibility = 3.0
    elif dependents == 3:
        household_flexibility = 2.0
    else:
        household_flexibility = 1.0

    return {
        "time_horizon_capacity": time_horizon_capacity,
        "income_stability": income_stability_map.get(
            personal["income_stability"],
            3.0
        ),
        "household_flexibility": household_flexibility,
        "financial_knowledge": knowledge_map.get(
            personal["financial_experience"],
            2.0
        ),
    }


# Verbatim from behavioral.py; SHA256: 6b3683206fca05cbd5fb10004fc86f8f5902e2007f3e19e700ae65dc0ca8d76f
BEHAVIORAL_QUESTIONS = [
    {
        "id": "discipline_01",
        "dimension": "discipline",
        "statement": (
            "If I set a financial target for the month, I usually stick to it "
            "even when something more enjoyable comes up."
        ),
        "reverse": False,
    },
    {
        "id": "discipline_02",
        "dimension": "discipline",
        "statement": (
            "I often start financial plans with good intentions but stop "
            "following them after a short period of time."
        ),
        "reverse": True,
    },

    {
        "id": "planning_01",
        "dimension": "planning",
        "statement": (
            "When I know a large expense is coming, I usually start preparing "
            "for it well before the payment is due."
        ),
        "reverse": False,
    },
    {
        "id": "planning_02",
        "dimension": "planning",
        "statement": (
            "I usually deal with financial obligations when they become urgent "
            "rather than planning for them ahead of time."
        ),
        "reverse": True,
    },

    {
        "id": "impulse_01",
        "dimension": "impulse_control",
        "statement": (
            "When I see something I really want, I often buy it first and "
            "figure out how it fits my finances afterward."
        ),
        "reverse": True,
    },
    {
        "id": "impulse_02",
        "dimension": "impulse_control",
        "statement": (
            "Before making an unplanned purchase, I usually give myself time "
            "to decide whether I still want it."
        ),
        "reverse": False,
    },

    {
        "id": "delay_01",
        "dimension": "delayed_gratification",
        "statement": (
            "I am comfortable delaying something I want now if doing so helps "
            "me reach a more important goal later."
        ),
        "reverse": False,
    },
    {
        "id": "delay_02",
        "dimension": "delayed_gratification",
        "statement": (
            "It is difficult for me to give up something enjoyable today for "
            "a financial benefit that may be years away."
        ),
        "reverse": True,
    },

    {
        "id": "loss_01",
        "dimension": "loss_tolerance",
        "statement": (
            "If a long-term investment fell significantly and my reason for "
            "owning it had not changed, I could avoid making a rushed decision."
        ),
        "reverse": False,
    },
    {
        "id": "loss_02",
        "dimension": "loss_tolerance",
        "statement": (
            "Seeing an investment lose money would make me want to reduce risk "
            "quickly, even if the money was intended for the long term."
        ),
        "reverse": True,
    },

    {
        "id": "uncertainty_01",
        "dimension": "uncertainty_tolerance",
        "statement": (
            "I can make an important financial decision without needing to feel "
            "completely certain about what will happen next."
        ),
        "reverse": False,
    },
    {
        "id": "uncertainty_02",
        "dimension": "uncertainty_tolerance",
        "statement": (
            "If a financial outcome is uncertain, I would usually rather avoid "
            "the decision than accept the possibility that it may not work out."
        ),
        "reverse": True,
    },
]

def calculate_behavior_scores(raw_answers):
    """
    Returns hidden 1.0-5.0 scores for each behavioral dimension.

    Raw answers are always the user's visible 1-5 selections.
    Reverse-scored items are transformed internally:
        1 -> 5
        2 -> 4
        3 -> 3
        4 -> 2
        5 -> 1
    """

    dimension_values = {}

    for question in BEHAVIORAL_QUESTIONS:
        raw_value = raw_answers[question["id"]]

        if question["reverse"]:
            scored_value = 6 - raw_value
        else:
            scored_value = raw_value

        dimension = question["dimension"]

        if dimension not in dimension_values:
            dimension_values[dimension] = []

        dimension_values[dimension].append(scored_value)

    scores = {
        dimension: round(sum(values) / len(values), 2)
        for dimension, values in dimension_values.items()
    }

    return scores


# Verbatim from occupation.py; SHA256: cb0ae32195844050967bf5b41702ec340e55ae267d977f2ee33ebf0c0e4e87dc
SECTORS=['Not specified','Private employer','Education / nonprofit','Federal government','State / local government','Self-employed / business owner','Not currently working']

PROMPTS={
 'Education / nonprofit':'Ask your employer whether you have a pension, 403(b), or 457(b). The plan depends on the employer, not just your job title.',
 'Federal government':'Check whether you have a Thrift Savings Plan (TSP) and a pension benefit.',
 'State / local government':'Check for a pension and a 457(b) or other employer-sponsored savings plan.',
 'Self-employed / business owner':'Business owners may establish a solo 401(k), SEP IRA or SIMPLE IRA, depending on business and employee circumstances. Confirm which you actually have.',
 'Private employer':'Check whether your employer offers a 401(k), pension, SIMPLE IRA or another retirement plan.',
}

def prompt(sector):return PROMPTS.get(sector,'You can add an existing retirement account even if you are not currently working.')


# Verbatim from profile_context.py; SHA256: c3b08f8a8b498bed10bc2674559c6e675c39943718943dc2da365016c8f962df
def active_context(status,student_work='No'):
    working=status in ('Full-time','Part-time','Self-employed') or (status=='Student' and student_work=='Yes')
    keys=set()
    if status=='Student':keys.update(('school_name','study_program','student_work'))
    if working:keys.update(('employer_name','occupation','work_sector','retirement_access','retirement_plan_name'))
    return keys


# Web adapter: validation, session-only persistence, and responsive controls.
MAX_MONEY = 1_000_000_000.0


def money(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{label}: enter a number.')
    if not 0 <= value <= MAX_MONEY or not math.isfinite(value):
        raise ValueError(f'{label}: use a finite amount between 0 and 1 billion.')
    return round(float(value), 2)


def clean_profile(raw):
    """Validate completely before committing; never trust uploaded metrics."""
    if not isinstance(raw, dict):
        raise ValueError('Profile must be a JSON object.')
    f = raw.get('financial', {})
    if not isinstance(f, dict):
        raise ValueError('Financial data must be an object.')
    f = deepcopy(f)
    for key in ('income', 'spending', 'accounts', 'investments', 'benefits'):
        group = f.setdefault(key, {})
        if not isinstance(group, dict):
            raise ValueError(f'{key} must be an object.')
        f[key] = {str(k): money(v, str(k)) for k, v in group.items()}
    for key in ('current_retirement_contribution', 'employer_match'):
        if f['benefits'].get(key, 0) > 100:
            raise ValueError('Employer benefit percentages must be between 0 and 100.')
    f = normalize_financial(f)
    for key in ('account_entries', 'debt'):
        if not isinstance(f[key], list) or len(f[key]) > 100:
            raise ValueError(f'{key} must be a list with at most 100 entries.')
        if any(not isinstance(row, dict) for row in f[key]):
            raise ValueError(f'Every {key} entry must be an object.')
    accounts = dict.fromkeys(CASH_TYPES, 0.0)
    investments = dict.fromkeys(INVESTMENT_TYPES, 0.0)
    for row in f['account_entries']:
        kind = row.get('type')
        if kind not in accounts and kind not in investments:
            raise ValueError('Select a supported account type.')
        row['name'] = row.get('name', '').strip() if isinstance(row.get('name'), str) else ''
        if not row['name']:
            raise ValueError('Name every account.')
        if not isinstance(row.get('provider', ''), str):
            raise ValueError('Account provider must be text.')
        row['balance'] = money(row.get('balance'), 'Account balance')
        group = accounts if kind in accounts else investments
        group[kind] += row['balance']
    emergency = money(f['accounts'].get('emergency_fund', 0), 'Emergency reserve')
    if emergency > sum(accounts.values()):
        raise ValueError('Emergency reserve cannot exceed your recorded cash balances.')
    accounts['emergency_fund'] = emergency
    f['accounts'], f['investments'] = accounts, investments
    for row in f['debt']:
        if not isinstance(row.get('name'), str) or not row['name'].strip():
            raise ValueError('Name every debt.')
        if not isinstance(row.get('provider', ''), str) or not isinstance(row.get('type', 'Other debt'), str):
            raise ValueError('Debt provider and type must be text.')
        for key in ('balance', 'minimum_payment', 'apr'):
            row[key] = money(row.get(key, 0), key)
        if row['apr'] > 100:
            raise ValueError('Debt APR must be between 0 and 100%.')
    goals = raw.get('goals', [])
    if not isinstance(goals, list) or len(goals) > 100:
        raise ValueError('Goals must be a list with at most 100 entries.')
    if any(not isinstance(g, dict) for g in goals):
        raise ValueError('Every goal must be an object.')
    state = default_state()
    state['financial'] = f
    state['financial_metrics'] = calculate_metrics(f)
    if any(abs(v) > MAX_MONEY for v in state['financial_metrics'].values()):
        raise ValueError('Combined profile totals must not exceed 1 billion.')
    state['goals'] = [validate_goal(g) for g in goals]
    for goal in state['goals']:
        money(goal['target_amount'], 'Goal target')
        money(goal['progress_amount'], 'Goal progress')
    for flag in ('personal_complete', 'behavioral_complete', 'financial_complete'):
        if not isinstance(raw.get(flag, False), bool):
            raise ValueError('Completion flags must be true or false.')
        state[flag] = raw.get(flag, False)
    if state['personal_complete']:
        state['personal'] = validate_personal(raw.get('personal'))
        state['personal_scores'] = calculate_personal_scores(state['personal'])
    if state['behavioral_complete']:
        answers = raw.get('behavioral')
        if not isinstance(answers, dict) or any(type(answers.get(q['id'])) is not int or answers[q['id']] not in range(1,6) for q in BEHAVIORAL_QUESTIONS):
            raise ValueError('Answer all 12 behavioral questions with a number from 1 to 5.')
        state['behavioral'] = {q['id']: answers[q['id']] for q in BEHAVIORAL_QUESTIONS}
        state['behavior_scores'] = calculate_behavior_scores(state['behavioral'])
    state['onboarding_complete'] = all(state[k] for k in ('personal_complete', 'behavioral_complete', 'financial_complete'))
    return state


def read_backup(data):
    if len(data) > 1_000_000:
        raise ValueError('Choose a profile smaller than 1 MB.')
    payload = json.loads(data)
    if not isinstance(payload, dict) or payload.get('format') != 'nextbestdollar-web' or payload.get('version') != 1:
        raise ValueError('Choose a NextBestDollar web profile backup (version 1).')
    return clean_profile(payload.get('profile'))


def export_backup(state):
    return json.dumps({'format': 'nextbestdollar-web', 'version': 1,
                       'profile': clean_profile(state)}, indent=2, allow_nan=False)


def amount(label, value=0.0, **kwargs):
    """Use whole-number controls for whole-dollar amounts, without .00 noise."""
    value = money(value, label)
    if value.is_integer():
        return st.number_input(label, min_value=0, max_value=int(MAX_MONEY),
                               value=int(value), step=1, format='%d', **kwargs)
    return st.number_input(label, min_value=0.0, max_value=MAX_MONEY,
                           value=value, step=0.01, format='%.2f', **kwargs)


def currency(value):
    return f'${float(value):,.2f}'


def goal_progress(goal):
    target = float(goal['target_amount'])
    progress = min(target, float(goal['progress_amount']))
    percent = 0 if target == 0 else round(progress / target * 100)
    return progress, target, min(100, percent)


def goal_progress_bar(goal):
    progress, target, percent = goal_progress(goal)
    st.markdown(
        f'<div class="goal-progress" role="progressbar" aria-valuenow="{percent}" aria-valuemin="0" aria-valuemax="100">'
        f'<div class="goal-progress-fill" style="width:{percent}%"></div></div>'
        f'<div class="goal-progress-label">{currency(progress)} saved <span>of {currency(target)}</span></div>',
        unsafe_allow_html=True,
    )


def money_bar_chart(metrics):
    data = pd.DataFrame(
        {'Category': ['Take-home income', 'Living expenses', 'Debt minimums'],
         'Amount': [metrics['monthly_income'], metrics['monthly_living_spending'], metrics['monthly_debt_minimums']]}
    )
    return (
        alt.Chart(data)
        .mark_bar(color='#176B58', cornerRadiusEnd=6, size=26)
        .encode(
            y=alt.Y('Category:N', sort=['Take-home income', 'Living expenses', 'Debt minimums'], title=None,
                    axis=alt.Axis(labelFontSize=13, labelPadding=12, ticks=False, domain=False)),
            x=alt.X('Amount:Q', title=None, axis=alt.Axis(format='$,.2f', grid=True, gridColor='#E1EAE4',
                    labelFontSize=12, domain=False, tickColor='#D2DED6')),
            tooltip=[alt.Tooltip('Category:N', title=''), alt.Tooltip('Amount:Q', title='Monthly amount', format='$,.2f')],
        )
        .properties(height=230, padding={'left': 8, 'right': 24, 'top': 18, 'bottom': 10})
        .configure_view(strokeOpacity=0, fill='#FFFFFF')
        .configure_axis(labelColor='#35534C', titleColor='#35534C')
    )


def forecast_chart(data):
    plot_data = data.reset_index().melt('Year', var_name='Series', value_name='Amount')
    return (
        alt.Chart(plot_data)
        .mark_line(point=alt.OverlayMarkDef(filled=True, fill='#FFFFFF', size=42), strokeWidth=3)
        .encode(
            x=alt.X('Year:Q', title='Year', axis=alt.Axis(tickMinStep=1, labelFontSize=12, titleFontSize=13,
                    grid=False, domainColor='#D2DED6', tickColor='#D2DED6')),
            y=alt.Y('Amount:Q', title='Value', axis=alt.Axis(format='$,.2f', labelFontSize=12, titleFontSize=13,
                    grid=True, gridColor='#E1EAE4', domain=False, tickColor='#D2DED6')),
            color=alt.Color('Series:N', title=None, scale=alt.Scale(domain=['Balance', 'Contributions'], range=['#176B58', '#7CA9E8']),
                            legend=alt.Legend(orient='bottom', labelFontSize=13, symbolStrokeWidth=3)),
            tooltip=[alt.Tooltip('Year:Q', format='.0f'), alt.Tooltip('Series:N', title=''), alt.Tooltip('Amount:Q', title='Value', format='$,.2f')],
        )
        .properties(height=360, padding={'left': 12, 'right': 28, 'top': 22, 'bottom': 18})
        .configure_view(strokeOpacity=0, fill='#FFFFFF')
        .configure_axis(labelColor='#35534C', titleColor='#35534C')
        .configure_legend(labelColor='#35534C')
    )


def render_planning(state, page):
    rev = st.session_state.revision
    if page == 'Goals':
        heading('Your goals', 'Build toward what matters.', 'Choose a milestone, track its progress, and connect each decision to a future you can see.')
        suggestions = suggested_goals(state)
        if suggestions:
            st.subheader('Suggested next goals')
            st.caption('These prompts come from the financial facts you saved. Review and customize any one before adding it.')
            for index, suggestion in enumerate(suggestions):
                with st.container(border=True):
                    left, right = st.columns([4, 1], vertical_alignment='center')
                    with left:
                        st.markdown(f"**{suggestion['name']}**")
                        st.write(suggestion['reason'])
                    with right:
                        if st.button('Customize', key=f'select_suggestion_{index}', width='stretch'):
                            st.session_state.goal_suggestion = suggestion
                            st.rerun()
        selected = st.session_state.get('goal_suggestion', {})
        st.subheader('Your milestones')
        if not state['goals']:
            st.info('Start with one milestone that matters to you. Give it a target and a date when you are ready.')
        for i, goal in enumerate(state['goals']):
            with st.container(border=True):
                top, status = st.columns([4, 1], vertical_alignment='center')
                with top:
                    st.subheader(goal['name'])
                    st.caption(f"{goal['type']} · {goal['priority']} priority" + (f" · Target {goal['target_date']}" if goal['target_date'] else ''))
                with status:
                    st.caption(goal_status(goal))
                goal_progress_bar(goal)
                with st.expander('Edit this goal'):
                    with st.form(f'goal_edit_{rev}_{i}'):
                        edited_name = st.text_input('Goal name', value=goal['name'])
                    edited_type = st.selectbox('Goal type', TYPES, index=TYPES.index(goal['type']))
                    edited_target = amount('Target amount', goal['target_amount'])
                    edited_progress = amount('Progress so far', goal['progress_amount'])
                    edited_due = st.date_input('Target date (optional)', value=date.fromisoformat(goal['target_date']) if goal['target_date'] else None)
                    edited_priority = st.selectbox('Priority', ['High','Medium','Low'], index=['High','Medium','Low'].index(goal['priority']))
                    edited_notes = st.text_area('Notes', value=goal['notes'])
                    save_edit = st.form_submit_button('Save goal changes', type='primary')
                    remove = st.form_submit_button('Remove goal')
                if save_edit or remove:
                    try:
                        if remove:
                            state['goals'].pop(i)
                        else:
                            state['goals'][i] = validate_goal(dict(name=edited_name, type=edited_type, target_amount=edited_target,
                                progress_amount=edited_progress, target_date=edited_due.isoformat() if edited_due else '',
                                priority=edited_priority, notes=edited_notes))
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        st.rerun()
        with st.expander('＋ Add a goal', expanded=bool(selected)):
            with st.form(f'goal_{rev}', clear_on_submit=True):
                st.write('Add a goal')
                name = st.text_input('Goal name', value=selected.get('name', ''))
                kind_default = selected.get('type', TYPES[0])
                kind = st.selectbox('Goal type', TYPES, index=TYPES.index(kind_default))
                target = amount('Target amount', selected.get('target_amount') or 0)
                progress = amount('Progress so far', selected.get('progress_amount', 0))
                due_value = st.date_input('Target date (optional)', value=None)
                due = due_value.isoformat() if due_value else ''
                priority_default = selected.get('priority', 'Medium')
                priority = st.selectbox('Priority', ['High', 'Medium', 'Low'], index=['High', 'Medium', 'Low'].index(priority_default))
                notes = st.text_area('Notes', value=selected.get('notes', ''))
                save_goal = st.form_submit_button('Save goal', type='primary')
            if save_goal:
                try:
                    goal = validate_goal(dict(name=name, type=kind, target_amount=target,
                        progress_amount=progress, target_date=due, priority=priority, notes=notes))
                    if len(state['goals']) >= 100:
                        raise ValueError('Maximum 100 goals per profile.')
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    state['goals'].append(goal)
                    st.session_state.pop('goal_suggestion', None)
                    st.rerun()
    else:
        if not state['financial_complete']:
            st.info('Save your financial profile first to build an allocation or forecast.')
            return
        metrics = state['financial_metrics']
        minimums = metrics['monthly_debt_minimums']
        if page == 'My allocation':
            st.subheader('Give each available dollar a job')
            st.metric('Monthly cash flow after living expenses and debt minimums', f"${metrics['monthly_free_cash_flow']:,.2f}")
            st.caption('Existing priority order: debt → savings → Roth IRA → brokerage. These are allocation targets, not transfers or a personalized investment recommendation.')
            for suggestion in suggested_goals(state):
                st.info(suggestion['reason'])
            loans = amount('Total debt payment INCLUDING minimums', minimums, key=f'loans_{rev}')
            savings = amount('Monthly savings target', key=f'savings_{rev}')
            confirmed = st.checkbox('I have independently verified my Roth eligibility and remaining contribution room', key=f'roth_ok_{rev}')
            roth = 0.0
            if confirmed:
                room = amount('Verified remaining Roth room for this tax year', key=f'roth_room_{rev}')
                months = st.slider('Months to fund this tax-year contribution', 1, 12, 12, key=f'roth_months_{rev}')
                roth = math.floor(room / months * 100) / 100
                st.caption(f'Monthly Roth target: ${roth:,.2f}. Stop after the selected months; recheck eligibility and limits each tax year.')
            try:
                result = allocate(metrics['monthly_income'], metrics['monthly_living_spending'], loans, savings, roth, minimums)
            except ValueError as exc:
                st.error(str(exc))
                return
            if result['shortfall']:
                st.warning(f"Requested plan exceeds income by ${result['shortfall']:,.2f}/month. Later priorities receive less funding.")
            if result['unfunded_minimums']:
                st.error(f"Debt minimums are underfunded by ${result['unfunded_minimums']:,.2f}/month.")
            for name, requested, funded in result['rows']:
                st.metric(name, f'${funded:,.2f}/month')
                if funded < requested:
                    st.caption(f'Requested: ${requested:,.2f}')
            st.caption('Allocation and forecast controls persist during this session. Profile downloads contain financial inputs and goals, not these exploratory scenarios.')
        else:
            st.subheader('Explore a growth scenario')
            st.caption("See what today's contributions could become. This scenario models one account with contributions at the end of each month.")
            initial = amount('Starting balance', metrics['total_investments'], key=f'initial_{rev}')
            monthly = amount('Monthly contribution', 0, key=f'monthly_{rev}')
            if monthly > max(0, metrics['monthly_free_cash_flow']):
                st.warning('This contribution exceeds your recorded monthly surplus.')
            years = st.slider('Years', 1, 60, 10, key=f'years_{rev}')
            rate = st.number_input('Assumed annual return (%)', min_value=-99.0, max_value=100.0, value=0.0, key=f'rate_{rev}')
            increase = st.number_input('Annual contribution change (%)', min_value=-100.0, max_value=100.0, value=0.0, key=f'increase_{rev}')
            rows = project(initial, monthly, years, rate, increase)
            df = pd.DataFrame([(0, initial, 0, initial)] + rows,
                              columns=['Year', 'Contributions', 'Growth', 'Balance']).set_index('Year')
            with st.container(border=True):
                st.altair_chart(forecast_chart(df[['Balance', 'Contributions']]), width='stretch')
            st.metric('Illustrative ending balance', currency(rows[-1][3]))
            st.caption('Returns are assumptions, not guarantees. Taxes, fees, inflation, withdrawals, and changing contribution limits are not modeled. Employer contributions are excluded.')
            st.download_button('Download forecast CSV', df.to_csv(), 'nextbestdollar-forecast.csv', 'text/csv')


PERSONAL_CHOICES = {
    'employment_status': ('What are you doing currently?', ['Full-time', 'Part-time', 'Self-employed', 'Student', 'Not currently employed', 'Retired']),
    'income_stability': ('How stable is your income?', ['Very stable', 'Mostly stable', 'Somewhat variable', 'Highly variable', 'No current income']),
    'marital_status': ('Relationship / marital status', ['Single', 'In a relationship', 'Engaged', 'Married', 'Separated / divorced', 'Widowed']),
    'housing_status': ('Current housing situation', ['Living with family', 'Renting', 'Own with mortgage', 'Own without mortgage', 'Other']),
    'finance_management': ('How do you currently manage your finances?', ['Individually', 'Jointly with a partner', 'Mostly individually', 'Mostly handled by someone else']),
    'financial_experience': ('How would you describe your financial knowledge?', ['Beginner', 'Basic', 'Intermediate', 'Advanced']),
}
CONTEXT_KEYS = ('school_name', 'study_program', 'student_work', 'employer_name', 'occupation', 'work_sector', 'retirement_access', 'retirement_plan_name')


def validate_personal(raw):
    if not isinstance(raw, dict):
        raise ValueError('Personal facts must be an object.')
    p = deepcopy(raw)
    for key in ('first_name', 'last_name'):
        if not isinstance(p.get(key), str) or not p[key].strip():
            raise ValueError('Please enter your first and last name.')
        p[key] = p[key].strip()
    try:
        dob = date.fromisoformat(p['date_of_birth'])
        p['age'] = calculate_age(dob)
    except (ValueError, KeyError, TypeError):
        raise ValueError('Please select your date of birth.')
    if not 16 <= p['age'] <= 100:
        raise ValueError('Date of birth must correspond to an age between 16 and 100.')
    for key, (label, options) in PERSONAL_CHOICES.items():
        if p.get(key) not in options:
            raise ValueError(f'Please answer: {label}')
    if type(p.get('dependents')) is not int or not 0 <= p['dependents'] <= 20:
        raise ValueError('Select your number of dependents, from 0 to 20.')
    active = active_context(p['employment_status'], p.get('student_work', 'No'))
    for key in CONTEXT_KEYS:
        if key not in active:
            p[key] = ''
        elif not isinstance(p.get(key, ''), str):
            raise ValueError(f'Invalid value for {key}.')
    if p['employment_status'] == 'Student' and p.get('student_work') not in ('Yes', 'No'):
        raise ValueError('Please select whether you are also working.')
    if 'occupation' in active:
        if p.get('work_sector') not in SECTORS or p.get('retirement_access') not in ('Yes', 'No', 'Not sure'):
            raise ValueError('Please check your work type and retirement plan answers.')
    if p.get('retirement_access') != 'Yes':
        p['retirement_plan_name'] = ''
    return p


def go(page):
    st.session_state.page = page
    st.rerun()


def heading(kicker, title, description):
    st.caption(kicker.upper())
    st.title(title)
    st.write(description)


def render_personal(state):
    heading('01 / Your foundation', 'A plan that starts with you.',
            'Tell us about your current situation. These answers provide context for future financial decisions.')
    p = state.get('personal', {})
    rev = st.session_state.revision
    def text_field(key, label):
        return st.text_input(label, value=p.get(key, ''), key=f'personal_{rev}_{key}')
    def choice(key, label, options, default=None):
        value = p.get(key, default)
        return st.selectbox(label, options, index=options.index(value) if value in options else None, key=f'personal_{rev}_{key}', placeholder='Choose an answer')
    draft = {}
    with st.container(border=True):
        st.subheader('The basics')
        a, b = st.columns(2)
        with a: draft['first_name'] = text_field('first_name', 'First name')
        with b: draft['last_name'] = text_field('last_name', 'Last name')
        dob = st.date_input('Date of birth', value=date.fromisoformat(p['date_of_birth']) if p.get('date_of_birth') else None,
            min_value=date(date.today().year-101, 1, 1), max_value=date.today(), key=f'personal_{rev}_dob')
        draft['date_of_birth'] = dob.isoformat() if dob else ''
        draft['employment_status'] = choice('employment_status', *PERSONAL_CHOICES['employment_status'])
        if draft['employment_status'] == 'Student':
            draft['school_name'] = text_field('school_name', 'School / university (optional)')
            draft['study_program'] = text_field('study_program', 'Program / field of study (optional)')
            draft['student_work'] = choice('student_work', 'Are you also working?', ['No', 'Yes'], 'No')
        working = 'occupation' in active_context(draft['employment_status'], draft.get('student_work', 'No'))
        if working:
            draft['employer_name'] = text_field('employer_name', 'Employer / business name (optional)')
            draft['occupation'] = text_field('occupation', 'Occupation / job title (optional)')
            draft['work_sector'] = choice('work_sector', 'Employer / work type', SECTORS, 'Not specified')
            st.caption(prompt(draft['work_sector']))
            draft['retirement_access'] = choice('retirement_access', 'Do you have a workplace or business retirement savings plan?', ['Not sure', 'Yes', 'No'], 'Not sure')
            if draft['retirement_access'] == 'Yes':
                draft['retirement_plan_name'] = text_field('retirement_plan_name', 'Plan name / type, if known (optional)')
        draft['income_stability'] = choice('income_stability', *PERSONAL_CHOICES['income_stability'])
    with st.container(border=True):
        st.subheader('Your household & experience')
        draft['marital_status'] = choice('marital_status', *PERSONAL_CHOICES['marital_status'])
        draft['dependents'] = choice('dependents', 'Number of dependents', list(range(21)))
        for key in ('housing_status', 'finance_management', 'financial_experience'):
            draft[key] = choice(key, *PERSONAL_CHOICES[key])
    st.caption('Your answers are kept in this session when you save. You can revisit them from the profile menu.')
    if st.button('Save & continue to money habits', type='primary', width='stretch'):
        try:
            personal = validate_personal(draft)
            updated = deepcopy(state)
            updated.update(personal=personal, personal_complete=True)
            st.session_state.profile = clean_profile(updated)
        except ValueError as exc:
            st.error(str(exc))
        else:
            go('Money habits')


def render_behavioral(state):
    heading('02 / Money habits', 'Understand your money mindset.',
            'For each statement, choose how likely it is to describe what you would realistically do.')
    st.caption('1 = Least likely · 5 = Most likely. There are no right answers. Your responses are saved with your profile; they do not change allocation amounts in this version.')
    answers = {}
    rev = st.session_state.revision
    for i, question in enumerate(BEHAVIORAL_QUESTIONS, 1):
        with st.container(border=True):
            st.caption(f'QUESTION {i:02d} OF 12')
            value = state.get('behavioral', {}).get(question['id'])
            answers[question['id']] = st.radio(question['statement'], list(range(1,6)),
                index=value-1 if value else None, horizontal=True, key=f'behavior_{rev}_{question["id"]}')
    answered = sum(v is not None for v in answers.values())
    st.progress(answered / 12, text=f'{answered} of 12 answered')
    a, b = st.columns(2)
    with a:
        if st.button('Back to personal facts', width='stretch'): go('Personal facts')
    with b:
        if st.button('Save & continue', type='primary', width='stretch'):
            if answered != 12:
                st.error('Please answer all 12 statements before continuing.')
            else:
                draft = deepcopy(state)
                draft.update(behavioral=answers, behavioral_complete=True)
                st.session_state.profile = clean_profile(draft)
                go('Financial facts')


def render_overview(state):
    import html
    if st.session_state.pop('financial_just_saved', False):
        st.success('Financial profile saved. Your plan is ready.' if state['onboarding_complete'] else 'Financial facts saved. Complete the remaining profile sections to finish onboarding.')
    name = html.escape(state.get('personal', {}).get('first_name', ''))
    st.markdown(f'''<div class="nbd-hero"><div class="nbd-eyebrow">YOUR MONEY, MOVING FORWARD</div>
        <h1>Your next chapter starts<br>with your next dollar.</h1>
        <p>{'Welcome back, '+name+'. ' if name else ''}Understand where you stand. Give your goals a plan. See what your decisions can make possible.</p></div>''', unsafe_allow_html=True)
    if not state['onboarding_complete']:
        st.info('Finish your profile to bring your full plan together.')
        target = 'Personal facts' if not state['personal_complete'] else 'Money habits' if not state['behavioral_complete'] else 'Financial facts'
        if st.button('Continue your profile', type='primary'): go(target)
        if not state['financial_complete']: return
    m = state['financial_metrics']
    cols = st.columns(3)
    for col, title, value, caption in zip(cols,
        ['Monthly breathing room', 'Net financial position', 'Emergency reserve'],
        [m['monthly_free_cash_flow'], m['net_financial_position'], m['emergency_fund']],
        ['After living costs and debt minimums', 'Cash + investments − recorded debt', 'Included in your cash balances']):
        with col:
            with st.container(border=True):
                st.metric(title, f'${value:,.0f}')
                st.caption(caption)
    st.subheader('Your next best moves')
    st.caption('Prompts based on the financial facts you saved. You choose the targets and priorities.')
    if m['monthly_free_cash_flow'] < 0:
        st.warning(f"Your outflows exceed income by ${abs(m['monthly_free_cash_flow']):,.2f} per month. Review your cash flow before adding new contributions.")
    for index, suggestion in enumerate(suggested_goals(state)):
        with st.container(border=True):
            st.markdown(f"**{suggestion['name']}**")
            st.write(suggestion['reason'])
            if st.button('Explore in goals →', key=f'suggestion_{index}'): go('Goals')
    left, right = st.columns([1,1])
    with left:
        with st.container(border=True):
            st.subheader('Your monthly picture')
            st.bar_chart(pd.DataFrame({'Monthly amount': [m['monthly_income'], m['monthly_living_spending'], m['monthly_debt_minimums']]}, index=['Take-home income','Living expenses','Debt minimums']), color='#176B58', horizontal=True)
            st.caption('A snapshot of your inputs, not a transaction history.')
    with right:
        with st.container(border=True):
            st.subheader('Goals worth moving toward')
            if not state['goals']:
                st.write('A first home. A debt-free date. More room to choose. Start with something that matters to you.')
            for goal in state['goals'][:3]:
                st.write(goal['name'])
                st.progress(min(1.0, goal['progress_amount']/goal['target_amount']))
                st.caption(f"${goal['progress_amount']:,.0f} of ${goal['target_amount']:,.0f}")
            if st.button('Open your goals', width='stretch'): go('Goals')
    with st.container(border=True):
        st.subheader('Make tomorrow more tangible.')
        st.write('Explore how a monthly contribution and time can change the future. Every forecast makes its assumptions visible.')
        if st.button('Explore your future →', type='primary'): go('Forecast')


STYLE = '''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root{--nbd-ink:#122D2A;--nbd-muted:#596C66;--nbd-green:#176B58}
.stApp{--text-color:#122D2A;--background-color:#F5F7F3;--secondary-background-color:#FFFFFF;--primary-color:#176B58;background:#F5F7F3;color:var(--nbd-ink);font-family:'DM Sans',sans-serif}
h1,h2,h3{font-family:'Manrope',sans-serif!important;letter-spacing:-.035em;color:var(--nbd-ink)}
h1{font-weight:800!important}p,label,span{font-family:'DM Sans',sans-serif}
[data-testid="stSidebar"]{background:#112F2A;color:#F1F6F1;border-right:0}
[data-testid="stSidebar"] *{color:#F1F6F1}
[data-testid="stSidebar"] button{background:#20483F;border:1px solid #3D6056;border-radius:12px}
[data-testid="stSidebar"] button:hover{background:#315E50;border-color:#BFE6AC}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:#BDD0C6}
[data-testid="stMainBlockContainer"]{max-width:1120px;padding-top:2rem;padding-bottom:4rem}
[data-testid="stVerticalBlockBorderWrapper"]>div{border-radius:18px!important}
[data-testid="stForm"], [data-testid="stExpander"]{background:#fff;border-radius:18px;border-color:#DCE5DF}
[data-testid="stMetricValue"]{font-family:'Manrope',sans-serif;font-weight:800;color:#176B58}
[data-testid="stBaseButton-primary"]{background:#176B58;border:1px solid #176B58;color:white;border-radius:12px;min-height:46px}
[data-testid="stBaseButton-secondary"]{border-radius:12px;min-height:42px;border-color:#D3DED6}
[data-testid="stMain"] p,[data-testid="stMain"] label{color:#122D2A}
[data-testid="stMain"] [data-testid="stCaptionContainer"] p{color:#596C66}
[data-testid="stMain"] input,[data-testid="stMain"] textarea,[data-baseweb="select"]>div,[data-baseweb="input"], [data-baseweb="base-input"]{color:#122D2A!important;background:#FFFFFF!important;border-color:#CBD8D0!important}
[data-baseweb="select"] span,[data-baseweb="select"] input{color:#122D2A!important}
[data-baseweb="popover"],[data-baseweb="menu"],[role="listbox"],[role="option"]{background:#FFFFFF!important;color:#122D2A!important}
[data-testid="stMain"] button[kind="secondary"], [data-testid="stMain"] button[kind="secondary"] p{background:#FFFFFF;color:#122D2A}
[data-testid="stMain"] button[kind="primary"] p{color:#FFFFFF}
[data-testid="stMain"] [data-testid="stMetricLabel"] p{color:#596C66}
[data-testid="stMain"] [data-testid="stExpander"] details>summary{color:#122D2A;background:#FFFFFF}
[data-testid="stMain"] [data-testid="stAlert"] p{color:#122D2A}

.nbd-brand{font-family:'Manrope',sans-serif;font-weight:800;font-size:24px;letter-spacing:-1px;margin:12px 0 0}
.nbd-brand em{font-style:normal;color:#C7EAB0}.nbd-tag{font-size:12px;color:#BED2C8;margin:6px 0 28px}
.nbd-hero{padding:38px;border-radius:24px;background:linear-gradient(120deg,#173D33,#285541);color:#fff;margin-bottom:24px;position:relative;overflow:hidden}
.nbd-hero:after{content:'';position:absolute;width:230px;height:230px;border:40px solid #BFE6AC12;border-radius:50%;right:-70px;top:40px;pointer-events:none}
.nbd-hero h1{color:#F7FBF4;font-size:clamp(28px,4vw,46px);line-height:1.13;margin:14px 0}
.nbd-hero p{color:#D5E7D8;max-width:610px;font-size:16px;line-height:1.6}
.nbd-eyebrow{font-size:11px;letter-spacing:2px;color:#C7EAB0;font-weight:700}
.nbd-welcome{padding:3.5rem 0 2rem}.nbd-welcome h1{font-size:clamp(38px,5vw,64px);line-height:1.05;margin:.6rem 0 1.2rem}.nbd-welcome p{font-size:17px;line-height:1.65;max-width:650px}.nbd-welcome img{filter:drop-shadow(0 20px 32px rgba(18,59,52,.16))}
@media(max-width:640px){[data-testid="stMainBlockContainer"]{padding:1.1rem}.nbd-hero{padding:24px}h1{font-size:30px!important}[data-testid="stHorizontalBlock"]{flex-wrap:wrap}[data-testid="stColumn"]{min-width:100%!important}}
</style>'''


def render_backup(state):
    heading('Your data', 'Keep your progress with you.', 'Download a private copy of your saved profile, then restore it when you return.')
    st.info('Your profile is saved in this browser session. Refreshing, disconnecting, or closing the page can reset it. Download a backup before leaving.')
    with st.container(border=True):
        st.subheader('Save a profile backup')
        st.write('Includes saved personal facts, all money-habit answers, financial inputs, and goals. Exploratory allocation and forecast controls are not included.')
        st.download_button('Download my profile', export_backup(state), 'nextbestdollar-profile.json', 'application/json', type='primary')
        st.caption('This file contains personal and financial information. Store it somewhere private.')
    with st.container(border=True):
        st.subheader('Pick up where you left off')
        upload = st.file_uploader('Choose your NextBestDollar JSON backup', type=['json'])
        if st.button('Restore saved profile', disabled=upload is None):
            try:
                restored = read_backup(upload.getvalue())
            except (ValueError, TypeError, KeyError, UnicodeError, RecursionError) as exc:
                st.error(f'Could not restore profile: {exc}')
            else:
                st.session_state.profile = restored
                st.session_state.revision += 1
                st.session_state.fin_step = 0
                go('Overview' if restored['onboarding_complete'] else 'Personal facts')


def render_welcome(state):
    st.markdown('<div class="nbd-welcome">', unsafe_allow_html=True)
    left, right = st.columns([1.2, 0.8], vertical_alignment='center')
    with left:
        st.caption('WELCOME TO NEXTBESTDOLLAR')
        st.title('Make your next dollar count.')
        st.write('A forward-looking financial plan that starts with your real life, connects your goals, and helps you see what your choices can make possible.')
        st.write('You will answer a few questions about your situation, money habits, and financial picture. Then you can explore your goals, your next best moves, and the future you are building.')
        if state['onboarding_complete']:
            primary_label, destination = 'Open my plan', 'Overview'
        elif any(state.get(key) for key in ('personal_complete', 'behavioral_complete', 'financial_complete')):
            primary_label, destination = 'Continue my plan', 'Personal facts' if not state['personal_complete'] else 'Money habits' if not state['behavioral_complete'] else 'Financial facts'
        else:
            primary_label, destination = 'Start my plan', 'Personal facts'
        if st.button(primary_label, type='primary', width='stretch'):
            go(destination)
        st.caption('Your profile stays in this browser session. You can download a private backup whenever you want.')
    with right:
        st.image('assets/nextbestdollar-icon.png', width=220)
    st.markdown('</div>', unsafe_allow_html=True)
    st.divider()
    first, second, third = st.columns(3)
    for column, number, title, detail in (
        (first, '01', 'See your starting point', 'Bring together income, expenses, accounts, debts, and the goals that matter to you.'),
        (second, '02', 'Give money a purpose', 'Turn your financial picture into a plan for today, with transparent tradeoffs.'),
        (third, '03', 'Make the future tangible', 'Explore how time, contributions, and goals can change what is possible.'),
    ):
        with column:
            with st.container(border=True):
                st.caption(number)
                st.subheader(title)
                st.write(detail)


def main():
    st.set_page_config(page_title='NextBestDollar · Your money, moving forward', page_icon='↗', layout='wide')
    st.markdown(STYLE, unsafe_allow_html=True)
    if 'profile' not in st.session_state:
        st.session_state.profile = clean_profile({})
    if 'redesign_loaded' not in st.session_state:
        st.session_state.profile = clean_profile(st.session_state.profile)
        st.session_state.redesign_loaded = True
    st.session_state.setdefault('revision', 0)
    st.session_state.setdefault('page', 'Overview' if st.session_state.profile.get('onboarding_complete') else 'Welcome')
    # Retain in-progress answers when navigating between views in this session.
    for key in list(st.session_state):
        if key.startswith(('personal_', 'behavior_', 'loans_', 'savings_', 'roth_', 'initial_', 'monthly_', 'years_', 'rate_', 'increase_')):
            st.session_state[key] = st.session_state[key]
    state = st.session_state.profile
    with st.sidebar:
        st.markdown('<div class="nbd-brand">NextBest<em>Dollar</em> ↗</div><div class="nbd-tag">YOUR MONEY, MOVING FORWARD</div>', unsafe_allow_html=True)
        st.caption('YOUR PLAN')
        for label in ('Overview', 'Goals', 'My allocation', 'Forecast'):
            if st.button(label, key=f'nav_{label}', width='stretch', type='primary' if st.session_state.page==label else 'secondary'): go(label)
        st.divider()
        st.caption('YOUR FOUNDATION')
        for label, flag in [('Personal facts','personal_complete'),('Money habits','behavioral_complete'),('Financial facts','financial_complete')]:
            if st.button(('✓ ' if state.get(flag) else '○ ')+label, key=f'nav_{label}', width='stretch'): go(label)
        completed = sum(bool(state.get(k)) for k in ('personal_complete','behavioral_complete','financial_complete'))
        st.progress(completed/3, text=f'{completed} of 3 profile sections saved')
        st.divider()
        if st.button('Save & restore profile', width='stretch'): go('Your data')
        st.caption('Make the next dollar easier to allocate intelligently. Plan forward, learn why, and move toward what matters.')
        st.caption('BETA · Session storage · No account linking')
    page = st.session_state.page
    if page in ('Personal facts','Money habits','Financial facts'):
        st.caption('YOUR FOUNDATION   /   PERSONAL → MONEY HABITS → FINANCIAL')
    if page == 'Welcome': render_welcome(state)
    elif page == 'Personal facts': render_personal(state)
    elif page == 'Money habits': render_behavioral(state)
    elif page == 'Financial facts': render_financial(state)
    elif page == 'Overview': render_overview(state)
    elif page == 'Your data': render_backup(state)
    else: render_planning(state, page)
    st.divider()
    st.caption('NextBestDollar · A clearer decision today. More possibility tomorrow.   |   Save a backup before you leave.')

FIN_INCOME_FIELDS = [
    ('Primary monthly take-home income', 'primary_take_home', 'Your typical monthly paycheck income after taxes.'),
    ('Other recurring monthly income', 'other_recurring_income', 'Side work, rental income, support, or other predictable recurring income.'),
    ('Average monthly variable income', 'variable_income', 'Average bonuses, commissions, tips, or irregular income across a normal year.'),
]
FIN_SPENDING_FIELDS = [
    ('Housing', 'housing', 'Rent or housing contribution. Enter mortgage principal/interest in Debt; count taxes and insurance only once.'),
    ('Utilities', 'utilities', 'Electricity, gas, water, internet, and phone.'),
    ('Groceries', 'groceries', 'Food purchased for home.'),
    ('Dining & coffee', 'dining', 'Restaurants, takeout, coffee, and similar spending.'),
    ('Transportation', 'transportation', 'Gas, transit, parking, maintenance, rideshare, excluding loan payments.'),
    ('Insurance', 'insurance', 'Health, auto, renters/home, life, or other insurance paid personally.'),
    ('Subscriptions', 'subscriptions', 'Streaming, software, memberships, and recurring services.'),
    ('Entertainment & personal', 'entertainment', 'Shopping, hobbies, events, personal care, and discretionary spending.'),
    ('Childcare / dependents', 'dependents_spending', 'Childcare, dependent support, or recurring family obligations.'),
    ('Other recurring spending', 'other_spending', 'Any recurring monthly spending not captured above.'),
]
FIN_DEBT_TYPES = ['Credit card', 'Student loan', 'Auto loan', 'Personal loan', 'Mortgage', 'Medical debt', 'Other debt']


def fin_commit(candidate, step=None, complete=False):
    """Commit atomically: invalid edits never replace the saved session profile."""
    try:
        if complete:
            candidate['financial_complete'] = True
            candidate['onboarding_complete'] = bool(candidate.get('personal_complete') and candidate.get('behavioral_complete'))
        st.session_state.profile = clean_profile(candidate)
    except (ValueError, TypeError) as exc:
        st.error(str(exc))
        return False
    st.session_state.revision = st.session_state.get('revision', 0) + 1
    if step is not None:
        st.session_state.fin_step = step
    if complete:
        st.session_state.page = 'Overview'
        st.session_state.financial_just_saved = True
    st.rerun()


def fin_account_editor(state, types, prefix):
    """Single-column forms keep every account field usable on a phone."""
    rev = st.session_state.get('revision', 0)
    entries = state['financial']['account_entries']
    st.subheader('Which accounts do you have?')
    st.caption('Add each account separately. You can add several from the same bank or provider. Zero-balance accounts are welcome.')
    choices = list(types)
    matching = [(i, row) for i, row in enumerate(entries) if row['type'] in types]
    for index, row in matching:
        with st.expander(f"{row['name']} · ${row['balance']:,.2f}"):
            with st.form(f'{prefix}_edit_{index}_{rev}'):
                kind = st.selectbox('Account type', choices, index=choices.index(row['type']), format_func=types.get)
                name = st.text_input('Account nickname (e.g., Everyday checking)', value=row['name'])
                provider = st.text_input('Bank / provider (optional)', value=row.get('provider', ''))
                balance = amount('Current balance ($)', row['balance'])
                saved = st.form_submit_button('Save account', type='primary')
                removed = st.form_submit_button('Remove account')
            if saved or removed:
                draft = deepcopy(state)
                if removed:
                    draft['financial']['account_entries'].pop(index)
                else:
                    draft['financial']['account_entries'][index] = dict(type=kind, name=name.strip(), provider=provider.strip(), balance=balance)
                fin_commit(draft)
    with st.expander('＋ Add an account', expanded=not matching):
        with st.form(f'{prefix}_add_{rev}', clear_on_submit=True):
            kind = st.selectbox('Account type', choices, format_func=types.get)
            name = st.text_input('Account nickname (e.g., Everyday checking)')
            provider = st.text_input('Bank / provider (optional)')
            balance = amount('Current balance ($)')
            submitted = st.form_submit_button('Add account', type='primary')
        if submitted:
            draft = deepcopy(state)
            draft['financial']['account_entries'].append(dict(type=kind, name=name.strip(), provider=provider.strip(), balance=balance))
            fin_commit(draft)


def fin_debt_editor(state):
    rev = st.session_state.get('revision', 0)
    debts = state['financial']['debt']
    for index, row in enumerate(debts):
        with st.expander(f"{row['name']} · ${row['balance']:,.2f} · {row['apr']:.2f}% APR"):
            with st.form(f'fin_debt_edit_{index}_{rev}'):
                choices = FIN_DEBT_TYPES if row.get('type') in FIN_DEBT_TYPES else FIN_DEBT_TYPES + [row.get('type', 'Other debt')]
                kind = st.selectbox('Debt type', choices, index=choices.index(row.get('type', 'Other debt')))
                name = st.text_input('Account / loan name', value=row['name'], help='Example: Federal Loan 2025, Discover Card, Auto Loan.')
                provider = st.text_input('Lender / card issuer (optional)', value=row.get('provider', ''))
                balance = amount('Current balance ($)', row['balance'])
                apr = st.number_input('APR / interest rate (%)', min_value=0.0, max_value=100.0, value=float(row['apr']), step=0.1)
                minimum = amount('Required monthly payment ($)', row['minimum_payment'])
                saved = st.form_submit_button('Save debt', type='primary')
                removed = st.form_submit_button('Remove debt')
            if saved or removed:
                draft = deepcopy(state)
                if removed:
                    draft['financial']['debt'].pop(index)
                else:
                    draft['financial']['debt'][index] = dict(type=kind, name=name.strip(), provider=provider.strip(), balance=balance, apr=apr, minimum_payment=minimum)
                fin_commit(draft)
    with st.expander('＋ Add a debt', expanded=not debts):
        with st.form(f'fin_debt_add_{rev}', clear_on_submit=True):
            kind = st.selectbox('Debt type', FIN_DEBT_TYPES)
            name = st.text_input('Account / loan name', help='Example: Federal Loan 2025, Discover Card, Auto Loan.')
            provider = st.text_input('Lender / card issuer (optional)')
            balance = amount('Current balance ($)')
            apr = st.number_input('APR / interest rate (%)', min_value=0.0, max_value=100.0, value=0.0, step=0.1)
            minimum = amount('Required monthly payment ($)')
            submitted = st.form_submit_button('Add debt', type='primary')
        if submitted:
            draft = deepcopy(state)
            draft['financial']['debt'].append(dict(type=kind, name=name.strip(), provider=provider.strip(), balance=balance, apr=apr, minimum_payment=minimum))
            fin_commit(draft)


def render_financial(state):
    step = max(0, min(3, st.session_state.get('fin_step', 0)))
    rev = st.session_state.get('revision', 0)
    financial = state['financial']
    titles = ['Income', 'Monthly Spending', 'Accounts & Savings', 'Debt & Investments']
    st.caption(f'FINANCIAL FACTS · STEP {step + 1} OF 4')
    st.subheader(titles[step])
    st.progress((step + 1) / 4)
    st.caption('Save each step to keep your progress in this session. Download your profile from Save & restore to keep a copy for later.')
    if step in (0, 1):
        group = 'income' if step == 0 else 'spending'
        fields = FIN_INCOME_FIELDS if step == 0 else FIN_SPENDING_FIELDS
        # Preserve totals from the earlier single-expense web profile on migration.
        defaults = deepcopy(financial[group])
        known = {key for _, key, _ in fields}
        fallback = 'other_recurring_income' if step == 0 else 'other_spending'
        defaults[fallback] = defaults.get(fallback, 0) + sum(v for k, v in defaults.items() if k not in known)
        with st.container(border=True):
            st.markdown('#### Monthly Income' if step == 0 else '#### Core Monthly Expenses')
            st.caption('Enter what typically reaches your household after taxes and payroll deductions. Rough estimates are okay.' if step == 0 else 'Use average monthly amounts. Debt minimum payments are entered separately in Step 4. Estimates do not need to be perfect.')
            with st.form(f'fin_{group}_{rev}'):
                values = {key: amount(label + ' ($)', defaults.get(key, 0), help=helper) for label, key, helper in fields}
                forward = st.form_submit_button('Save & continue', type='primary')
                back = st.form_submit_button('Save & back') if step else False
            if forward or back:
                draft = deepcopy(state)
                draft['financial'][group] = values
                fin_commit(draft, step=step + (1 if forward else -1))
    elif step == 2:
        with st.container(border=True):
            fin_account_editor(state, CASH_TYPES, 'fin_cash')
        with st.container(border=True):
            st.markdown('#### Emergency savings')
            st.caption('This is part of your cash balances above, not extra money. If removing cash accounts, first reduce this reserve to fit the remaining cash.')
            with st.form(f'fin_emergency_{rev}'):
                reserve = amount('Cash reserved for emergencies ($)', financial['accounts'].get('emergency_fund', 0))
                forward = st.form_submit_button('Save & continue', type='primary')
                save = st.form_submit_button('Save reserve')
                back = st.form_submit_button('Save & back')
            if forward or save or back:
                draft = deepcopy(state)
                draft['financial']['accounts']['emergency_fund'] = reserve
                fin_commit(draft, step=3 if forward else 1 if back else 2)
    else:
        with st.container(border=True):
            st.markdown('#### Debt')
            st.caption('Add each debt separately, especially student loans with different interest rates. Save each account before continuing.')
            has_debt = st.radio('Do you currently have debt?', ['No', 'Yes'], index=1 if financial['debt'] else 0, horizontal=True, key=f'fin_has_debt_{rev}')
            if has_debt == 'Yes':
                fin_debt_editor(state)
            elif financial['debt']:
                st.warning('Saving “No” will remove your recorded debts. Confirm below, or choose Yes to keep them.')
            clear_confirm = st.checkbox('Remove all recorded debts when I save', key=f'fin_clear_debt_{rev}') if has_debt == 'No' and financial['debt'] else False
        with st.container(border=True):
            st.markdown('#### Investments')
            fin_account_editor(state, INVESTMENT_TYPES, 'fin_investments')
        with st.container(border=True):
            st.markdown('#### Employer Retirement Benefits')
            st.caption('These fields help identify whether employer match is being left unused.')
            with st.form(f'fin_finish_{rev}'):
                contribution = st.number_input('Your current retirement contribution (%)', min_value=0.0, max_value=100.0, value=float(financial['benefits'].get('current_retirement_contribution', 0)), step=0.5, help='Enter the percent of pay you currently contribute.')
                match = st.number_input('Employer match available (%)', min_value=0.0, max_value=100.0, value=float(financial['benefits'].get('employer_match', 0)), step=0.5, help='Enter the maximum employer match as a percent of pay, if known.')
                finish = st.form_submit_button('Save financial profile', type='primary')
                back = st.form_submit_button('Save & back')
            if finish or back:
                if has_debt == 'Yes' and not financial['debt']:
                    st.error('You selected Yes for debt. Please add at least one debt account.')
                elif has_debt == 'No' and financial['debt'] and not clear_confirm:
                    st.error('Confirm removal of recorded debts, or choose Yes to keep them.')
                else:
                    draft = deepcopy(state)
                    if has_debt == 'No':
                        draft['financial']['debt'] = []
                    draft['financial']['benefits'] = dict(current_retirement_contribution=contribution, employer_match=match)
                    fin_commit(draft, step=2 if back else 3, complete=finish)


if __name__ == "__main__":
    main()
