def kernelization_preprocessing(items, mule_capacities):
    """Kernelization (Pre-processing).
    Filters and discards items that cannot be transported before running the algorithm.
    Criterion: an item whose weight exceeds the strongest mule's capacity is impossible to transport.
    """
    if not mule_capacities:
        return [], items
    max_capacity = max(mule_capacities)
    valid_items = []
    infeasible_items = []
    for item in items:
        weight = item[1]
        if weight > max_capacity:
            infeasible_items.append(item)
        else:
            valid_items.append(item)
    return valid_items, infeasible_items

def efficient_solution(items, mule_capacities):
    # 1. Kernelization 
    processable_items, initial_rejections = kernelization_preprocessing(items, mule_capacities)
    
    # 2. Improved greedy LPT (value-descending order keeps the risk balanced)
    sorted_items = sorted(
        [(value, weight, idx) for idx, (value, weight) in enumerate(processable_items)],
        key=lambda x: x[0],
        reverse=True
    )
    
    mule_count = len(mule_capacities)
    mules = [
        {'value': 0, 'weight': 0, 'capacity': capacity, 'items': []}
        for capacity in mule_capacities
    ]
    
    unassigned_items = []
    for value, weight, original_index in sorted_items:
        mule_indices_by_value = sorted(range(mule_count), key=lambda mule_idx: mules[mule_idx]['value'])
        assigned = False
        for mule_idx in mule_indices_by_value:
            if mules[mule_idx]['weight'] + weight <= mules[mule_idx]['capacity']:
                mules[mule_idx]['value'] += value
                mules[mule_idx]['weight'] += weight
                mules[mule_idx]['items'].append((value, weight, original_index))
                assigned = True
                break
        if not assigned:
            unassigned_items.append((value, weight, original_index))

    # 3. Reinforced local search (moves + swaps)
    improved = True
    while improved:
        improved = False
        richest_mule = max(range(mule_count), key=lambda mule_idx: mules[mule_idx]['value'])
        poorest_mule = min(range(mule_count), key=lambda mule_idx: mules[mule_idx]['value'])
        current_diff = mules[richest_mule]['value'] - mules[poorest_mule]['value']

        for i, rich_item in enumerate(mules[richest_mule]['items']):
            rich_value, rich_weight, _ = rich_item
            if mules[poorest_mule]['weight'] + rich_weight <= mules[poorest_mule]['capacity']:
                new_diff = abs(
                    (mules[richest_mule]['value'] - rich_value)
                    - (mules[poorest_mule]['value'] + rich_value)
                )
                if new_diff < current_diff:
                    mules[poorest_mule]['items'].append(mules[richest_mule]['items'].pop(i))
                    mules[richest_mule]['value'] -= rich_value
                    mules[richest_mule]['weight'] -= rich_weight
                    mules[poorest_mule]['value'] += rich_value
                    mules[poorest_mule]['weight'] += rich_weight
                    improved = True
                    break
        if improved:
            continue

        for i, rich_item in enumerate(mules[richest_mule]['items']):
            rich_value, rich_weight, _ = rich_item
            for j, poor_item in enumerate(mules[poorest_mule]['items']):
                poor_value, poor_weight, _ = poor_item
                rich_weight_after_swap = (
                    mules[richest_mule]['weight'] - rich_weight + poor_weight
                )
                poor_weight_after_swap = (
                    mules[poorest_mule]['weight'] - poor_weight + rich_weight
                )
                
                if (
                    rich_weight_after_swap <= mules[richest_mule]['capacity']
                    and poor_weight_after_swap <= mules[poorest_mule]['capacity']
                ):
                    new_diff = abs(
                        (mules[richest_mule]['value'] - rich_value + poor_value)
                        - (mules[poorest_mule]['value'] - poor_value + rich_value)
                    )
                    if new_diff < current_diff:
                        mules[richest_mule]['items'][i], mules[poorest_mule]['items'][j] = (
                            mules[poorest_mule]['items'][j],
                            mules[richest_mule]['items'][i],
                        )
                        mules[richest_mule]['value'] += poor_value - rich_value
                        mules[richest_mule]['weight'] += poor_weight - rich_weight
                        mules[poorest_mule]['value'] += rich_value - poor_value
                        mules[poorest_mule]['weight'] += rich_weight - poor_weight
                        improved = True
                        break
            if improved:
                break

    value_difference = max(mule['value'] for mule in mules) - min(mule['value'] for mule in mules)
    return value_difference, mules, unassigned_items
