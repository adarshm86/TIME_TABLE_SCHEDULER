import random
from collections import defaultdict, namedtuple

# ---------- CONFIG ----------
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
DAY_SLOTS = {d: 7 for d in DAYS}

MIN_SLOTS_PER_DAY = 5   # IMPORTANT for feasibility
MAX_SLOTS_PER_DAY = 7

MAX_ATTEMPTS = 5000
RANDOM_SEED = 42

# ---------- CORE CLASSES ----------
class Faculty:
    def __init__(self, faculty_id, name):
        self.id = faculty_id
        self.name = name
        self.schedule = {}  # (day, slot) -> (batch_id, subject_label)

    def is_free(self, day, slot):
        return (day, slot) not in self.schedule

    def assign(self, day, slot, batch_id, subject_label):
        self.schedule[(day, slot)] = (batch_id, subject_label)

    def clear(self):
        self.schedule.clear()


class Subject:
    def __init__(self, subject_id, name, credits, faculty, has_lab=False):
        self.id = subject_id
        self.name = name
        self.credits = credits
        self.faculty = faculty
        self.has_lab = has_lab

        # RULE: credits = theory hours
        self.theory_slots = credits
        self.lab_sessions = 1 if has_lab else 0
        self.lab_slots = 2 if has_lab else 0

    def total_slots(self):
        return self.theory_slots + self.lab_slots


class Batch:
    def __init__(self, batch_id):
        self.id = batch_id
        self.schedule = {}  # (day, slot) -> subject_label

    def is_free(self, day, slot):
        return (day, slot) not in self.schedule

    def assign(self, day, slot, subject_label):
        self.schedule[(day, slot)] = subject_label

    def clear(self):
        self.schedule.clear()


Unit = namedtuple("Unit", ["batch", "subject", "kind"])  # kind: theory / lab

