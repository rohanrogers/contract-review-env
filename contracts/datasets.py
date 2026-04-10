"""
Contract datasets with increasing complexity and ambiguity
"""

from server.environment import ContractClause, RiskType


EASY_CONTRACTS = [
    {
        "contract_id": "EASY_001",
        "difficulty": "easy",
        "clauses": [
            ContractClause(
                id="E1_C1",
                text="The Client shall pay the Contractor a monthly fee of $5,000 for services rendered under this Agreement.",
                risks=[],
                severity=0.0,
                business_value=0.9
            ),
            ContractClause(
                id="E1_C2",
                text="This Agreement shall automatically renew for successive one-year terms unless either party provides written notice of termination at least 90 days prior to the end of the current term.",
                risks=[RiskType.AUTO_RENEWAL],
                severity=0.6,
                business_value=0.5
            ),
            ContractClause(
                id="E1_C3",
                text="The Contractor agrees to maintain confidentiality of all Client information disclosed during the term of this Agreement.",
                risks=[],
                severity=0.0,
                business_value=0.7
            ),
            ContractClause(
                id="E1_C4",
                text="The Contractor shall be liable for any and all damages arising from services provided, without limitation as to amount or scope.",
                risks=[RiskType.UNLIMITED_LIABILITY],
                severity=0.9,
                business_value=0.3
            ),
            ContractClause(
                id="E1_C5",
                text="Either party may terminate this Agreement with 30 days written notice.",
                risks=[],
                severity=0.0,
                business_value=0.8
            ),
        ]
    },
    {
        "contract_id": "EASY_002",
        "difficulty": "easy",
        "clauses": [
            ContractClause(
                id="E2_C1",
                text="Services will be provided on a time-and-materials basis at the rates specified in Exhibit A.",
                risks=[],
                severity=0.0,
                business_value=0.8
            ),
            ContractClause(
                id="E2_C2",
                text="The Contractor shall not provide similar services to any competitor of Client during the term and for 24 months thereafter.",
                risks=[RiskType.EXCLUSIVITY, RiskType.NON_COMPETE],
                severity=0.7,
                business_value=0.4
            ),
            ContractClause(
                id="E2_C3",
                text="All intellectual property created by Contractor in the course of providing services shall become the exclusive property of Client.",
                risks=[RiskType.IP_TRANSFER],
                severity=0.6,
                business_value=0.5
            ),
            ContractClause(
                id="E2_C4",
                text="This Agreement is governed by the laws of Delaware.",
                risks=[],
                severity=0.1,
                business_value=0.6
            ),
        ]
    }
]


