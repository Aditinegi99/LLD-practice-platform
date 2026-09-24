from app.evaluators.base import EvaluationInput
from app.evaluators.deterministic import DeterministicEvaluator

CRITERIA = [
    {"name": "Entity & Requirement Coverage", "description": "", "weight": 1.0, "evaluation_mode": "deterministic"},
    {"name": "God-Class / Coupling", "description": "", "weight": 1.0, "evaluation_mode": "deterministic"},
    {"name": "Naming Consistency", "description": "", "weight": 0.5, "evaluation_mode": "deterministic"},
]

GOOD_CODE = """
class ParkingLot:
    def find_spot(self, vehicle): pass
    def assign_spot(self, vehicle): pass

class ParkingSpot:
    def is_available(self): pass
    def occupy(self): pass

class Vehicle:
    def get_type(self): pass

class Ticket:
    def calculate_fee(self): pass
"""

GOD_CLASS_CODE = """
class ParkingLot:
    def find_spot(self): pass
    def assign_spot(self): pass
    def calculate_fee(self): pass
    def print_ticket(self): pass
    def send_email(self): pass
    def log_event(self): pass
    def validate_vehicle(self): pass
    def charge_card(self): pass

class Ticket:
    def get_id(self): pass
"""

BAD_NAMING_CODE = """
class parkinglot:
    def FindSpot(self): pass
    def assign_spot(self): pass

class ParkingSpot:
    def is_available(self): pass
"""


def make_input(code, expected_entities=None):
    return EvaluationInput(
        problem_title="Parking Lot System",
        requirements=["Support multiple vehicle types"],
        constraints=[],
        expected_entities=expected_entities or ["ParkingLot", "ParkingSpot", "Vehicle", "Ticket"],
        criteria=CRITERIA,
        rationale="Some rationale text.",
        code_payload=code,
    )


def test_entity_coverage_full_match():
    evaluator = DeterministicEvaluator()
    output = evaluator.evaluate(make_input(GOOD_CODE))
    coverage = next(r for r in output.results if r.criterion_name == "Entity & Requirement Coverage")
    assert coverage.score == 100.0
    assert coverage.source == "deterministic"


def test_entity_coverage_partial_match_reports_missing():
    evaluator = DeterministicEvaluator()
    code_missing_ticket = "class ParkingLot:\n    pass\nclass ParkingSpot:\n    pass\nclass Vehicle:\n    pass\n"
    output = evaluator.evaluate(make_input(code_missing_ticket))
    coverage = next(r for r in output.results if r.criterion_name == "Entity & Requirement Coverage")
    assert coverage.score < 100.0
    assert "Ticket" in coverage.evidence


def test_god_class_flagged_when_method_count_imbalanced():
    evaluator = DeterministicEvaluator()
    output = evaluator.evaluate(make_input(GOD_CLASS_CODE))
    god = next(r for r in output.results if r.criterion_name == "God-Class / Coupling")
    assert god.score < 70.0
    assert "god-class" in god.evidence.lower()


def test_god_class_not_flagged_for_balanced_classes():
    evaluator = DeterministicEvaluator()
    output = evaluator.evaluate(make_input(GOOD_CODE))
    god = next(r for r in output.results if r.criterion_name == "God-Class / Coupling")
    assert god.score >= 80.0


def test_naming_flags_lowercase_class_name():
    evaluator = DeterministicEvaluator()
    output = evaluator.evaluate(make_input(BAD_NAMING_CODE))
    naming = next(r for r in output.results if r.criterion_name == "Naming Consistency")
    assert naming.score < 100.0
    assert "parkinglot" in naming.evidence


def test_empty_code_does_not_crash():
    evaluator = DeterministicEvaluator()
    output = evaluator.evaluate(make_input(""))
    assert len(output.results) == 3
    coverage = next(r for r in output.results if r.criterion_name == "Entity & Requirement Coverage")
    assert coverage.score == 0.0
