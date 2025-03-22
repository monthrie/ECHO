# bridge.py - Place this in your original root directory (outside second_brain/)

# Import from new locations and expose at the original import paths
from second_brain.prompts.structuring_prompt import get_structuring_prompt
from second_brain.prompts.conversion_prompt import get_conversion_prompt
from second_brain.prompts.blueprint_prompt import get_blueprint_conversion_prompt
from second_brain.prompts.update_prompts import get_integration_decision_prompt
from second_brain.utils.config import Config

# Make these available at their original import paths
# This allows existing code to continue working without changes