MEDIUM_CONTRACTS = [
    {
        "contract_id": "MEDIUM_001",
        "difficulty": "medium",
        "clauses": [
            ContractClause(
                id="M1_C1",
                text="Compensation shall be structured as a base fee plus performance bonuses, with quarterly true-up adjustments subject to Client's sole discretion.",
                risks=[],
                severity=0.2,
                business_value=0.7
            ),
            ContractClause(
                id="M1_C2",
                text="This Agreement shall continue in successive terms of equal duration unless terminated by either party; provided that Client may terminate immediately for convenience with written notice, while Contractor must provide 180 days advance notice.",
                risks=[RiskType.UNILATERAL_TERMINATION, RiskType.AUTO_RENEWAL],
                severity=0.8,
                business_value=0.4
            ),
            ContractClause(
                id="M1_C3",
                text="Contractor shall indemnify, defend and hold harmless Client, its affiliates, officers, directors, employees and agents from and against any and all claims, damages, losses, and expenses (including reasonable attorneys' fees) arising out of or relating to the performance or non-performance of services hereunder.",
                risks=[RiskType.INDEMNIFICATION],
                severity=0.7,
                business_value=0.5
            ),
            ContractClause(
                id="M1_C4",
                text="Contractor acknowledges that Client's business methods, customer lists, pricing strategies, and operational data constitute confidential and proprietary information, and agrees not to disclose such information to any third party or use it for any purpose other than performance of this Agreement.",
                risks=[RiskType.CONFIDENTIALITY],
                severity=0.5,
                business_value=0.6
            ),
            ContractClause(
                id="M1_C5",
                text="Any failure by Contractor to meet the service level targets specified in Exhibit B shall result in liquidated damages of $10,000 per incident, with no cap on total liability.",
                risks=[RiskType.PENALTY_CLAUSE, RiskType.UNLIMITED_LIABILITY],
                severity=0.9,
                business_value=0.3
            ),
            ContractClause(
                id="M1_C6",
                text="All work product, inventions, discoveries, improvements, and intellectual property of any kind conceived or developed by Contractor, whether alone or jointly with others, during the term of engagement shall be deemed works made for hire and shall vest exclusively in Client.",
                risks=[RiskType.IP_TRANSFER],
                severity=0.6,
                business_value=0.5
            ),
        ]
    },
    {
        "contract_id": "MEDIUM_002",
        "difficulty": "medium",
        "clauses": [
            ContractClause(
                id="M2_C1",
                text="Contractor warrants that it has full authority to enter this Agreement and that its performance will not violate any other agreement or obligation.",
                risks=[],
                severity=0.1,
                business_value=0.7
            ),
            ContractClause(
                id="M2_C2",
                text="During the term hereof and for a period of thirty-six (36) months thereafter, Contractor shall not, directly or indirectly, solicit, employ, or engage any employee or contractor of Client or its affiliates.",
                risks=[RiskType.NON_COMPETE],
                severity=0.8,
                business_value=0.3
            ),
            ContractClause(
                id="M2_C3",
                text="Any dispute arising under this Agreement shall be resolved exclusively by the courts of Singapore, and Contractor hereby irrevocably consents to the jurisdiction of such courts and waives any objection to venue.",
                risks=[RiskType.JURISDICTION],
                severity=0.7,
                business_value=0.4
            ),
            ContractClause(
                id="M2_C4",
                text="In the event of any breach by Contractor, Client shall be entitled to seek injunctive relief without the necessity of posting bond, in addition to all other remedies available at law or in equity.",
                risks=[],
                severity=0.3,
                business_value=0.6
            ),
            ContractClause(
                id="M2_C5",
                text="Contractor's liability for any claim shall be limited to the fees paid in the six months preceding the claim, except where such limitation is prohibited by law.",
                risks=[],
                severity=0.1,
                business_value=0.8
            ),
        ]
    }
]


