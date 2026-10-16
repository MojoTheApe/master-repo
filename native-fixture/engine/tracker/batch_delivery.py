"""Project batch completion from matching admission/delivery evidence, not labels."""
from . import delivery_policy as rules


def project(batch, workflow):
    expected = set(batch.get('main_prs', []))
    promotions = dict(workflow.get('promotions', {}), **workflow.get('main_batches', {}))
    policy = next((promotions.get(str(pr), {}).get('policy') for pr in expected
                   if promotions.get(str(pr), {}).get('batch_id') == batch['id']), None)
    members = []
    for number in batch['issues']:
        receipt = workflow.get('tasks', {}).get(str(number), {})
        candidates = [receipt, *reversed(receipt.get('history', []))]
        compatible = {policy}
        for row in candidates:
            if row.get('policy') == policy and expected <= {s.get('pr') for s in row.get('sources', [])}:
                compatible.add(rules.summary(row).get('policy'))
        matching = [r for r in candidates if expected and policy and r.get('policy') in compatible
                    and expected <= {s.get('pr') for s in r.get('sources', [])}]
        # Current failures supersede older success for the same admitted scope.
        # A reopened Issue can still recover its prior batch's latest receipt.
        selected = next(iter(matching), {})
        members.append(rules.summary(selected))
    effective = {r.get('policy') for r in members}
    return {'policy': next(iter(effective)) if len(effective) == 1 else policy, 'receipts': members}


def finish(batch, config):
    """Turn allowlisted evidence into a public result for this exact composition."""
    proof = batch.pop('delivery_evidence', {})
    members = proof.get('receipts', [])
    total = len(batch['issues'])
    current = proof.get('policy') == rules.fingerprint(config)
    merge_complete = current and rules.policy(config)['completion'] == 'reviewed-merge'
    done = sum(bool(current and r.get('admitted') and (r.get('verified') or merge_complete)) for r in members)
    terminal = batch['state'] == 'merged'
    state = ('delivered' if terminal and total and done == total else
             'failed' if terminal and current and any(r.get('state') == 'failed' for r in members) else
             'pending' if terminal else 'inactive' if batch['state'] == 'cancelled' else 'working')
    batch['delivery'] = {'state': state, 'complete': bool(state == 'delivered'), 'count': done if terminal else 0, 'total': total}
