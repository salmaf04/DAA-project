def solve_discrete_transport(items, mule_capacities):
    # items: list of tuples [(value1, weight1), (value2, weight2), ...]
    # mule_capacities: list with each mule's maximum weight [cap1, cap2, ...]

    num_items = len(items)
    num_mules = len(mule_capacities)
    memo = {}

    def solve(idx, mule_states):
        # mule_states is a tuple of tuples: ((accum_value, accum_weight), ...)
        current_state = (idx, mule_states)

        if current_state in memo:
            return memo[current_state]

        if idx == num_items:
            values = [state[0] for state in mule_states]
            # Objective: minimize the difference between the max and min values
            return max(values) - min(values), mule_states

        best_diff = float('inf')
        best_configuration = None

        item_value, item_weight = items[idx]

        for mule_idx in range(num_mules):
            current_value, current_weight = mule_states[mule_idx]

            if current_weight + item_weight <= mule_capacities[mule_idx]:
                mule_states_list = list(mule_states)
                mule_states_list[mule_idx] = (current_value + item_value, current_weight + item_weight)

                diff, config = solve(idx + 1, tuple(mule_states_list))

                if diff < best_diff:
                    best_diff = diff
                    best_configuration = config

        memo[current_state] = (best_diff, best_configuration)
        return best_diff, best_configuration

    initial_mule_states = tuple((0, 0) for _ in range(num_mules))
    optimal_diff, final_configuration = solve(0, initial_mule_states)

    return optimal_diff, final_configuration