# ---------- SCHEDULER ----------
class Scheduler:
    def __init__(self, assignments, lab_faculty_override=None):
        self.assignments = assignments
        self.lab_faculty_override = lab_faculty_override or {}

        self.batches = sorted({a[0] for a in assignments}, key=lambda b: b.id)
        self.faculties = sorted({a[1].faculty for a in assignments}, key=lambda f: f.id)

        for f in self.lab_faculty_override.values():
            if f not in self.faculties:
                self.faculties.append(f)

    def generate(self):
        if RANDOM_SEED is not None:
            random.seed(RANDOM_SEED)

        # Build units
        batch_units = defaultdict(list)
        for batch, subject in self.assignments:
            for _ in range(subject.theory_slots):
                batch_units[batch].append(Unit(batch, subject, "theory"))
            for _ in range(subject.lab_sessions):
                batch_units[batch].append(Unit(batch, subject, "lab"))

        for attempt in range(1, MAX_ATTEMPTS + 1):
            for b in self.batches:
                b.clear()
            for f in self.faculties:
                f.clear()

            # Allocate per-day load
            remaining_slots = {}
            for batch, units in batch_units.items():
                total = sum(2 if u.kind == "lab" else 1 for u in units)
                allocation = self._distribute_slots(total)
                if allocation is None:
                    break
                remaining_slots[batch] = allocation
            else:
                # Shuffle units, labs first
                all_units = []
                for units in batch_units.values():
                    random.shuffle(units)
                    all_units.extend(units)

                random.shuffle(all_units)
                all_units.sort(key=lambda u: 0 if u.kind == "lab" else 1)

                success = True
                for unit in all_units:
                    placed = False
                    days = [d for d in DAYS if remaining_slots[unit.batch][d] > 0]
                    random.shuffle(days)

                    for day in days:
                        for slot in range(1, DAY_SLOTS[day] + 1):
                            if unit.kind == "lab":
                                if slot + 1 > DAY_SLOTS[day]:
                                    continue
                                if remaining_slots[unit.batch][day] < 2:
                                    continue
                            faculty = (
                                self.lab_faculty_override.get(
                                    unit.subject.name, unit.subject.faculty
                                )
                                if unit.kind == "lab"
                                else unit.subject.faculty
                            )
                            if not self._can_place(unit, day, slot, faculty):
                                continue

                            self._place(unit, day, slot, faculty)
                            remaining_slots[unit.batch][day] -= 2 if unit.kind == "lab" else 1
                            placed = True
                            break
                        if placed:
                            break

                    if not placed:
                        success = False
                        break

                if success and all(
                    all(v == 0 for v in remaining_slots[b].values())
                    for b in remaining_slots
                ):
                    return

        raise Exception("Failed to generate timetable")

    def _distribute_slots(self, total):
        min_total = MIN_SLOTS_PER_DAY * len(DAYS)
        max_total = MAX_SLOTS_PER_DAY * len(DAYS)
        if not (min_total <= total <= max_total):
            return None

        allocation = {d: MIN_SLOTS_PER_DAY for d in DAYS}
        remaining = total - min_total

        for d in DAYS:
            if remaining <= 0:
                break
            can_add = MAX_SLOTS_PER_DAY - allocation[d]
            add = min(can_add, remaining)
            allocation[d] += add
            remaining -= add

        return allocation if remaining == 0 else None

    def _can_place(self, unit, day, slot, faculty):
        b = unit.batch
        s = unit.subject

        if unit.kind == "theory":
            return b.is_free(day, slot) and s.faculty.is_free(day, slot)

        # lab
        return (
            b.is_free(day, slot)
            and b.is_free(day, slot + 1)
            and faculty.is_free(day, slot)
            and faculty.is_free(day, slot + 1)
        )

    def _place(self, unit, day, slot, faculty):
        b = unit.batch
        s = unit.subject

        if unit.kind == "theory":
            b.assign(day, slot, s.name)
            s.faculty.assign(day, slot, b.id, s.name)
        else:
            label = s.name + " Lab"
            b.assign(day, slot, label)
            b.assign(day, slot + 1, label)
            faculty.assign(day, slot, b.id, label)
            faculty.assign(day, slot + 1, b.id, label)

# ---------- PRINT ----------
def print_timetable(batch):
    print(f"\nTimetable for {batch.id}")
    for day in DAYS:
        print(day, ":", end=" ")
        for s in range(1, DAY_SLOTS[day] + 1):
            print(batch.schedule.get((day, s), "-"), end=" | ")
        print()

# ---------- DATA ----------
f_preya = Faculty(1, "Dr. Preya")
f_santhosh = Faculty(2, "Prof. Santhosh")
f_padma = Faculty(3, "Dr. Padma")
f_david = Faculty(4, "David")
f_raghu = Faculty(5, "Raghu")
f_muttu = Faculty(6, "Prof. Muttu")
f_deepa = Faculty(7, "Prof. Deepa")
f_swathi = Faculty(8, "Prof. Swathi")

os = Subject(1, "OS", 4, f_preya, True)
ddco = Subject(2, "DDCO", 4, f_santhosh, True)
dsa = Subject(3, "DSA", 4, f_padma, True)
math = Subject(4, "Math", 4, f_raghu)
evs = Subject(5, "EVS", 1, f_muttu)
uhv = Subject(6, "UHV", 1, f_deepa)
java = Subject(7, "JAVA", 3, f_swathi, True)

isea = Batch("ISE-A")
iseb = Batch("ISE-B")

assignments = [
    (isea, os), (isea, ddco), (isea, dsa), (isea, math), (isea, evs), (isea, uhv), (isea, java),
    (iseb, os), (iseb, ddco), (iseb, dsa), (iseb, math), (iseb, evs), (iseb, uhv), (iseb, java),
]

scheduler = Scheduler(assignments, lab_faculty_override={"DSA": f_david})
scheduler.generate()

print_timetable(isea)
print_timetable(iseb)
