"""
Sanctions screening utility for OFAC, UN, EU and other sanction lists
"""

import logging
from typing import Optional
from difflib import SequenceMatcher

from ..models.compliance import SanctionListType, SanctionMatch

logger = logging.getLogger(__name__)


class SanctionsScreening:
    """
    Sanctions list screening utility

    In production, integrate with:
    - Dow Jones Risk & Compliance
    - Refinitiv World-Check One
    - ComplyAdvantage
    - Accuity
    - LexisNexis Bridger Insight XG

    This is a simplified implementation for demonstration.
    """

    def __init__(self):
        """Initialize sanctions screening"""
        # In production, load from database or external service
        self.sanction_lists = self._load_sanction_lists()

    def _load_sanction_lists(self) -> dict:
        """
        Load sanction lists from storage

        In production:
        1. Subscribe to official sanction list APIs/feeds
        2. Store in database with daily updates
        3. Implement caching for performance
        4. Include aliases, DOB, passport numbers, etc.

        Returns:
            Dictionary of sanction lists by type
        """
        # Simplified example data - In production, load from database
        return {
            SanctionListType.OFAC: [
                {
                    "id": "ofac_1",
                    "name": "IRAN, GOVERNMENT OF",
                    "program": "IRAN",
                    "country": "IR",
                    "aliases": ["ISLAMIC REPUBLIC OF IRAN", "IRAN GOV"],
                },
                {
                    "id": "ofac_2",
                    "name": "KOREAN COMMITTEE FOR SPACE TECHNOLOGY",
                    "program": "DPRK",
                    "country": "KP",
                    "aliases": ["KCST"],
                },
                # Add more OFAC entries
            ],
            SanctionListType.UN: [
                {
                    "id": "un_1",
                    "name": "AL-QAIDA",
                    "program": "TERRORISM",
                    "country": None,
                    "aliases": ["QAIDA", "AL QAEDA"],
                },
                # Add more UN entries
            ],
            SanctionListType.EU: [
                {
                    "id": "eu_1",
                    "name": "TALIBAN",
                    "program": "TERRORISM",
                    "country": "AF",
                    "aliases": ["TALEBAN"],
                },
                # Add more EU entries
            ],
        }

    def screen(
        self,
        name: str,
        list_types: Optional[list[SanctionListType]] = None,
        threshold: float = 0.8,
    ) -> list[dict]:
        """
        Screen name against sanction lists

        Args:
            name: Name to screen (person or entity)
            list_types: List types to check (None = all)
            threshold: Match threshold (0-1), default 0.8

        Returns:
            List of potential matches with scores
        """
        if not name or not name.strip():
            return []

        name = name.upper().strip()
        matches = []

        # Default to all lists
        if list_types is None:
            list_types = [
                SanctionListType.OFAC,
                SanctionListType.UN,
                SanctionListType.EU,
            ]

        # Screen against each list
        for list_type in list_types:
            if list_type not in self.sanction_lists:
                continue

            for entry in self.sanction_lists[list_type]:
                # Check exact match with name
                if name == entry["name"].upper():
                    matches.append(
                        {
                            "list_type": list_type,
                            "match_score": 1.0,
                            "match_type": "exact",
                            "sanction_id": entry["id"],
                            "match_name": entry["name"],
                            "program": entry.get("program"),
                            "country": entry.get("country"),
                            "aliases": entry.get("aliases", []),
                        }
                    )
                    continue

                # Check fuzzy match with name
                name_score = self._fuzzy_match(name, entry["name"].upper())
                if name_score >= threshold:
                    matches.append(
                        {
                            "list_type": list_type,
                            "match_score": name_score,
                            "match_type": "fuzzy",
                            "sanction_id": entry["id"],
                            "match_name": entry["name"],
                            "program": entry.get("program"),
                            "country": entry.get("country"),
                            "aliases": entry.get("aliases", []),
                        }
                    )
                    continue

                # Check aliases
                for alias in entry.get("aliases", []):
                    if name == alias.upper():
                        matches.append(
                            {
                                "list_type": list_type,
                                "match_score": 1.0,
                                "match_type": "alias",
                                "sanction_id": entry["id"],
                                "match_name": entry["name"],
                                "program": entry.get("program"),
                                "country": entry.get("country"),
                                "aliases": entry.get("aliases", []),
                            }
                        )
                        break

                    alias_score = self._fuzzy_match(name, alias.upper())
                    if alias_score >= threshold:
                        matches.append(
                            {
                                "list_type": list_type,
                                "match_score": alias_score,
                                "match_type": "alias_fuzzy",
                                "sanction_id": entry["id"],
                                "match_name": entry["name"],
                                "program": entry.get("program"),
                                "country": entry.get("country"),
                                "aliases": entry.get("aliases", []),
                            }
                        )
                        break

        # Sort by match score descending
        matches.sort(key=lambda x: x["match_score"], reverse=True)

        logger.info(
            f"Sanctions screening for '{name}': {len(matches)} matches found"
        )

        return matches

    def _fuzzy_match(self, str1: str, str2: str) -> float:
        """
        Calculate fuzzy match score between two strings

        Args:
            str1: First string
            str2: Second string

        Returns:
            Match score (0-1)
        """
        return SequenceMatcher(None, str1, str2).ratio()

    def screen_country(self, country_code: str) -> bool:
        """
        Check if country is sanctioned

        Args:
            country_code: ISO 3166-1 alpha-2 country code

        Returns:
            True if country is sanctioned
        """
        if not country_code:
            return False

        country_code = country_code.upper()

        # High-risk/sanctioned countries
        sanctioned_countries = {
            "IR",  # Iran
            "KP",  # North Korea
            "SY",  # Syria
            "CU",  # Cuba
            "VE",  # Venezuela (partial)
            # Add more based on current sanctions
        }

        return country_code in sanctioned_countries

    def get_high_risk_countries(self) -> list[str]:
        """
        Get list of high-risk countries for compliance

        Returns:
            List of ISO country codes
        """
        return [
            "IR",  # Iran
            "KP",  # North Korea
            "SY",  # Syria
            "CU",  # Cuba
            "VE",  # Venezuela
            "AF",  # Afghanistan
            "IQ",  # Iraq
            "LY",  # Libya
            "SO",  # Somalia
            "SD",  # Sudan
            "YE",  # Yemen
            "MM",  # Myanmar (Burma)
            "BY",  # Belarus
            # Add more based on FATF grey/black lists
        ]

    async def reload_sanction_lists(self):
        """
        Reload sanction lists from source

        In production:
        1. Fetch from official APIs (OFAC, UN, EU)
        2. Parse and normalize data
        3. Update database
        4. Clear caches
        5. Log update metrics
        """
        logger.info("Reloading sanction lists...")
        self.sanction_lists = self._load_sanction_lists()
        logger.info("Sanction lists reloaded successfully")


