"""4S PLUS domain catalog. Facts here are verified from the live system and
Ahmed's own walkthrough (2026-10-17), not invented marketing copy.

Two audiences, always kept separate:
  prospecting      Vo Technology selling 4S PLUS to dealers and workshops (B2B)
  dealer_marketing a dealer using 4S PLUS data to retain car owners (B2C)
"""

PRODUCT_PILLARS = {
    "sales": {
        "name": "Sales",
        "facts": [
            "Vehicle inventory tracked by model, color, chassis number, and status",
            "A sold car carries its chassis number into Service, so its full history follows it",
        ],
        "owner": "Ahmed Fouad (cars module)",
    },
    "spare_parts": {
        "name": "Spare Parts",
        "facts": [
            "Service raises material requests from the JobCard Parts tab (Create Requests)",
            "Parts confirms and issues, stock drops instantly",
            "Parts can be loaded in bulk from Excel",
        ],
        "owner": "Hazem (spare parts module)",
    },
    "service": {
        "name": "Service",
        "facts": [
            "JobCard lifecycle: W.I.P (work in progress) then Ready for invoicing",
            "Operations track Actual hours versus Sold hours, sold rate, and net per operation",
            "Menus include Service Packages, Periodic Maintenance Service, Appointments, QC CheckList, Job Types, Shops, Discount On Labour and Parts, Follow Customer",
            "Opening a JobCard auto fills vehicle data from the chassis linked master record",
        ],
        "owner": "Ahmed Gamal (maintenance and service module)",
    },
    "survey": {
        "name": "Survey",
        "facts": [
            "Customer satisfaction is surveyed after service delivery",
            "Follow Customer is a built in Service menu, so follow up is part of the workflow, not an afterthought",
        ],
        "owner": "Part of the 4S product pillars",
    },
}

ADJACENT_MODULES = {
    "crm": {
        "name": "CRM",
        "facts": [
            "Customer files, follow ups, reminders, and marketing live here",
            "The CRM customer is the same person who owns the JobCards",
            "AI layer adds lead scoring, follow up automation, and predictive insights (Shahd's CRM automation deck)",
        ],
        "owner": "Shahd (CRM module)",
    },
    "accounting": {
        "name": "Accounting",
        "facts": [
            "Actual versus Sold hours per JobCard feed per card profitability",
            "Invoices are produced when a JobCard becomes Ready for invoicing",
        ],
        "owner": "Ibrahim (accounting module)",
    },
}

# The signature story: one car, one chassis number, every module.
ONE_CAR_JOURNEY = [
    ("sales", "Car is sold, chassis number recorded"),
    ("service", "Car returns for maintenance, JobCard opens with full history and warranty check"),
    ("spare_parts", "Parts are requested from the JobCard and issued from stock"),
    ("accounting", "JobCard closes Ready for invoicing, profitability is known per card"),
    ("crm", "Satisfaction survey goes out, predictive maintenance alert schedules the next visit"),
    ("survey", "Feedback returns and feeds the next campaign"),
]

PROSPECT_PERSONAS = [
    {
        "id": "dealer_owner",
        "audience": "prospecting",
        "title": "Dealer or showroom owner",
        "pains": ["Lost customer data", "No clear view of sales and service together", "Follow ups depend on memory"],
        "trigger_moment": "Manual work in spreadsheets starts producing errors and lost follow ups",
        "decision_role": "Pays and decides",
    },
    {
        "id": "workshop_manager",
        "audience": "prospecting",
        "title": "Workshop or service center manager",
        "pains": ["Cannot see technician efficiency", "JobCards tracked on paper", "Parts shortages stop jobs mid work"],
        "trigger_moment": "Workshop volume grows past what paper and memory can track",
        "decision_role": "Uses daily, influences the decision",
    },
    {
        "id": "parts_trader",
        "audience": "prospecting",
        "title": "Spare parts trader or stock manager",
        "pains": ["Stock levels unclear", "No demand signal from the workshop", "Dead stock ties up cash"],
        "trigger_moment": "Repeated stock outs or a stock count that does not match reality",
        "decision_role": "Uses daily",
    },
]

RETAIL_PERSONAS = [
    {
        "id": "car_owner_due",
        "audience": "dealer_marketing",
        "title": "Car owner due for periodic maintenance",
        "pains": ["Forgets service intervals", "Fears surprise costs", "Loses service history at resale"],
        "trigger_moment": "Months or kilometers since last service pass the interval",
        "decision_role": "Books the appointment",
    },
    {
        "id": "car_owner_detractor",
        "audience": "dealer_marketing",
        "title": "Car owner who scored the service low in the survey",
        "pains": ["Feels unheard after a bad visit"],
        "trigger_moment": "Survey score of 6 or less after delivery",
        "decision_role": "Recovery target, human call first, never an automated offer first",
    },
]

CONTENT_PILLARS = [
    {"id": "one_car_journey", "name": "One Car Journey", "angle": "Follow one chassis number across Sales, Service, Parts, Accounting, CRM, and Survey"},
    {"id": "workshop_efficiency", "name": "Workshop Efficiency", "angle": "Actual versus Sold hours, QC checklist, and JobCard lifecycle discipline"},
    {"id": "parts_without_shortage", "name": "Parts Without Shortage", "angle": "Create Requests to Issues flow, stock that drops instantly, demand signals"},
    {"id": "trust_and_survey", "name": "Trust and Survey", "angle": "Follow Customer, satisfaction surveys, and service history that protects resale value"},
    {"id": "ai_over_erp", "name": "AI Over the ERP", "angle": "Lead scoring, predictive maintenance alerts, and automated follow ups on top of 4S PLUS data"},
]

# Claims the agent must never make (guardrail source of truth).
PROHIBITED_CLAIMS = [
    "guaranteed results",
    "guarantee",
    "نتائج مضمونة",
    "بنضمن",
    "best in egypt",
    "number one",
    "الأفضل في مصر",
    "رقم واحد",
    "free forever",
    "مجانا للأبد",
]
