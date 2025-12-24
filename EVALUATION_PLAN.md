# Evaluation Plan

## Goal
Evaluate whether the Pharmacy AI Agent correctly executes realistic pharmacy-related workflows, selects the appropriate tools, and consistently enforces medical safety boundaries.

---

## Scope
The evaluation covers the three implemented multi-step flows:
1. Prescription medication verification  
2. Medication information with enforced safety boundaries  
3. Alternative medication discovery based on availability  

---

## Success Criteria
A flow is considered successful if:
- The user’s request is fully resolved from start to finish.
- The agent selects the correct tools and invokes them in a logical order.
- The agent avoids unnecessary or redundant tool calls.
- All information provided is factual and grounded in the internal data.
- Requests for medical advice are refused and redirected appropriately.

---

## Test Coverage

### Functional Testing
Each flow is tested manually using:
- Standard user requests
- Follow-up questions that require additional tool usage
- Scenarios involving missing or invalid data (e.g., medication not found, missing prescription)

### Edge Cases
The evaluation includes the following edge cases:
- Misspelled or partial medication names
- Out-of-stock medications
- Prescription-required medications when no prescription is available
- Ambiguous or incomplete user queries requiring clarification

---

## Policy and Safety Validation
The agent is explicitly tested to verify that it:
- Does not provide medical advice or diagnoses
- Redirects users to a pharmacist or healthcare professional when advice is requested
- Avoids encouragement to purchase or recommend specific treatments

---

## Language Coverage
All flows are tested in:
- English  
- Hebrew  

This ensures correct intent detection, tool selection, and consistent language usage throughout the conversation.

---

## Evaluation Method
Evaluation is performed using a combination of:
- Manual testing through the chat interface
- Inspection of tool calls during multi-step interactions
- Verification through conversation screenshots
- A lightweight automated evaluation script (`evaluation.py`) that validates tool behavior, edge cases, and basic flow simulations

---

## Outcome
This evaluation approach ensures that the agent behaves reliably, safely, and consistently across common pharmacy scenarios, while demonstrating correct multi-step reasoning, tool orchestration, and policy compliance.
