"""
Attack Profile Configuration System
Declarative attack simulation for Adversarial Fraud Lab
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from enum import Enum


class AttackCategory(Enum):
    SOCIAL_ENGINEERING = "SE"
    SYNTHETIC_IDENTITY = "KYC"
    PAYMENT_RAIL = "PR"
    AI_SPECIFIC = "AI"
    BEHAVIORAL = "BM"


@dataclass
class AttackProfile:
    """Configuration for a specific fraud attack profile."""
    profile_id: str
    attack_id: str
    fraud_type: str
    category: AttackCategory
    amount_range: Tuple[float, float] = (100, 10000)
    urgency: str = "medium"
    evasion_techniques: List[str] = None
    description: str = ""
    
    def __post_init__(self):
        if self.evasion_techniques is None:
            self.evasion_techniques = []


# Predefined attack profiles
ATTACK_PROFILES = {
    "voice_clone_scam": AttackProfile(
        profile_id="voice_clone_scam",
        attack_id="SE-001",
        fraud_type="ai_impersonation",
        category=AttackCategory.SOCIAL_ENGINEERING,
        amount_range=(500, 10000),
        urgency="high",
        evasion_techniques=["normal_hours"],
        description="Deepfake voice impersonation"
    ),
    "synthetic_identity_basic": AttackProfile(
        profile_id="synthetic_identity_basic",
        attack_id="KYC-002",
        fraud_type="synthetic_identity",
        category=AttackCategory.SYNTHETIC_IDENTITY,
        amount_range=(100, 5000),
        evasion_techniques=["gradual_buildup"],
        description="GAN-generated synthetic identity"
    ),
    "bnpl_max_out": AttackProfile(
        profile_id="bnpl_max_out",
        attack_id="PR-003",
        fraud_type="bnpl_abuse",
        category=AttackCategory.PAYMENT_RAIL,
        amount_range=(500, 10000),
        evasion_techniques=[],
        description="BNPL max-out fraud"
    ),
    "llm_jacking": AttackProfile(
        profile_id="llm_jacking",
        attack_id="AI-004",
        fraud_type="ai_impersonation",
        category=AttackCategory.AI_SPECIFIC,
        amount_range=(100, 5000),
        description="LLM-integrated payment hijacking (NOVEL)"
    ),
}


def get_profile(profile_id: str) -> Optional[AttackProfile]:
    return ATTACK_PROFILES.get(profile_id)


def list_profiles() -> List[str]:
    return list(ATTACK_PROFILES.keys())


if __name__ == "__main__":
    print(f"Attack Profile System: {len(ATTACK_PROFILES)} profiles loaded")
    for pid, profile in ATTACK_PROFILES.items():
        print(f"  - {pid}: {profile.description}")
