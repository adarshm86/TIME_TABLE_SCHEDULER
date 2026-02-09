import random

# Define days
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

# Define subjects and their theory classes with faculty
theory_requirements = [
    ('OS', 'Dr. Preya', 3),
    ('DDCO', 'Prof. Santhosh', 3),
    ('DSA', 'Dr. Padma Reddy', 3),
    ('MATH', 'Raghu', 4),
    ('EVS', 'Prof. Muttu', 1),
    ('UHV', 'Prof. Deepa', 1),
    ('JAVA', 'Prof. Swathi', 2),
]

# Define lab sessions with faculty
lab_requirements = [
    ('OS Lab', 'Dr. Preya'),
    ('DDCO Lab', 'Prof. Santhosh'),
    ('DSA Lab', 'David'),
    ('JAVA Lab', 'Prof. Swathi'),
]

# Function to generate timetable for a batch
def generate_timetable(batch_name):
    timetable = {day: [] for day in days}
    faculty_sched = {day: {i: set() for i in range(7)} for day in days}
    
    # Step 1: Decide number of slots per day (4 to 7)
    for day in days:
        num_slots = random.randint(4, 7)
        timetable[day] = [None] * num_slots
    
    # Step 2: Assign lab positions (2 consecutive slots, no crossing lunch, one per block)
    lab_positions = {day: [] for day in days}
    for lab in lab_requirements:
        placed = False
        attempts = 0
        while not placed and attempts < 100:
            day = random.choice(days)
            slots = timetable[day]
            n = len(slots)
            possible = []
            # Morning positions (1-4, not crossing lunch)
            if n >= 4:
                for start in range(3):  # 0-1, 1-2, 2-3
                    if start + 1 < 4:
                        possible.append((start, start + 1))
            # Afternoon positions (5-7)
            if n > 4:
                for start in range(4, n - 1):
                    possible.append((start, start + 1))
            # Filter: only one lab per block
            existing = lab_positions[day]
            morning_has = any(p[0] < 4 for p in existing)
            afternoon_has = any(p[0] >= 4 for p in existing)
            filtered = [p for p in possible if (p[0] < 4 and not morning_has) or (p[0] >= 4 and not afternoon_has)]
            if filtered:
                pos = random.choice(filtered)
                lab_positions[day].append(pos)
                timetable[day][pos[0]] = lab
                timetable[day][pos[1]] = lab
                faculty_sched[day][pos[0]].add(lab[1])
                faculty_sched[day][pos[1]].add(lab[1])
                placed = True
            attempts += 1
    
    # Step 3: Prepare theory list
    theory_list = []
    for sub, fac, count in theory_requirements:
        theory_list.extend([(sub, fac)] * count)
    random.shuffle(theory_list)
    
    # Step 4: Assign theory classes
    for th in theory_list:
        placed = False
        attempts = 0
        while not placed and attempts < 100:
            day = random.choice(days)
            slots = timetable[day]
            n = len(slots)
            possible_slots = [i for i in range(n) if slots[i] is None]
            if not possible_slots:
                attempts += 1
                continue
            for i in possible_slots:
                # Check faculty conflict
                if th[1] in faculty_sched[day][i]:
                    continue
                # Check no same subject consecutive
                prev_sub = slots[i-1][0] if i > 0 and slots[i-1] else None
                next_sub = slots[i+1][0] if i + 1 < n and slots[i+1] else None
                if prev_sub == th[0] or next_sub == th[0]:
                    continue
                # Check max 2 consecutive theory classes
                # Count theory streaks left and right
                left_theory = 0
                j = i - 1
                while j >= 0 and slots[j] and 'Lab' not in slots[j][0]:
                    left_theory += 1
                    j -= 1
                right_theory = 0
                j = i + 1
                while j < n and slots[j] and 'Lab' not in slots[j][0]:
                    right_theory += 1
                    j += 1
                if left_theory + right_theory + 1 > 2:
                    continue
                # Place
                slots[i] = th
                faculty_sched[day][i].add(th[1])
                placed = True
                break
            attempts += 1
    
    # Step 5: Print timetable
    print(f"\nTimetable for {batch_name}:")
    for day in days:
        print(f"{day}:")
        slots = timetable[day]
        for i, slot in enumerate(slots):
            slot_num = i + 1
            if slot:
                print(f"  Slot {slot_num}: {slot[0]} - {slot[1]}")
            else:
                print(f"  Slot {slot_num}: Free")
        print("  (Lunch after Slot 4)")

# Generate for both batches (assuming same structure)
generate_timetable("ISEA")
generate_timetable("ISEB")