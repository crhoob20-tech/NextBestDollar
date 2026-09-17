"""Explainable prompts from saved facts; users review before creating a goal."""
from financial import normalize_financial

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
