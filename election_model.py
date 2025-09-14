"""
Canadian Election Simulator - Election Model
Copyright (c) 2025 [Amin Behbudov, Fares Abdulmajeed Alabdulhadi, Tahmid Wasif Zaman, Dimural Murat]

This module defines the election simulation model and logic.
"""

import random
from typing import Any, Dict, List, Optional, Tuple
import networkx as nx
from config import SEATS_BY_PROVINCE, MAJORITY_THRESHOLD


class RegionNode:
    """
    A node in the election tree representing a region (country, province, or seat).

    Attributes:
        name (str): Name of the region
        node_type (str): Type of region ('country', 'province', or 'seat')
        children (List["RegionNode"]): Child nodes
        num_seats (int): Number of seats in this region
        results (Dict[str, int]): Election results for this region
    """
    name: str
    node_type: str
    children: List["RegionNode"]
    num_seats: int
    results: Dict[str, int]

    def __init__(self, name: str, node_type: str = "country",
                 children: Optional[List["RegionNode"]] = None, num_seats: int = 0) -> None:
        """
        Initialize a RegionNode.

        Args:
            name (str): Name of the region
            node_type (str): Type of region ('country', 'province', or 'seat')
            children (Optional[List[RegionNode]]): Child nodes. Defaults to None.
            num_seats (int, optional): Number of seats in this region. Defaults to 0.
        """
        self.name = name
        self.node_type = node_type  # 'country', 'province', or 'seat'
        self.children = children if children is not None else []
        self.num_seats = num_seats
        self.results = {}

    def add_child(self, child_node: "RegionNode") -> None:
        """
        Add a child node to this region.

        Args:
            child_node (RegionNode): Child region node
        """
        self.children.append(child_node)

    def simulate(self, polling_data: Dict[str, Any], graph: nx.DiGraph, margin: float = 0.03) -> Dict[str, int]:
        """
        Recursively simulate the election for this region and all children.

        Args:
            polling_data (dict): Polling data (either for the entire country or for a specific province)
            graph (nx.DiGraph): Voter transition graph
            margin (float, optional): Random margin to apply to polling. Defaults to 0.03.

        Returns:
            Dict[str, int]: Election results for this region
        """
        if self.node_type == "seat":
            self.results = simulate_single_seat(polling_data, graph, margin)
            return self.results
        elif self.node_type == "province":
            self.results = {}
            # Expect polling_data for a province to be a dict keyed by seat
            for child in self.children:
                child_poll = polling_data.get(self.name, {})
                child_result = child.simulate(child_poll, graph, margin)
                for p, count in child_result.items():
                    self.results[p] = self.results.get(p, 0) + count
            return self.results
        elif self.node_type == "country":
            self.results = {}
            # For country, polling_data is expected to be the full polling dict
            for child in self.children:
                child_result = child.simulate(polling_data, graph, margin)
                for p, count in child_result.items():
                    self.results[p] = self.results.get(p, 0) + count
            return self.results

        return self.results

    def reset_results(self) -> None:
        """
        Reset the results for this region and all children.
        """
        self.results = {}
        for child in self.children:
            child.reset_results()


def build_election_tree(seats_by_province: Dict[str, int]) -> RegionNode:
    """
    Build an election tree based on provincial seat distribution.

    Args:
        seats_by_province (Dict[str, int]): Mapping of provinces to number of seats

    Returns:
        RegionNode: Root node of the election tree
    """
    canada = RegionNode("Canada", node_type="country")
    for province, num_seats in seats_by_province.items():
        province_node = RegionNode(province, node_type="province", num_seats=num_seats)
        for i in range(num_seats):
            seat_node = RegionNode(f"{province}_Seat_{i + 1}", node_type="seat")
            province_node.add_child(seat_node)
        canada.add_child(province_node)
    return canada


def simulate_single_seat(polling: Dict[str, float], graph: nx.DiGraph, margin: float = 0.03) -> Dict[str, int]:
    """
    Simulate a single seat election based on polling data.

    Args:
        polling (Dict[str, float]): Polling data for parties
        graph (nx.DiGraph): Voter transition graph
        margin (float, optional): Random margin to apply to polling. Defaults to 0.03.

    Returns:
        Dict[str, int]: Election result for the seat (winning party gets 1)
    """
    adjusted_polling = adjust_polling_graph(polling, graph)

    sampled_poll = {
        p: max(0, min(1, adjusted_polling[p] + random.uniform(-margin, margin)))
        for p in adjusted_polling
    }
    total = sum(sampled_poll.values())

    for m in sampled_poll:
        sampled_poll[m] /= total

    parties = list(sampled_poll.keys())
    weights = list(sampled_poll.values())
    winner = random.choices(parties, weights)[0]
    return {winner: 1}


