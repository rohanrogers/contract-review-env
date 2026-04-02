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
                severity=0.3,
                business_value=0.6
            ),
            ContractClause(
                id="H1_C2",
                text="The initial term shall be three years, automatically extending for additional one-year periods unless written notice of non-renewal is provided; such notice shall be effective only if delivered by certified mail to the registered office address, and shall require approval by Client's board of directors if initiated by Contractor but may be effectuated by Client's procurement manager.",
                risks=[RiskType.AUTO_RENEWAL, RiskType.UNILATERAL_TERMINATION],
                severity=0.9,
                business_value=0.3
            ),
            ContractClause(
                id="H1_C3",
                text="Contractor shall defend, indemnify, and hold harmless Client Parties (defined to include Client, its parent, subsidiaries, affiliates, and their respective officers, directors, employees, agents, successors, and assigns) from any and all Losses (defined to include claims, demands, actions, damages, liabilities, costs, and expenses including attorneys' fees and expert witness fees) arising from, relating to, or in connection with: (a) services performed or not performed hereunder; (b) any actual or alleged infringement of third-party intellectual property rights; (c) any breach or alleged breach of representations, warranties, or covenants; or (d) any negligent or willful acts or omissions of Contractor or its personnel, regardless of whether such Losses arise in contract, tort, strict liability, or any other theory of liability.",
                risks=[RiskType.INDEMNIFICATION, RiskType.UNLIMITED_LIABILITY],
                severity=1.0,
                business_value=0.2
            ),
            ContractClause(
                id="H1_C4",
                text="Contractor acknowledges that during the course of engagement, it may have access to or become aware of Confidential Information, which shall include not only information marked as confidential but also any business, technical, financial, customer, supplier, pricing, strategic, or other information that reasonably should be understood as confidential given the nature of the information and circumstances of disclosure; Contractor agrees to protect such information using the same degree of care used to protect its own confidential information of like kind, but in no event less than reasonable care, and shall not disclose such information to any third party or use it for any purpose whatsoever except as strictly necessary for performance hereunder.",
                risks=[RiskType.CONFIDENTIALITY],
                severity=0.7,
                business_value=0.5
            ),
            ContractClause(
                id="H1_C5",
                text="Contractor agrees that all Deliverables shall constitute works made for hire under applicable copyright law; to the extent any Deliverable does not qualify as a work made for hire, Contractor hereby irrevocably assigns, transfers, and conveys to Client all right, title, and interest in and to such Deliverable, including all intellectual property rights therein, whether now known or hereafter devised; Contractor further agrees to execute any documents reasonably requested by Client to perfect such assignment and waives any moral rights or similar rights it may have in the Deliverables.",
                risks=[RiskType.IP_TRANSFER],
                severity=0.8,
                business_value=0.4
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
                text="Contractor covenants that, during the term and for forty-eight (48) months following termination for any reason, it shall not, whether directly or indirectly, as principal, agent, employee, consultant, or in any other capacity: (a) engage in any business that competes with any line of business conducted by Client or its affiliates; (b) solicit or service any customer or prospective customer of Client with whom Contractor had contact or about whom Contractor obtained information during the engagement; or (c) hire, solicit, or encourage any employee or contractor of Client to terminate their relationship with Client; Contractor acknowledges that the scope and duration of these restrictions are reasonable given the nature of Client's business and Contractor's role.",
                risks=[RiskType.EXCLUSIVITY, RiskType.NON_COMPETE],
                severity=0.95,
                business_value=0.1
            ),
            ContractClause(
                id="H1_C8",
                text="This Agreement shall be governed by and construed in accordance with the laws of the Cayman Islands, without regard to conflicts of law principles; any legal action or proceeding arising hereunder shall be brought exclusively in the courts of George Town, Grand Cayman, and each party irrevocably submits to the jurisdiction of such courts and waives any objection to venue or claim of inconvenient forum.",
                risks=[RiskType.JURISDICTION],
                severity=0.8,
                business_value=0.3
            ),
        ]
    }
]


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
