from sqlalchemy.orm import Session
from . import models

PROBLEMS = [
    {
        "slug": "parking-lot",
        "title": "Parking Lot System",
        "difficulty": "easy",
        "summary": "Design a multi-level parking lot that supports different vehicle types, "
                   "spot allocation, and fee calculation.",
        "requirements": [
            "Support multiple vehicle types (motorcycle, car, bus) with different spot size needs.",
            "Assign the nearest available suitable spot when a vehicle enters.",
            "Track occupancy per level and raise a clear signal when the lot is full.",
            "Calculate a parking fee based on duration when a vehicle exits.",
        ],
        "constraints": [
            "A bus may require multiple adjacent spots or a dedicated large spot - your choice, but state it.",
            "Should support adding a new vehicle type later without rewriting the allocation logic.",
        ],
        "expected_entities": ["ParkingLot", "ParkingSpot", "Vehicle", "Ticket"],
        "criteria": [
            {"name": "Entity & Requirement Coverage", "weight": 1.0, "mode": "deterministic",
             "description": "Are the core entities implied by the requirements actually present in the code?"},
            {"name": "God-Class / Coupling", "weight": 1.0, "mode": "deterministic",
             "description": "Is responsibility spread reasonably across classes, or does one class do everything?"},
            {"name": "Naming Consistency", "weight": 0.5, "mode": "deterministic",
             "description": "Are class and method names consistent and conventional?"},
            {"name": "Responsibility Assignment", "weight": 1.5, "mode": "llm",
             "description": "Does each class have a single, clear responsibility appropriate to the domain?"},
            {"name": "Extensibility", "weight": 1.5, "mode": "llm",
             "description": "Could a new vehicle type or pricing strategy be added without modifying existing classes?"},
            {"name": "Trade-off Reasoning", "weight": 1.0, "mode": "llm",
             "description": "Does the learner's rationale acknowledge trade-offs (e.g. bus spot allocation) rather than ignoring them?"},
        ],
    },
    {
        "slug": "elevator-system",
        "title": "Elevator System",
        "difficulty": "medium",
        "summary": "Design the control logic for a bank of elevators in a building, "
                   "handling requests efficiently.",
        "requirements": [
            "Support multiple elevators serving the same set of floors.",
            "Handle both hall calls (up/down button on a floor) and car calls (button inside the elevator).",
            "Choose a reasonable elevator to dispatch for a new request.",
            "Track elevator state (idle, moving up, moving down, doors open).",
        ],
        "constraints": [
            "Do not assume a single elevator - the design must generalize to N elevators.",
            "Dispatch strategy should be swappable (e.g. nearest-car vs least-busy) without rewriting the elevator class.",
        ],
        "expected_entities": ["Elevator", "ElevatorController", "Request", "Floor"],
        "criteria": [
            {"name": "Entity & Requirement Coverage", "weight": 1.0, "mode": "deterministic",
             "description": "Are the core entities implied by the requirements present?"},
            {"name": "God-Class / Coupling", "weight": 1.0, "mode": "deterministic",
             "description": "Is dispatch logic separated from individual elevator state, or all in one place?"},
            {"name": "Naming Consistency", "weight": 0.5, "mode": "deterministic",
             "description": "Are class and method names consistent and conventional?"},
            {"name": "State Modeling", "weight": 1.5, "mode": "llm",
             "description": "Is elevator state (idle/moving/doors) modeled clearly, e.g. via a state machine or explicit enum, rather than scattered booleans?"},
            {"name": "Extensibility", "weight": 1.5, "mode": "llm",
             "description": "Can the dispatch strategy be swapped without modifying the Elevator class itself?"},
            {"name": "Trade-off Reasoning", "weight": 1.0, "mode": "llm",
             "description": "Does the rationale discuss why this dispatch strategy was chosen and its downsides?"},
        ],
    },
    {
        "slug": "vending-machine",
        "title": "Vending Machine",
        "difficulty": "easy",
        "summary": "Design a vending machine that accepts payment, dispenses items, and returns change.",
        "requirements": [
            "Track inventory per item slot, including quantity.",
            "Accept payment (assume coins/notes as discrete denominations) and compute change.",
            "Handle the case where the exact change cannot be made.",
            "Model the machine's operational states (idle, has money, dispensing, out of stock).",
        ],
        "constraints": [
            "Do not hardcode item prices in the dispensing logic.",
            "Should support adding a new payment method (e.g. card) later.",
        ],
        "expected_entities": ["VendingMachine", "Inventory", "Item", "Payment"],
        "criteria": [
            {"name": "Entity & Requirement Coverage", "weight": 1.0, "mode": "deterministic",
             "description": "Are the core entities implied by the requirements present?"},
            {"name": "God-Class / Coupling", "weight": 1.0, "mode": "deterministic",
             "description": "Is payment/change logic separated from inventory and dispensing logic?"},
            {"name": "Naming Consistency", "weight": 0.5, "mode": "deterministic",
             "description": "Are class and method names consistent and conventional?"},
            {"name": "State Modeling", "weight": 1.5, "mode": "llm",
             "description": "Are the machine's operational states modeled explicitly and handled correctly, including the failure case (can't make change)?"},
            {"name": "Extensibility", "weight": 1.5, "mode": "llm",
             "description": "Could a new payment method be added without rewriting the core dispensing flow?"},
            {"name": "Trade-off Reasoning", "weight": 1.0, "mode": "llm",
             "description": "Does the rationale address what happens on edge cases like insufficient change or out-of-stock items?"},
        ],
    },
]


def seed(db: Session):
    if db.query(models.Problem).count() > 0:
        return
    for p in PROBLEMS:
        problem = models.Problem(
            slug=p["slug"], title=p["title"], difficulty=p["difficulty"],
            summary=p["summary"], requirements=p["requirements"],
            constraints=p["constraints"], expected_entities=p["expected_entities"],
        )
        db.add(problem)
        db.flush()
        for c in p["criteria"]:
            db.add(models.Criterion(
                problem_id=problem.id, name=c["name"], description=c["description"],
                weight=c["weight"], evaluation_mode=models.EvaluationMode(c["mode"]),
            ))
    db.commit()