HARD_CONTRACTS = [
    {
        "contract_id": "HARD_001",
        "difficulty": "hard",
        "clauses": [
            ContractClause(
                id="H1_C1",
                text="Payment terms shall be net-90 from invoice date, subject to Client's standard procurement review cycle and approval process, which may extend the payment period; provided that Client reserves the right to offset any amounts owed against any claims or disputed charges.",
                risks=[],
                severity=0.1,
                business_value=0.9
            ),
            ContractClause(
                id="H1_C2",
                text="The initial term shall be three years with automatic renewal for successive one-year periods unless either party provides 90 days written notice. This contract governs the exclusive $2.4M annual enterprise platform license, and all revenue commitments, SLA guarantees, and dedicated support tiers are contingent upon this renewal structure remaining intact.",
                risks=[RiskType.AUTO_RENEWAL],
                severity=0.5,
                business_value=0.85
            ),
            ContractClause(
                id="H1_C3",
                text="Contractor shall defend, indemnify, and hold harmless Client and its affiliates from any and all losses, claims, damages, liabilities, costs and expenses (including attorneys' fees) arising from or relating to: (a) services performed hereunder; (b) infringement of third-party IP rights; or (c) breach of any representation or warranty. This indemnification is a core condition of the strategic partnership and underpins Client's commitment to co-develop and co-market joint solutions worth an estimated $8M in pipeline revenue.",
                risks=[RiskType.INDEMNIFICATION, RiskType.UNLIMITED_LIABILITY],
                severity=0.9,
                business_value=0.8
            ),
            ContractClause(
                id="H1_C4",
                text="Contractor acknowledges that during the engagement it may access Confidential Information, defined broadly to include any business, technical, financial, or strategic information. Contractor agrees to protect such information using reasonable care and shall not disclose it to third parties or use it for any purpose except as strictly necessary for performance hereunder.",
                risks=[RiskType.CONFIDENTIALITY],
                severity=0.6,
                business_value=0.5
            ),
            ContractClause(
                id="H1_C5",
                text="Contractor agrees that all Deliverables shall constitute works made for hire; to the extent any Deliverable does not so qualify, Contractor irrevocably assigns to Client all right, title, and interest. In exchange, Client grants Contractor a perpetual, royalty-free license to use derivative methodologies developed during the engagement for future client work, and Contractor retains all rights to its pre-existing IP and tools.",
                risks=[RiskType.IP_TRANSFER],
                severity=0.8,
                business_value=0.7
            ),
            ContractClause(
                id="H1_C6",
                text="Performance standards shall be measured against the service level objectives set forth in Schedule C; failure to achieve such objectives in any calendar month shall be deemed a material breach and shall entitle Client to (i) withhold payment for that month's services, (ii) assess liquidated damages equal to 50% of monthly fees for each performance failure, and (iii) pursue any additional remedies available under this Agreement or at law, all of which shall be cumulative and not alternative.",
                risks=[RiskType.PENALTY_CLAUSE, RiskType.UNLIMITED_LIABILITY],
                severity=0.95,
                business_value=0.2
            ),
            ContractClause(
                id="H1_C7",
                text="During the term and for twenty-four (24) months following termination, Contractor shall not directly compete with Client's core platform business in the enterprise SaaS market. In consideration, Client grants Contractor exclusive preferred-vendor status for all professional services engagements across Client's portfolio companies, representing approximately $1.5M in guaranteed annual revenue.",
                risks=[RiskType.EXCLUSIVITY, RiskType.NON_COMPETE],
                severity=0.85,
                business_value=0.65
            ),
            ContractClause(
                id="H1_C8",
                text="This Agreement shall be governed by and construed in accordance with the laws of the Cayman Islands, without regard to conflicts of law principles; any legal action or proceeding arising hereunder shall be brought exclusively in the courts of George Town, Grand Cayman, and each party irrevocably submits to the jurisdiction of such courts.",
                risks=[RiskType.JURISDICTION],
                severity=0.75,
                business_value=0.3
            ),
            ContractClause(
                id="H1_C9",
                text="Contractor shall process all personal data received from Client strictly in accordance with Client's data processing instructions and applicable data protection laws, including but not limited to GDPR, CCPA, and equivalent local regulations. Contractor shall implement appropriate technical and organizational measures to ensure a level of security appropriate to the risk, and shall notify Client of any data breach within 72 hours. This data processing framework is integral to the $3.2M annual analytics platform license and Client's regulatory compliance obligations.",
                risks=[RiskType.INDEMNIFICATION],
                severity=0.7,
                business_value=0.75
            ),
            ContractClause(
                id="H1_C10",
                text="Neither party shall be liable for any failure or delay in performing its obligations under this Agreement to the extent such failure or delay results from circumstances beyond the reasonable control of the affected party, including but not limited to acts of God, pandemic, epidemic, government actions, war, terrorism, civil disturbance, fire, flood, earthquake, or interruption of essential utilities. The affected party shall provide prompt written notice and use commercially reasonable efforts to mitigate the impact.",
                risks=[],
                severity=0.1,
                business_value=0.6
            ),
            ContractClause(
                id="H1_C11",
                text="In the event of a Change of Control of either party (defined as the acquisition of 50% or more of the voting securities, or a merger, consolidation, or sale of substantially all assets), the non-affected party may, at its sole discretion, terminate this Agreement upon 30 days written notice without penalty or further obligation, notwithstanding any remaining term or outstanding commitments.",
                risks=[RiskType.UNILATERAL_TERMINATION],
                severity=0.65,
                business_value=0.45
            ),
            ContractClause(
                id="H1_C12",
                text="Client shall have the right, upon reasonable prior notice and during normal business hours, to audit Contractor's records, systems, and facilities to verify compliance with the terms of this Agreement, including data protection obligations, service level adherence, and financial billing accuracy. Such audits shall occur no more than twice per calendar year and shall be conducted at Client's expense.",
                risks=[],
                severity=0.15,
                business_value=0.55
            ),
            ContractClause(
                id="H1_C13",
                text="In the event Contractor fails to meet the uptime targets specified in Schedule D (99.95% monthly availability), Client shall be entitled to service level credits calculated as follows: for each 0.1% below the target, a credit of 5% of the monthly service fee shall be applied, up to a maximum of 30% of the monthly fee. Repeated failures (three or more consecutive months below target) shall constitute a material breach entitling Client to terminate with full refund of prepaid fees. These service level commitments underpin a mission-critical $4.1M deployment across Client's global operations.",
                risks=[RiskType.PENALTY_CLAUSE],
                severity=0.6,
                business_value=0.8
            ),
            ContractClause(
                id="H1_C14",
                text="Contractor shall maintain, at its own expense, comprehensive general liability insurance with coverage of not less than $2,000,000 per occurrence and $5,000,000 in aggregate, professional errors and omissions insurance with coverage of not less than $3,000,000, and cyber liability insurance with coverage of not less than $5,000,000. Certificates of insurance shall be provided upon request.",
                risks=[],
                severity=0.05,
                business_value=0.4
            ),
        ]
    }
]


