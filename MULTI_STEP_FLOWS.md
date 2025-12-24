# Multi-Step Workflow Demonstrations

This document describes three distinct multi-step workflows that the Pharmacy AI Agent can execute. Each flow represents a complete customer interaction from initial request to resolution.

---

## Flow 1: Prescription Medication Purchase Verification

**Goal:** 
verify whether a customer can purchase a prescription medication .

**Steps:**
1.User asks about purchasing a medication.
2.agent identifies the medication and check whether it requires a prescripition.
3.agent calls 'check presctiption(user_id,medication_name)'.
4.if a valid prescription exists, agent calls 'check medication_stock(medication_name)'.
5.agent provides a final response combining prescription status and stock availability.

**Variations:**
- no prescription -> inform the user that a prescription is required and redirect a doctor.
-out of stock -> notify the user and suggest pharmacist follow-up.
- over-the-counter medication -> skip presctiption check and confirm availabilty.

---

## Flow 2: Medication Information and Safety Boundaries


**Goal:** provide factual information about medication while enforcing medical safety boundaries.

**Steps:**
1. user asks for information about a specific medication.
2. agent identifies the medication and calls `get_medication_by_name(medication_name)`.
3. agent summarizes factual details (usage, side effects, prescription status).
4. if the user asks about availability, agent calls `check_medication_stock(medication_name)`.
5. if the user asks for medical advice, agent refuses and redirects to a healthcare professional.

**Variations:**
- Medication not found → prompt user to check spelling or suggest alternatives.
- Prescription medication → clearly state prescription requirement.
- Medical advice request → refuse and redirect to pharmacist or doctor.


---

## Flow 3: Alternative Medication Discovery

**Goal:** Help a user discover suitable over-the-counter pain relief options without knowing specific medication names.

**Steps:**
1. User describes a symptom (e.g., headache) without mentioning a medication.
2. Agent identifies the relevant category and calls `search_medications(filter_type="category", query)`.
3. Agent presents available options in that category.
4. If the user asks for differences, agent retrieves details using `get_medication_by_name(medication_name)` for comparison.
5. If the user selects a medication, agent calls `check_medication_stock(medication_name)` and confirms availability.

**Variations:**
- Search by active ingredient → use `search_medications(filter_type="ingredient", query)`.
- Selected medication out of stock → suggest available alternatives.
- Request for full catalog → use `search_medications(filter_type="all")`.
- Medical advice request → refuse and redirect to pharmacist or doctor.

---

