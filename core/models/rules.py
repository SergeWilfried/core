"""
Rule engine models for configurable compliance rules
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Any, Callable
from pydantic import BaseModel, Field


class RuleType(str, Enum):
    """Type of compliance rule"""

    AMOUNT_THRESHOLD = "amount_threshold"
    VELOCITY = "velocity"
    GEO_FENCING = "geo_fencing"
    SANCTION_SCREENING = "sanction_screening"
    KYC_VERIFICATION = "kyc_verification"
    PEP_CHECK = "pep_check"
    PATTERN_DETECTION = "pattern_detection"
    BLACKLIST = "blacklist"
    WHITELIST = "whitelist"
    TIME_RESTRICTION = "time_restriction"
    CURRENCY_RESTRICTION = "currency_restriction"
    PAYMENT_METHOD_RESTRICTION = "payment_method_restriction"
    CUSTOM = "custom"


class RuleConditionOperator(str, Enum):
    """Operators for rule conditions"""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    MATCHES_REGEX = "matches_regex"
    BETWEEN = "between"


class RuleAction(str, Enum):
    """Action to take when rule is triggered"""

    ALLOW = "allow"
    BLOCK = "block"
    REVIEW = "review"
    ALERT = "alert"
    LOG = "log"
    INCREASE_RISK_SCORE = "increase_risk_score"
    REQUIRE_APPROVAL = "require_approval"


class RuleSeverity(str, Enum):
    """Severity of rule violation"""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RuleScope(str, Enum):
    """Scope where rule applies"""

    GLOBAL = "global"  # All organizations
    ORGANIZATION = "organization"  # Specific organization
    CUSTOMER = "customer"  # Specific customer
    ACCOUNT = "account"  # Specific account


class RuleCondition(BaseModel):
    """Condition for rule evaluation"""

    field: str = Field(..., description="Field to evaluate (e.g., 'amount', 'country')")
    operator: RuleConditionOperator = Field(..., description="Comparison operator")
    value: Any = Field(..., description="Value to compare against")
    value_type: str = Field(
        default="string", description="Type: string, number, boolean, list"
    )

    def evaluate(self, context: dict[str, Any]) -> bool:
        """
        Evaluate condition against context

        Args:
            context: Evaluation context with field values

        Returns:
            True if condition matches
        """
        # Get field value from context
        field_value = context.get(self.field)
        if field_value is None:
            return False

        # Convert types for comparison
        compare_value = self.value
        if self.value_type == "number":
            field_value = float(field_value) if isinstance(field_value, (int, float, Decimal)) else 0
            compare_value = float(self.value)
        elif self.value_type == "boolean":
            field_value = bool(field_value)
            compare_value = bool(self.value)

        # Evaluate operator
        if self.operator == RuleConditionOperator.EQUALS:
            return field_value == compare_value
        elif self.operator == RuleConditionOperator.NOT_EQUALS:
            return field_value != compare_value
        elif self.operator == RuleConditionOperator.GREATER_THAN:
            return field_value > compare_value
        elif self.operator == RuleConditionOperator.GREATER_THAN_OR_EQUAL:
            return field_value >= compare_value
        elif self.operator == RuleConditionOperator.LESS_THAN:
            return field_value < compare_value
        elif self.operator == RuleConditionOperator.LESS_THAN_OR_EQUAL:
            return field_value <= compare_value
        elif self.operator == RuleConditionOperator.IN:
            return field_value in (compare_value if isinstance(compare_value, list) else [compare_value])
        elif self.operator == RuleConditionOperator.NOT_IN:
            return field_value not in (compare_value if isinstance(compare_value, list) else [compare_value])
        elif self.operator == RuleConditionOperator.CONTAINS:
            return compare_value in str(field_value)
        elif self.operator == RuleConditionOperator.NOT_CONTAINS:
            return compare_value not in str(field_value)
        elif self.operator == RuleConditionOperator.MATCHES_REGEX:
            import re
            return bool(re.match(compare_value, str(field_value)))
        elif self.operator == RuleConditionOperator.BETWEEN:
            if isinstance(compare_value, list) and len(compare_value) == 2:
                return compare_value[0] <= field_value <= compare_value[1]
            return False

        return False


class ComplianceRule(BaseModel):
    """Configurable compliance rule"""

    id: str = Field(..., description="Unique rule ID")
    organization_id: Optional[str] = Field(
        None, description="Organization ID (None for global rules)"
    )

    # Rule identification
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    rule_type: RuleType = Field(..., description="Type of rule")

    # Scope
    scope: RuleScope = Field(
        default=RuleScope.ORGANIZATION, description="Rule scope"
    )
    applies_to: list[str] = Field(
        default_factory=list,
        description="Specific IDs this rule applies to (customers, accounts, etc.)",
    )

    # Conditions
    conditions: list[RuleCondition] = Field(
        default_factory=list, description="Conditions to evaluate"
    )
    conditions_logic: str = Field(
        default="AND", description="Logic for combining conditions: AND, OR"
    )

    # Action
    action: RuleAction = Field(..., description="Action when rule triggers")
    severity: RuleSeverity = Field(..., description="Severity level")
    risk_score_impact: int = Field(
        default=0, ge=0, le=100, description="Impact on risk score (0-100)"
    )

    # Configuration
    message: Optional[str] = Field(
        None, description="Message to display when rule triggers"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional rule metadata"
    )

    # Status
    enabled: bool = Field(default=True, description="Whether rule is active")
    priority: int = Field(
        default=100, ge=1, le=1000, description="Evaluation priority (lower = higher priority)"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When rule was created"
    )
    updated_at: Optional[datetime] = Field(
        None, description="When rule was last updated"
    )
    created_by: Optional[str] = Field(
        None, description="User who created rule"
    )

    def evaluate(self, context: dict[str, Any]) -> bool:
        """
        Evaluate rule against context

        Args:
            context: Evaluation context

        Returns:
            True if rule triggers
        """
        if not self.enabled:
            return False

        if not self.conditions:
            return False

        # Evaluate all conditions
        results = [condition.evaluate(context) for condition in self.conditions]

        # Apply logic
        if self.conditions_logic == "AND":
            return all(results)
        elif self.conditions_logic == "OR":
            return any(results)

        return False

    def should_apply_to(self, target_id: Optional[str] = None) -> bool:
        """
        Check if rule should apply to target

        Args:
            target_id: Customer/account/transaction ID

        Returns:
            True if rule applies
        """
        if not self.enabled:
            return False

        # Global rules apply to all
        if self.scope == RuleScope.GLOBAL:
            return True

        # If applies_to is empty, apply to all in scope
        if not self.applies_to:
            return True

        # Check if target is in applies_to list
        if target_id and target_id in self.applies_to:
            return True

        return False


class RuleEvaluationResult(BaseModel):
    """Result of rule evaluation"""

    rule_id: str = Field(..., description="Rule that was evaluated")
    rule_name: str = Field(..., description="Rule name")
    triggered: bool = Field(..., description="Whether rule triggered")
    action: Optional[RuleAction] = Field(None, description="Action to take")
    severity: Optional[RuleSeverity] = Field(None, description="Severity")
    message: Optional[str] = Field(None, description="Message")
    risk_score_impact: int = Field(default=0, description="Risk score impact")
    context: dict[str, Any] = Field(
        default_factory=dict, description="Evaluation context"
    )
    evaluated_at: datetime = Field(
        default_factory=datetime.utcnow, description="When evaluated"
    )


class RuleSet(BaseModel):
    """Collection of rules for a specific purpose"""

    id: str = Field(..., description="Rule set ID")
    organization_id: Optional[str] = Field(
        None, description="Organization ID (None for global)"
    )
    name: str = Field(..., description="Rule set name")
    description: str = Field(..., description="Rule set description")

    # Rules
    rule_ids: list[str] = Field(
        default_factory=list, description="Rules in this set"
    )

    # Configuration
    enabled: bool = Field(default=True, description="Whether rule set is active")
    evaluation_order: str = Field(
        default="priority", description="How to order rules: priority, sequential"
    )
    stop_on_first_trigger: bool = Field(
        default=False, description="Stop evaluating after first trigger"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When created"
    )
    updated_at: Optional[datetime] = Field(None, description="When updated")

    # Metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class RuleTemplate(BaseModel):
    """Pre-configured rule template"""

    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    rule_type: RuleType = Field(..., description="Rule type")
    category: str = Field(
        ..., description="Category: kyc, aml, sanctions, velocity, etc."
    )

    # Template configuration
    default_conditions: list[dict] = Field(
        default_factory=list, description="Default conditions"
    )
    default_action: RuleAction = Field(..., description="Default action")
    default_severity: RuleSeverity = Field(..., description="Default severity")

    # Customization
    configurable_fields: list[str] = Field(
        default_factory=list, description="Fields that can be customized"
    )

    # Usage
    usage_count: int = Field(
        default=0, description="How many times template was used"
    )

    # Metadata
    tags: list[str] = Field(default_factory=list, description="Template tags")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


# Pre-built rule templates
RULE_TEMPLATES = {
    "high_value_transaction": RuleTemplate(
        id="tmpl_high_value",
        name="High Value Transaction",
        description="Flag transactions above a certain amount for review",
        rule_type=RuleType.AMOUNT_THRESHOLD,
        category="aml",
        default_conditions=[
            {
                "field": "amount",
                "operator": "greater_than",
                "value": 10000,
                "value_type": "number",
            }
        ],
        default_action=RuleAction.REVIEW,
        default_severity=RuleSeverity.HIGH,
        configurable_fields=["amount", "action"],
        tags=["aml", "threshold"],
    ),
    "blocked_country": RuleTemplate(
        id="tmpl_blocked_country",
        name="Blocked Country",
        description="Block transactions to/from specific countries",
        rule_type=RuleType.GEO_FENCING,
        category="sanctions",
        default_conditions=[
            {
                "field": "country_code",
                "operator": "in",
                "value": ["IR", "KP", "SY"],  # Iran, North Korea, Syria
                "value_type": "list",
            }
        ],
        default_action=RuleAction.BLOCK,
        default_severity=RuleSeverity.CRITICAL,
        configurable_fields=["countries"],
        tags=["sanctions", "geo"],
    ),
    "daily_velocity": RuleTemplate(
        id="tmpl_daily_velocity",
        name="Daily Transaction Limit",
        description="Limit daily transaction count or amount per customer",
        rule_type=RuleType.VELOCITY,
        category="fraud",
        default_conditions=[
            {
                "field": "daily_count",
                "operator": "greater_than",
                "value": 10,
                "value_type": "number",
            }
        ],
        default_action=RuleAction.BLOCK,
        default_severity=RuleSeverity.MEDIUM,
        configurable_fields=["daily_count", "daily_amount"],
        tags=["velocity", "fraud"],
    ),
    "unverified_kyc": RuleTemplate(
        id="tmpl_unverified_kyc",
        name="Unverified KYC",
        description="Block transactions for customers without verified KYC",
        rule_type=RuleType.KYC_VERIFICATION,
        category="kyc",
        default_conditions=[
            {
                "field": "kyc_status",
                "operator": "not_equals",
                "value": "verified",
                "value_type": "string",
            }
        ],
        default_action=RuleAction.BLOCK,
        default_severity=RuleSeverity.HIGH,
        configurable_fields=["action"],
        tags=["kyc"],
    ),
}
