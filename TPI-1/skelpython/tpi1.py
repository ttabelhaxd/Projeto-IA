# STUDENT NAME: ABEL JOSÉ ENES TEIXEIRA
# STUDENT NUMBER: 113655

# DISCUSSED TPI-1 WITH: (names and numbers):
"""
José Marques 114321 
Luís Godinho 112959
Tiago Lopes  113586
"""


from tree_search import *
from strips import *
from blocksworld import *


class MyNode(SearchNode):

    def __init__(self, state, parent, depth=0, cost=0, heuristic=0, action=None):
        super().__init__(state, parent)
        self.depth = depth
        self.cost = cost
        self.heuristic = heuristic
        self.action = action


class MyTree(SearchTree):

    def __init__(self, problem, strategy="breadth", improve=False):
        super().__init__(problem, strategy)
        root = MyNode(problem.initial, None)
        self.open_nodes = [root]
        self.num_closed = 0
        self.num_skipped = 0
        self.num_solution = 0
        self.strategy = strategy
        self.improve = improve
        self.best_solution = None
        self.best_cost = float("inf")

    @property
    def num_open(self):
        return len(self.open_nodes)

    def astar_add_to_open(self, lnewnodes):
        self.open_nodes.extend(lnewnodes)
        self.open_nodes.sort(key=lambda x: (x.cost + x.heuristic, x.depth, x.state))

    def informeddepth_add_to_open(self, lnewnodes):
        lnewnodes.sort(key=lambda n: (n.cost + n.heuristic, n.state))
        self.open_nodes[:0] = lnewnodes

    def search2(self):
        while self.open_nodes != []:
            node = self.open_nodes.pop(0)

            if self.problem.goal_test(node.state):
                if not self.improve:
                    self.solution = node
                    self.num_solution += 1
                    return self.get_path(node)

                if self.best_solution is None or node.cost < self.best_cost:
                    self.best_solution = node
                    self.best_cost = node.cost

                self.num_solution += 1
                continue

            elif node.cost + node.heuristic >= self.best_cost:
                self.num_skipped += 1
                continue

            else:
                lnewnodes = []
                for a in self.problem.domain.actions(node.state):
                    newstate = self.problem.domain.result(node.state, a)
                    if newstate not in self.get_path(node):
                        newnode = MyNode(
                            state=newstate,
                            parent=node,
                            depth=node.depth + 1,
                            cost=node.cost + self.problem.domain.cost(node.state, a),
                            heuristic=self.problem.domain.heuristic(
                                newstate, self.problem.goal
                            ),
                            action=a,
                        )
                        lnewnodes.append(newnode)

                self.add_to_open(lnewnodes)
                self.num_closed += 1

        if self.improve and self.best_solution is not None:
            self.solution = self.best_solution
            return self.get_path(self.best_solution)

        return None

    def check_admissible(self, node):
        current = node.parent
        while current is not None:
            if current.cost + current.heuristic > node.cost:
                return False
            current = current.parent
        return True

    def get_plan(self, node):
        if node.parent == None:
            return []
        plan = self.get_plan(node.parent)
        plan += [node.action]
        return plan

class MyBlocksWorld(STRIPS):

    def heuristic(self, state, goal):
        return self.heuristic_combined(state, goal)

    def heuristic_blocks_out_of_place(self, state, goal):
        """
        Heuristic 1: Number of blocks out of place
        This heuristic is admissible since each block out of place must be moved at least once.
        """
        return len([block for block in goal if block not in state])

    def heuristic_more_informed(self, state, goal):
        """
        Heuristic 2: Number of blocks out of place with distance
        This heuristic sums the minimum number of moves needed to reposition each block.
        """
        distance = 0
        for predicate in goal:
            if predicate not in state:
                if isinstance(predicate, On):
                    block1, block2 = predicate.args
                    for state_predicate in state:
                        if isinstance(state_predicate, On) and state_predicate.args[0] == block1:
                            distance += 1 #Move from one block on top of another
                            break
                        elif isinstance(state_predicate, Floor) and state_predicate.args[0] == block1:
                            distance += 1 #Move from floor to the goal position
                            break
        return distance

    def heuristic_very_informed(self, state, goal):
        """
        Heuristic 3: Very informed heuristic
        This heuristic ensures it counts the minimum moves required and does not overestimate.
        """
        moves = 0
        for predicate in goal:
            if predicate not in state:
                moves += 1
                if isinstance(predicate, On):
                    block1, block2 = predicate.args
                    for state_predicate in state:
                        if isinstance(state_predicate, On) and state_predicate.args[0] == block1:
                            moves += 1 #Move to block on top
                            break
                        elif isinstance(state_predicate, Floor) and state_predicate.args[0] == block1:
                            moves += 1 #Move from floor to the block
                            break
        return moves

    def heuristic_combined(self, state, goal):
        """
        Combined heuristic
        This heuristic combines the individual heuristics in an admissible way.
        """
        out_of_place = self.heuristic_blocks_out_of_place(state, goal)
        distance = self.heuristic_more_informed(state, goal)
        moves = self.heuristic_very_informed(state, goal)
        
        # Ensure the combined heuristic is admissible
        return max(out_of_place, distance, moves)
