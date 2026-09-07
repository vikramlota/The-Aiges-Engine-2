"""
Phase 2.3 Game-Theory Ad-Allocation Agent using Multi-Armed Bandit (Thompson Sampling).
Optimizes marketing spend distribution across channels (Instagram, YouTube, Meta, Google)
with strict exploration vs exploitation balance and explainable rationale.
"""
import math
import random
from typing import List, Dict, Any


def run_thompson_sampling_optimizer(
    channels: List[Dict[str, Any]],
    total_budget: float,
    num_simulations: int = 5000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Runs Bayesian Thompson Sampling multi-armed bandit simulation on ad channels.
    Returns recommended allocation percentages, spend shifts, confidence, and plain-language reasoning.
    """
    if not channels:
        return {
            "shifts": [],
            "reasoning": "No ad channels configured in campaign.",
            "confidence": 0.0
        }

    rng = random.Random(seed)
    n_channels = len(channels)

    # 1. Compute empirical metrics and posterior distribution parameters
    channel_stats = []
    total_conversions = 0
    total_spend = 0.0

    for ch in channels:
        name = ch["name"]
        spend = float(ch.get("current_spend", 0.0))
        impressions = int(ch.get("impressions", 0))
        clicks = int(ch.get("clicks", 0))
        conversions = int(ch.get("conversions", 0))
        revenue = float(ch.get("revenue", 0.0))
        current_pct = float(ch.get("current_allocation_pct", 100.0 / n_channels))

        total_conversions += conversions
        total_spend += spend

        # Return on Ad Spend (ROAS)
        roas = (revenue / spend) if spend > 0 else 0.0
        cvr = (conversions / clicks) if clicks > 0 else 0.0
        ctr = (clicks / impressions) if impressions > 0 else 0.0

        # Bayesian posterior parameters:
        # Prior: Normal(mu_0 = 1.5, sigma_0 = 1.0) representing typical baseline ROAS
        # Likelihood variance shrinks with more conversions
        prior_mu = 1.5
        prior_var = 1.0

        if conversions > 0 and spend > 0:
            # Observation variance inversely proportional to sqrt of sample size
            obs_var = max(0.1, 4.0 / math.sqrt(conversions))
            post_var = 1.0 / (1.0 / prior_var + 1.0 / obs_var)
            post_mu = post_var * (prior_mu / prior_var + roas / obs_var)
        else:
            # Thin data -> maintains prior uncertainty
            post_mu = prior_mu
            post_var = prior_var

        channel_stats.append({
            "name": name,
            "current_pct": current_pct,
            "spend": spend,
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "revenue": revenue,
            "roas": round(roas, 2),
            "cvr": round(cvr * 100, 2),
            "ctr": round(ctr * 100, 2),
            "post_mu": post_mu,
            "post_sigma": math.sqrt(post_var),
            "wins": 0
        })

    # 2. Monte Carlo Thompson Sampling draws
    for _ in range(num_simulations):
        best_val = -float("inf")
        best_idx = 0
        for idx, ch in enumerate(channel_stats):
            # Sample from posterior Normal(mu, sigma)
            sample = rng.gauss(ch["post_mu"], ch["post_sigma"])
            if sample > best_val:
                best_val = sample
                best_idx = idx
        channel_stats[best_idx]["wins"] += 1

    # 3. Calculate target allocations with Exploration Floor
    # Exploratory floor prevents starving unproven or promising channels
    min_floor_pct = max(5.0, round(100.0 / (n_channels * 4), 1))
    remaining_pct = max(0.0, 100.0 - (min_floor_pct * n_channels))

    target_allocations = []
    for ch in channel_stats:
        win_prob = ch["wins"] / float(num_simulations)
        ch["win_prob"] = win_prob
        raw_target = min_floor_pct + (remaining_pct * win_prob)

        # Smooth shift: limit maximum single-period change to ±15% to maintain budgetary stability
        max_delta = 15.0
        bounded_target = max(
            min_floor_pct,
            min(ch["current_pct"] + max_delta, max(ch["current_pct"] - max_delta, raw_target))
        )
        target_allocations.append(bounded_target)

    # Normalize target percentages so they sum exactly to 100.0%
    sum_targets = sum(target_allocations)
    if sum_targets > 0:
        normalized_targets = [round((t / sum_targets) * 100.0, 1) for t in target_allocations]
        diff = round(100.0 - sum(normalized_targets), 1)
        max_idx = max(range(n_channels), key=lambda i: channel_stats[i]["wins"])
        normalized_targets[max_idx] = round(normalized_targets[max_idx] + diff, 1)
    else:
        normalized_targets = [round(100.0 / n_channels, 1) for _ in range(n_channels)]

    # 4. Build output channel shifts
    shifts = []
    for idx, ch in enumerate(channel_stats):
        suggested_pct = normalized_targets[idx]
        delta_pct = round(suggested_pct - ch["current_pct"], 1)
        suggested_spend = round(total_budget * (suggested_pct / 100.0), 2)

        shifts.append({
            "channel_name": ch["name"],
            "current_pct": ch["current_pct"],
            "suggested_pct": suggested_pct,
            "delta_pct": delta_pct,
            "current_spend": ch["spend"],
            "suggested_spend": suggested_spend,
            "roas": ch["roas"],
            "conversions": ch["conversions"],
            "win_probability": round(ch["win_prob"] * 100, 1)
        })

    # Sort shifts by highest positive delta
    shifts.sort(key=lambda s: s["delta_pct"], reverse=True)

    # 5. Compute statistical confidence & plain-language explanation
    top_channel = shifts[0]
    bottom_channel = shifts[-1]

    # Data volume penalty on confidence
    base_confidence = max(s["win_probability"] for s in shifts) / 100.0
    if total_conversions < 20:
        confidence = round(max(0.35, base_confidence * 0.6), 2)
        data_note = f" (Note: Total conversions across campaign is low at {total_conversions}; keeping conservative shifts with {min_floor_pct}% exploration floor)."
    elif total_conversions < 50:
        confidence = round(max(0.55, base_confidence * 0.8), 2)
        data_note = f" (Moderate data volume: {total_conversions} conversions recorded)."
    else:
        confidence = round(base_confidence, 2)
        data_note = f" (High statistical significance: {total_conversions} total conversions evaluated)."

    if top_channel["delta_pct"] > 0:
        reasoning = (
            f"Thompson Sampling recommends shifting +{top_channel['delta_pct']}% budget toward "
            f"'{top_channel['channel_name']}' (observed ROAS: {top_channel['roas']}x, {top_channel['win_probability']}% marginal win rate). "
            f"Funded primarily by reducing '{bottom_channel['channel_name']}' by {abs(bottom_channel['delta_pct'])}% "
            f"(observed ROAS: {bottom_channel['roas']}x).{data_note}"
        )
    else:
        reasoning = (
            f"Current allocation is close to optimal equilibrium across all active channels. "
            f"Preserving existing spend distribution with {min_floor_pct}% protective exploration floor.{data_note}"
        )

    return {
        "shifts": shifts,
        "reasoning": reasoning,
        "confidence": confidence
    }
