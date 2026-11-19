# Test passages

All passages are public text. No personal or confidential data is used.

| ID | Article | Language | Competency label used | Licence |
|----|---------|----------|-----------------------|---------|
| P1_rti | Right to Information Act, 2005 | English | Domain: Right to Information | CC BY-SA 4.0 |
| P2_gem | Government e Marketplace | English | Functional: Public Procurement | CC BY-SA 4.0 |
| P3_cvc | Central Vigilance Commission | English | Functional: Vigilance and Ethics | CC BY-SA 4.0 |
| P4_sbm | Swachh Bharat Mission | English | Domain: Sanitation Programmes | CC BY-SA 4.0 |
| P5_digital_india | Digital India | English | Domain: e-Governance | CC BY-SA 4.0 |
| P6_rti_hindi | सूचना का अधिकार (Right to Information) | Hindi | Domain: Right to Information | CC BY-SA 4.0 |

Each JSON file stores the exact Wikipedia revision (`source`), so the same input can be fetched again.
Passages are the article introduction, cut to at most ~1800 characters at a sentence end.

The competency labels are the project's own, grouped as Behavioural / Functional / Domain. They are
not copied from an official iGOT Karmayogi competency dictionary (still to be verified, see the
Milestone 2 PDF, Section 4, limitations).

Edge-case and invalid inputs (very short text, injected instructions, empty text, etc.) are defined
in `test-data/cases/test_cases.json`. Where a case changes a real passage, that is stated in the case.
