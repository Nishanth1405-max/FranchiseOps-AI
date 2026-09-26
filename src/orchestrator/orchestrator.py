import pandas as pd

from inventory_agent.inventory_agent.inventory_agent import (
    load_inventory_data,
    build_inventory_agent_output,
)

from src.marketing_agent.marketing_agent import (
    load_data,
    build_marketing_agent_output,
)


class AgentOrchestrator:
    """
    Coordinates the execution of franchise agents.
    """

    def run(self):
        print("\n========== AGENT ORCHESTRATION ==========\n")

        results = {}

        # Load common dataset
        print("Loading franchise dataset...")
        inventory_data = load_inventory_data()

        # Inventory Agent
        print("\nRunning Inventory Agent...")
        inventory_result = build_inventory_agent_output(inventory_data)
        results["Inventory Agent"] = inventory_result

        # Marketing Agent
        print("\nRunning Marketing Agent...")
        marketing_data = load_data()
        marketing_result = build_marketing_agent_output(marketing_data)
        results["Marketing Agent"] = marketing_result

        print("\n========== ORCHESTRATION COMPLETED ==========")

        print(
            f"Inventory output: {inventory_result.shape}"
        )
        print(
            f"Marketing output: {marketing_result.shape}"
        )

        return results