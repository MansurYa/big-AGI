"""
S0.4 - Agent 1 Standalone Test
Tests that Agent 1 (Selector) can be called and returns valid block selections.
"""
import sys
sys.path.insert(0, '/Users/mansurzainullin/MyCode/big-AGI/context-management')

from src.agents.agent1_selector import Agent1Selector
from src.utils.data_loader import add_line_numbers

def test_agent1_standalone():
    """Test Agent 1 standalone functionality."""

    print("=== S0.4: AGENT 1 STANDALONE TEST ===\n")

    # Create test context
    test_context = """User: Let me explain the Monte Carlo simulation approach.

I ran 10,000 iterations with seed=42 and epsilon=0.001. The simulation showed interesting convergence patterns.

During execution, I encountered a ZeroDivisionError in node B during QUEUE aggregation. This happened because the queue was empty.

After debugging, I added validation: if queue is empty, return 0. This fixed the issue.

The final results showed convergence after 5000 iterations with error margin of 0.0015.