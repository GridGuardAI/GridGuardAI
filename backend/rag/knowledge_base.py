KNOWLEDGE_BASE = [
    {
        "text": "A power factor below 0.90 typically indicates inductive loads such as "
                "motors, pumps, or transformers operating inefficiently, often due to "
                "aging equipment or the absence of power factor correction capacitors.",
        "source": "GridGuard Technical Reference - Power Factor Fundamentals",
    },
    {
        "text": "Voltage deviations beyond a utility's regulated band (commonly a few "
                "percent around nominal, e.g. 230V +/-5-10% for many distribution systems) "
                "may indicate local grid stress, transformer issues, or heavy nearby loads.",
        "source": "GridGuard Technical Reference - Voltage Regulation Basics",
    },
    {
        "text": "A significant unexplained rise in monthly consumption (commonly screened "
                "above ~20-40% change) warrants investigating new/added loads, increased "
                "operating hours, seasonal effects (e.g. AC/heating), or a meter/billing "
                "discrepancy before concluding equipment is faulty.",
        "source": "GridGuard Technical Reference - Consumption Anomaly Screening",
    },
    {
        "text": "Improving power factor toward 0.95-1.0 using correctly sized capacitor "
                "banks can reduce reactive-power-related charges on some commercial/"
                "industrial tariffs, though the exact saving depends on the utility's "
                "specific tariff structure.",
        "source": "GridGuard Technical Reference - PF Correction Guidance",
    },
    {
        "text": "Increased operating hours for existing equipment is a common and often "
                "benign explanation for increased energy use (e.g. more work shifts, "
                "hotter weather driving longer AC run-time) and should be checked before "
                "assuming a fault.",
        "source": "GridGuard Technical Reference - Operating-Hour Analysis",
    },
    {
        "text": "Repeated voltage fluctuations outside the normal band over time can "
                "accelerate wear on sensitive electronic equipment and shorten the "
                "lifespan of motors, transformers, and compressors.",
        "source": "GridGuard Technical Reference - Equipment Wear & Voltage Quality",
    },
    {
        "text": "A large mismatch between a modeled/estimated load-based energy figure and "
                "the actual billed consumption can result from missing appliances in the "
                "model, incorrect operating-hour assumptions, or a meter/billing data issue "
                "- it is a data/model mismatch flag, not proof of equipment fault.",
        "source": "GridGuard Technical Reference - Load Modeling Notes",
    },
    {
        "text": "Regular load audits and periodic inspection of major appliances help "
                "catch developing electrical inefficiencies (like declining power factor "
                "or rising baseline load) before they show up as a large bill increase.",
        "source": "GridGuard Technical Reference - Preventive Energy Audits",
    },

    # --- Real NEPRA regulatory references (Consumer Service Manual, Revised 2025) ---
    # Paraphrased from the official document, not quoted verbatim. Full text:
    # https://nepra.org.pk/Legislation/7-Manuals/2025/CONSUMER%20SERVICE%20MANUAL%20(CSM)%20REVISED%202025.pdf

    {
        "text": "Under NEPRA's regulatory definitions, power factor for billing purposes "
                "is calculated as the ratio of energy consumed (kWh) to apparent energy "
                "(kVAh) over the billing month - the same relationship used in this "
                "system's real/apparent power calculations.",
        "source": "NEPRA Consumer Service Manual, Revised 2025 - Chapter 1 (Definitions), item 53",
    },
    {
        "text": "Penalties for low power factor are not fixed in the general Consumer "
                "Service Manual - they are set in the 'Terms and Conditions' of the "
                "specific tariff category approved by NEPRA, so the exact penalty (if "
                "any) depends on the consumer's tariff category and must be verified "
                "against that schedule rather than assumed.",
        "source": "NEPRA Consumer Service Manual, Revised 2025 - Chapter 7 (Tariff), Section 7.3",
    },
    {
        "text": "If a consumer's meter is confirmed defective, NEPRA rules require the "
                "utility to bill on an average basis - the higher of the same month's "
                "consumption from the previous year or the average of the last eleven "
                "months - for up to two billing cycles until the meter is replaced. This "
                "means a large one-off consumption jump can sometimes reflect a metering "
                "issue rather than an electrical fault.",
        "source": "NEPRA Consumer Service Manual, Revised 2025 - Chapter 4 (Metering), Section 4.3",
    },
    {
        "text": "A consumer who doubts their meter's accuracy can request the utility (or "
                "escalate to NEPRA's Provincial Office of Inspection) to test it against a "
                "calibrated check meter; if the meter is found to be running fast, the "
                "utility must credit excess billed units for up to two previous billing "
                "cycles.",
        "source": "NEPRA Consumer Service Manual, Revised 2025 - Chapter 4 (Metering), Section 4.3",
    },
    {
        "text": "Using an electricity connection for a purpose other than what it was "
                "sanctioned for (for example running a business on a residential tariff) "
                "is classed as tariff misuse; the utility may retroactively bill the "
                "tariff difference, but without documented proof this back-charge is "
                "limited to a couple of billing cycles.",
        "source": "NEPRA Consumer Service Manual, Revised 2025 - Chapter 7 (Tariff), Section 7.5",
    },
    {
        "text": "Every electricity bill in Pakistan is required to show 12 months of "
                "billing history alongside the present and previous meter readings, so a "
                "consumer can independently verify their own month-to-month consumption "
                "trend rather than relying on a single reading.",
        "source": "NEPRA Consumer Service Manual, Revised 2025 - Chapter 6 (Meter Reading & Billing), Section 6.4",
    },
    {
        "text": "Bills are due within 15 days of the issue date, or 7 days from actual "
                "delivery if later; paying after this window triggers a Late Payment "
                "Surcharge on top of the electricity charges themselves.",
        "source": "NEPRA Consumer Service Manual, Revised 2025 - Chapter 6 (Meter Reading & Billing), Section 6.5",
    },
]
