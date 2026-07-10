"""Verification suite for the ss-economy compute bidding marketplace."""
import unittest


class ComputeMarketplaceValidator:
    def __init__(self):
        self.ledger_bids = {}

    def register_node_bid(self, node_id: str, vram_gb: int, price_per_gigaflop: float):
        self.ledger_bids[node_id] = {
            "vram_gb": vram_gb,
            "price": price_per_gigaflop,
        }

    def match_best_resource(self, required_vram: int, max_budget_price: float):
        eligible_nodes = {
            k: v
            for k, v in self.ledger_bids.items()
            if v["vram_gb"] >= required_vram and v["price"] <= max_budget_price
        }
        if not eligible_nodes:
            return None
        return min(eligible_nodes, key=lambda k: eligible_nodes[k]["price"])


class TestSovereignEconomy(unittest.TestCase):
    def setUp(self):
        self.validator = ComputeMarketplaceValidator()
        self.validator.register_node_bid("node://us-east-gpu", vram_gb=80, price_per_gigaflop=0.004)
        self.validator.register_node_bid("node://eu-west-gpu", vram_gb=40, price_per_gigaflop=0.002)
        self.validator.register_node_bid("node://asia-south-gpu", vram_gb=24, price_per_gigaflop=0.001)

    def test_resource_matching_large_model(self):
        optimal = self.validator.match_best_resource(required_vram=80, max_budget_price=0.01)
        self.assertEqual(optimal, "node://us-east-gpu")

    def test_resource_matching_mid_model(self):
        optimal = self.validator.match_best_resource(required_vram=40, max_budget_price=0.01)
        self.assertEqual(optimal, "node://eu-west-gpu")

    def test_no_eligible_resource(self):
        optimal = self.validator.match_best_resource(required_vram=999, max_budget_price=0.01)
        self.assertIsNone(optimal)

    def test_budget_constraint(self):
        optimal = self.validator.match_best_resource(required_vram=24, max_budget_price=0.0005)
        self.assertIsNone(optimal)


if __name__ == "__main__":
    unittest.main()