def adjust_polling_graph(original_polling: Dict[str, float],
                         graph: Optional[nx.DiGraph] = None, influence_factor: float = 0.2) -> Dict[str, float]:
    """
    Adjust polling based on voter transition patterns from the graph.

    Args:
        original_polling (Dict[str, float]): Original polling data
        graph (Optional[nx.DiGraph]): Voter transition graph. Defaults to None.
        influence_factor (float, optional): Factor to weight the graph influence. Defaults to 0.2.

    Returns:
        Dict[str, float]: Adjusted polling data
    """
    if graph is None:
        return original_polling  # no adjustment

    adjusted_polling: Dict[str, float] = original_polling.copy()
    for p in original_polling:
        if p == "OTH" or p not in graph.nodes:
            continue
        incoming_influence = 0.0
        for neighbor in graph.predecessors(p):
            if neighbor in original_polling and graph[neighbor][p]['weight'] > 0:
                incoming_influence += original_polling[neighbor] * graph[neighbor][p]['weight']
        adjusted_polling[p] += influence_factor * incoming_influence

    total = sum(adjusted_polling.values())
    for p in adjusted_polling:
        adjusted_polling[p] /= total
    return adjusted_polling


def _simulate_trial(election_tree: RegionNode, polling_data: Dict[str, Any],
                    voter_graph: Optional[nx.DiGraph], margin: float = 0.03) -> Dict[str, int]:
    """
    Helper function to simulate a single trial.

    Args:
        election_tree (RegionNode): The root of the election tree.
        polling_data (Dict[str, Any]): Polling data.
        voter_graph (Optional[nx.DiGraph]): Voter transition graph.
        margin (float): Margin parameter.

    Returns:
        Dict[str, int]: Simulation results for the trial.
    """
    election_tree.reset_results()
    return election_tree.simulate(polling_data, voter_graph, margin)


def run_simulation(polling_data: Dict[str, Any], trials: int = 1000, voter_graph: Optional[nx.DiGraph] = None)\
        -> Tuple[Dict[str, List[int]], Dict[str, Dict[str, float]]]:
    """
    Run a full election simulation with multiple trials.

    Args:
        polling_data (Dict[str, Any]): Polling data by province
        trials (int, optional): Number of simulation trials. Defaults to 1000.
        voter_graph (Optional[nx.DiGraph], optional): Voter transition graph. Defaults to None.

    Returns:
        Tuple[Dict[str, List[int]], Dict[str, Dict[str, float]]]:
         A tuple containing seat distribution and win statistics.
    """
    election_tree = build_election_tree(SEATS_BY_PROVINCE)
    all_parties = {party for province_poll in polling_data.values() for party in province_poll.keys()}

    seat_distribution = {party: [] for party in all_parties}
    win_stats = {party: {"majority": 0, "minority": 0, "no_win": 0} for party in all_parties}

    def update_win_stats(results: Dict[str, int]) -> None:
        """
            Update the win statistics based on the election results.

            Args:
                results (Dict[str, int]): The election results mapping each party to its seat count.
            Returns:
                None: Updates the `win_stats` dictionary in place.
        """
        top_party = max(results, key=results.get)
        top_seats = results[top_party]
        ties = [party for party, count in results.items() if count == top_seats]

        if len(ties) == 1:
            if top_seats >= MAJORITY_THRESHOLD:
                win_stats[top_party]["majority"] += 1
            else:
                win_stats[top_party]["minority"] += 1

    for _ in range(trials):
        results = _simulate_trial(election_tree, polling_data, voter_graph, margin=0.03)
        for y, count in results.items():
            seat_distribution[y].append(count)
        update_win_stats(results)

    for x in all_parties:
        maj, minr = win_stats[x]["majority"], win_stats[x]["minority"]
        win_stats[x]["no_win"] = trials - maj - minr

        for stat in win_stats[x]:
            win_stats[x][stat] /= trials

    return seat_distribution, win_stats


if __name__ == "__main__":
    # Test the election model with sample data
    from scraper import scrape_polling_data
    from graph import build_historical_voter_graph
    from data_loader import load_historical_data

    # Get sample data
    sample_polling = scrape_polling_data()
    if sample_polling:
        votes_2015, votes_2019, votes_2021 = load_historical_data()
        historical_graph = build_historical_voter_graph(votes_2015, votes_2019, votes_2021)

        # Run a small test simulation
        seats, stats = run_simulation(sample_polling, trials=100, voter_graph=historical_graph)


        print("Simulation Results (100 trials):")
        for party, prob in stats.items():
            print(f"{party}: {100 * prob['majority']:.1f}% majority, {100 * prob['minority']:.1f}% minority")


if __name__ == '__main__':
    import doctest
    import python_ta

    doctest.testmod()

    python_ta.check_all(config={
        'extra-imports': [],
        'allowed-io': [],
        'max-line-length': 120
    })