class CountryRiskAssessment:
    """Country risk assessment for geographic compliance"""

    def __init__(self):
        """Initialize country risk assessment"""
        self.risk_scores = self._load_country_risk_scores()

    def _load_country_risk_scores(self) -> dict[str, int]:
        """
        Load country risk scores

        In production, integrate with:
        - FATF country assessments
        - Basel AML Index
        - Transparency International CPI
        - World Bank governance indicators

        Returns:
            Dictionary of country code -> risk score (0-100)
        """
        return {
            # Critical risk (75-100)
            "KP": 100,  # North Korea
            "IR": 95,  # Iran
            "SY": 95,  # Syria
            "AF": 90,  # Afghanistan
            "YE": 90,  # Yemen
            # High risk (50-74)
            "MM": 70,  # Myanmar
            "VE": 65,  # Venezuela
            "IQ": 65,  # Iraq
            "LY": 65,  # Libya
            # Medium risk (25-49)
            "PK": 45,  # Pakistan
            "BD": 40,  # Bangladesh
            "NG": 40,  # Nigeria
            "PH": 35,  # Philippines
            # Low risk (0-24)
            "US": 10,
            "GB": 10,
            "DE": 10,
            "FR": 10,
            "CA": 10,
            "AU": 10,
            "JP": 10,
            "SG": 10,
            "CH": 10,
            # Default for unlisted countries
        }

    def get_country_risk_score(self, country_code: str) -> int:
        """
        Get risk score for country

        Args:
            country_code: ISO 3166-1 alpha-2 country code

        Returns:
            Risk score (0-100)
        """
        if not country_code:
            return 50  # Default medium risk

        country_code = country_code.upper()
        return self.risk_scores.get(country_code, 50)

    def is_high_risk_country(self, country_code: str) -> bool:
        """
        Check if country is high risk

        Args:
            country_code: ISO 3166-1 alpha-2 code

        Returns:
            True if high risk (score >= 50)
        """
        return self.get_country_risk_score(country_code) >= 50


# Global instances
sanctions_screening = SanctionsScreening()
country_risk_assessment = CountryRiskAssessment()
