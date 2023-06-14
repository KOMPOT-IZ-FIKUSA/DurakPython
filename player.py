from probability_container import ProbabilityContainer as ProbContainer


class Player:
    def __init__(self, ranks_count):
        self.probs_container = ProbContainer(ranks_count)

    def get_known_cards(self):
        return self.probs_container.get_known_existing_cards_indices()