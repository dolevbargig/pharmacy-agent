import sqlite3
import json

def init_database():
    """Initialize the pharmacy database with synthetic data"""
    conn = sqlite3.connect('pharmacy.db')
    cursor = conn.cursor()

    # Create Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        date_of_birth TEXT NOT NULL
    )
    ''')

    # Create Medications table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS medications (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        active_ingredient TEXT NOT NULL,
        dosage TEXT NOT NULL,
        requires_prescription BOOLEAN NOT NULL,
        in_stock BOOLEAN NOT NULL,
        usage_instructions TEXT NOT NULL,
        side_effects TEXT,
        description TEXT NOT NULL,
        category TEXT NOT NULL
    )
    ''')

    # Create Prescriptions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prescriptions (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        medication_id INTEGER NOT NULL,
        prescription_date TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (medication_id) REFERENCES medications(id)
    )
    ''')

    # Insert 10 synthetic users
    users = [
        (1, 'Danny Cohen', 'danny.cohen@email.com', '050-1234567', '1985-03-15'),
        (2, 'Sarah Levi', 'sarah.levi@email.com', '052-2345678', '1990-07-22'),
        (3, 'Joseph Abraham', 'joseph.abraham@email.com', '053-3456789', '1978-11-30'),
        (4, 'Rachel Golan', 'rachel.golan@email.com', '054-4567890', '1995-02-14'),
        (5, 'Michael David', 'michael.david@email.com', '050-5678901', '1982-09-08'),
        (6, 'Anna Katz', 'anna.katz@email.com', '052-6789012', '1988-05-19'),
        (7, 'Eli Shemesh', 'eli.shemesh@email.com', '053-7890123', '1975-12-03'),
        (8, 'Michelle Barak', 'michelle.barak@email.com', '054-8901234', '1992-06-27'),
        (9, 'Ron Peretz', 'ron.peretz@email.com', '050-9012345', '1987-04-11'),
        (10, 'Noa Shapira', 'noa.shapira@email.com', '052-0123456', '1998-10-25')
    ]

    cursor.executemany('INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?)', users)

    # Insert 5 synthetic medications
    medications = [
        (
            1,
            'Acamol',  # Paracetamol
            'Paracetamol',
            '500mg',
            False,  # requires_prescription
            True,   # in_stock
            'Take 1-2 tablets every 4-6 hours. Maximum 8 tablets per day.',
            'Mild headache, rare nausea',
            'Pain reliever and fever reducer. Suitable for headaches, toothaches, and fever.',
            'pain_relief'
        ),
        (
            2,
            'Advil',  # Ibuprofen
            'Ibuprofen',
            '400mg',
            False,  # requires_prescription
            True,   # in_stock
            'Take 1 tablet every 6-8 hours with food. Maximum 3 tablets per day.',
            'Stomach pain, heartburn, rare dizziness',
            'Anti-inflammatory medication for pain, inflammation, and fever.',
            'pain_relief'
        ),
        (
            3,
            'Augmentin',  # Antibiotic
            'Amoxicillin + Clavulanic Acid',
            '875mg/125mg',
            True,   # requires_prescription
            True,   # in_stock
            'Take one tablet twice daily with food for 7-10 days.',
            'Diarrhea, nausea, allergic rash',
            'Antibiotic for treating bacterial infections. Requires prescription.',
            'antibiotic'
        ),
        (
            4,
            'Lipitor',  # Cholesterol
            'Atorvastatin',
            '20mg',
            True,   # requires_prescription
            False,  # in_stock (out of stock for variety)
            'Take one tablet daily, with or without food.',
            'Muscle pain, headache, digestive issues',
            'Cholesterol-lowering medication. Requires prescription and medical monitoring.',
            'cholesterol'
        ),
        (
            5,
            'Benadryl',  # Antihistamine
            'Diphenhydramine',
            '25mg',
            False,  # requires_prescription
            True,   # in_stock
            'Take 1-2 tablets every 4-6 hours. May cause drowsiness.',
            'Drowsiness, dry mouth, dizziness',
            'Antihistamine for allergies, itching, and hives.',
            'allergy'
        )
    ]

    cursor.executemany('''
        INSERT OR REPLACE INTO medications
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', medications)

    # Insert synthetic prescriptions
    # Format: (id, user_id, medication_id, prescription_date)
    prescriptions = [
        # Danny Cohen (user 1) - has prescriptions for Augmentin and Lipitor
        (1, 1, 3, '2024-12-01'),      # Augmentin
        (2, 1, 4, '2024-11-15'),      # Lipitor

        # Sarah Levi (user 2) - has prescription for Augmentin
        (3, 2, 3, '2024-12-10'),      # Augmentin

        # Joseph Abraham (user 3) - has prescription for Lipitor
        (4, 3, 4, '2024-11-20'),      # Lipitor

        # Rachel Golan (user 4) - no prescriptions

        # Michael David (user 5) - has prescription for Augmentin
        (5, 5, 3, '2024-12-05'),      # Augmentin

        # Anna Katz (user 6) - has prescription for Lipitor
        (6, 6, 4, '2024-10-30'),      # Lipitor

        # Eli Shemesh (user 7) - no prescriptions
        # Michelle Barak (user 8) - no prescriptions
        # Ron Peretz (user 9) - no prescriptions
        # Noa Shapira (user 10) - no prescriptions
    ]

    cursor.executemany('''
        INSERT OR REPLACE INTO prescriptions
        VALUES (?, ?, ?, ?)
    ''', prescriptions)

    conn.commit()
    conn.close()

    print("✅ Database initialized successfully!")
    print(f"   - Created 10 users")
    print(f"   - Created 5 medications")
    print(f"   - Created 6 prescriptions")

if __name__ == '__main__':
    init_database()