HARD_002_CONTRACT = {
    "contract_id": "HARD_002",
    "difficulty": "hard",
    "clauses": [
        ContractClause(
            id="H2_C1",
            text="Licensor grants to Licensee a non-exclusive, non-transferable, worldwide license to use the Licensed Technology (as defined in Exhibit A) for internal business purposes only, subject to the terms and conditions of this Agreement and the payment of applicable license fees.",
            risks=[],
            severity=0.1,
            business_value=0.9
        ),
        ContractClause(
            id="H2_C2",
            text="The annual license fee shall be $1,800,000, payable in quarterly installments of $450,000. Licensor reserves the right to increase fees by up to 8% annually upon 60 days written notice. All fees are non-refundable once paid.",
            risks=[],
            severity=0.3,
            business_value=0.85
        ),
        ContractClause(
            id="H2_C3",
            text="Licensee acknowledges that the Licensed Technology, including all source code, algorithms, architectures, documentation, and derivative works, constitutes the exclusive intellectual property of Licensor. Licensee shall not reverse engineer, decompile, disassemble, or create derivative works based on the Licensed Technology. Any improvements, modifications, or integrations developed by Licensee using the Licensed Technology shall be jointly owned, with Licensor retaining the right to incorporate such improvements into future product releases.",
            risks=[RiskType.IP_TRANSFER],
            severity=0.8,
            business_value=0.7
        ),
        ContractClause(
            id="H2_C4",
            text="Licensee shall not, directly or indirectly, sublicense, distribute, or make available the Licensed Technology to any third party, including affiliates, subsidiaries, or contractors, without the prior written consent of Licensor.",
            risks=[RiskType.EXCLUSIVITY],
            severity=0.5,
            business_value=0.4
        ),
        ContractClause(
            id="H2_C5",
            text="Licensee agrees that during the term and for a period of thirty-six (36) months following termination, it shall not develop, market, or distribute any product or service that directly competes with Licensor's core product line as defined in Schedule B. In consideration, Licensor grants Licensee most-favored-customer pricing and priority access to all beta releases and new feature deployments, representing an estimated $600K annual value advantage.",
            risks=[RiskType.NON_COMPETE],
            severity=0.85,
            business_value=0.65
        ),
        ContractClause(
            id="H2_C6",
            text="Licensor warrants that the Licensed Technology will perform substantially in accordance with the documentation for a period of twelve (12) months from delivery. Licensor's sole obligation and Licensee's exclusive remedy for breach of this warranty shall be correction of material defects or, at Licensor's option, replacement of the defective components.",
            risks=[],
            severity=0.2,
            business_value=0.7
        ),
        ContractClause(
            id="H2_C7",
            text="Licensee shall indemnify, defend, and hold harmless Licensor from any and all claims, damages, losses, liabilities, costs, and expenses arising from Licensee's use of the Licensed Technology, including but not limited to claims of data breach, regulatory non-compliance, or harm to third parties resulting from Licensee's products or services that incorporate the Licensed Technology.",
            risks=[RiskType.INDEMNIFICATION],
            severity=0.75,
            business_value=0.35
        ),
        ContractClause(
            id="H2_C8",
            text="All Confidential Information disclosed by either party shall be protected using the same degree of care the receiving party uses to protect its own confidential information, but no less than reasonable care. Confidential Information includes but is not limited to product roadmaps, pricing models, customer data, technical specifications, and any information marked as confidential or that a reasonable person would understand to be confidential.",
            risks=[RiskType.CONFIDENTIALITY],
            severity=0.5,
            business_value=0.5
        ),
        ContractClause(
            id="H2_C9",
            text="Licensor may terminate this Agreement immediately upon written notice if Licensee breaches any material term, including unauthorized sublicensing, reverse engineering, or failure to pay fees within 30 days of the due date. Upon termination, Licensee must destroy all copies of the Licensed Technology and certify destruction in writing within 10 business days.",
            risks=[RiskType.UNILATERAL_TERMINATION],
            severity=0.7,
            business_value=0.3
        ),
        ContractClause(
            id="H2_C10",
            text="IN NO EVENT SHALL LICENSOR'S TOTAL LIABILITY UNDER THIS AGREEMENT EXCEED THE FEES PAID BY LICENSEE IN THE TWELVE (12) MONTHS PRECEDING THE CLAIM. THIS LIMITATION APPLIES TO ALL CAUSES OF ACTION IN THE AGGREGATE, INCLUDING WITHOUT LIMITATION BREACH OF CONTRACT, TORT, NEGLIGENCE, STRICT LIABILITY, AND STATUTORY CLAIMS.",
            risks=[],
            severity=0.1,
            business_value=0.8
        ),
        ContractClause(
            id="H2_C11",
            text="This Agreement shall be governed by and construed in accordance with the laws of the State of Delaware, without regard to its conflict of laws provisions. Any dispute arising under or in connection with this Agreement shall be resolved exclusively through binding arbitration administered by the American Arbitration Association in Wilmington, Delaware.",
            risks=[],
            severity=0.2,
            business_value=0.6
        ),
        ContractClause(
            id="H2_C12",
            text="Licensor shall provide Licensee with reasonable technical support during normal business hours, including access to a dedicated support portal, email-based issue resolution within two business days, and quarterly product update briefings. Premium support tiers with 24/7 availability and four-hour response SLAs are available for an additional annual fee of $180,000.",
            risks=[],
            severity=0.1,
            business_value=0.75
        ),
    ]
}

# Add HARD_002 to the hard contracts list
HARD_CONTRACTS.append(HARD_002_CONTRACT)


def get_contract_by_id(contract_id: str):
    """Retrieve contract data by ID"""
    all_contracts = EASY_CONTRACTS + MEDIUM_CONTRACTS + HARD_CONTRACTS
    for contract in all_contracts:
        if contract["contract_id"] == contract_id:
            return contract
    return None


def get_contracts_by_difficulty(difficulty: str):
    """Get all contracts of a given difficulty"""
    if difficulty == "easy":
        return EASY_CONTRACTS
    elif difficulty == "medium":
        return MEDIUM_CONTRACTS
    elif difficulty == "hard":
        return HARD_CONTRACTS
    return []
