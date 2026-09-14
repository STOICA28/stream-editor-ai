from stream_editor.contracts.editorial import RankingProfile, ScoreComponents


class ExperimentalRanker:
    """
    EXPERIMENTAL - NOT canonical editorial decision.
    Calculates a score based on a given ranking profile weights.
    """
    @staticmethod
    def rank(scores: ScoreComponents, profile: RankingProfile) -> float | None:
        total_score = 0.0
        total_weight = 0.0
        has_scores = False
        
        scores_dict = scores.to_dict()
        
        for key, weight in profile.weights.items():
            val = scores_dict.get(key)
            if val is not None:
                total_score += val * weight
                # Even for negative weights (like repetition), we sum the magnitude or just sum the weights?
                # Actually, usually weights can be negative (e.g. repetition). The sum of absolute weights might be used for normalization, or just raw sum.
                # If we normalize, total_weight += abs(weight). But let's just do a raw weighted sum if we don't normalize, or maybe we do.
                # I will just return the raw weighted sum as the rank. But wait, if some are missing, raw sum is unfair.
                # Normalizing by sum of absolute weights of *present* scores makes sense.
                total_weight += abs(weight)
                has_scores = True
                
        if not has_scores:
            return None
            
        return total_score / total_weight if total_weight > 0 else 0.0
