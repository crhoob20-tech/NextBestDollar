import unittest
from copy import deepcopy
from recommendations import next_action
from allocation import allocate


def profile(income=3000, spending=2000, reserve=0, debts=None):
    return dict(financial_complete=True, financial=dict(
        income={'primary_take_home': income}, spending={'housing': spending},
        accounts={'savings': reserve, 'emergency_fund': reserve}, debt=debts or []))


class RecommendationsTests(unittest.TestCase):
    def test_setup(self):
        self.assertEqual(next_action({})['kind'], 'setup')

    def test_shortfall_and_zero(self):
        for income in (1000, 2000):
            result = next_action(profile(income=income))
            self.assertEqual(result['kind'], 'shortfall')
            self.assertEqual(result['amount'], 0)

    def test_reserve_gap_caps_amount(self):
        self.assertEqual(next_action(profile(reserve=1900))['amount'], 100)

    def test_does_not_spend_checking_balance(self):
        state = profile()
        state['financial']['accounts']['checking'] = 50000
        self.assertEqual(next_action(state)['kind'], 'buffer')

    def test_debt_minimums_deducted_once(self):
        debts = [dict(name='Card', balance=5000, minimum_payment=200, apr=25)]
        result = next_action(profile(reserve=3000, debts=debts))
        self.assertEqual(result['kind'], 'debt')
        self.assertEqual(result['amount'], 800)

    def test_highest_apr_and_payoff_cap(self):
        debts = [dict(name='Loan', balance=5000, minimum_payment=100, apr=10),
                 dict(name='Card', balance=300, minimum_payment=100, apr=25)]
        result = next_action(profile(reserve=3000, debts=debts))
        self.assertIn('Card', result['title'])
        self.assertEqual(result['amount'], 200)

    def test_reserve_then_goals(self):
        self.assertEqual(next_action(profile(reserve=2000))['kind'], 'reserve')
        self.assertEqual(next_action(profile(reserve=6000))['kind'], 'plan')

    def test_invalid_data_never_recommends_amount(self):
        for value in (float('nan'), float('inf'), -1, 'broken', None, True):
            self.assertEqual(next_action(profile(income=value))['kind'], 'review')
        state = profile()
        state['financial']['debt'] = [{'balance': 1000}]
        self.assertEqual(next_action(state)['kind'], 'review')

    def test_impossible_reserve_and_missing_costs(self):
        state = profile(reserve=500)
        state['financial']['accounts']['savings'] = 0
        self.assertEqual(next_action(state)['kind'], 'review')
        self.assertEqual(next_action(profile(spending=0))['kind'], 'review')

    def test_no_mutation_or_cached_metric_dependency(self):
        state = profile()
        state['financial_metrics'] = {'monthly_free_cash_flow': 999999}
        original = deepcopy(state)
        self.assertEqual(next_action(state)['amount'], 1000)
        self.assertEqual(state, original)

    def test_legacy_debt_shape(self):
        state = profile(reserve=3000)
        state['financial']['debt'] = {'credit_card': dict(balance=5000, minimum_payment=200, apr=25)}
        self.assertEqual(next_action(state)['kind'], 'debt')

    def test_existing_allocation_conserves_cash(self):
        for income in (0, 1000, 5000):
            result = allocate(income, 1500, 500, 300, 100, 200)
            self.assertEqual(result['living_expenses_funded'] + sum(row[2] for row in result['rows']), income)
            self.assertTrue(all(row[2] >= 0 for row in result['rows']))


if __name__ == '__main__':
    unittest.main()
