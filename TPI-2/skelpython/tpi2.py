#encoding: utf8

# YOUR NAME: Abel José Enes Teixeira
# YOUR NUMBER: 113655

# COLLEAGUES WITH WHOM YOU DISCUSSED THIS ASSIGNMENT (names, numbers):
# - Tiago Albuquerque, Nº 112901

from semantic_network import *
from constraintsearch import *
from bayes_net import *
from collections import defaultdict, Counter
from itertools import product, combinations

class MySN(SemanticNetwork):

    def __init__(self):
        SemanticNetwork.__init__(self)

    def relation_type_counts(self, relname):
        counts = {'AssocSome':0,'AssocOne':0,'AssocNum':0}
        for d in self.declarations:
            if d.relation.name == relname:
                if isinstance(d.relation, AssocSome):
                    counts['AssocSome'] += 1
                elif isinstance(d.relation, AssocOne):
                    counts['AssocOne'] += 1
                elif isinstance(d.relation, AssocNum):
                    counts['AssocNum'] += 1
        if all(v==0 for v in counts.values()):
            return None
        return max(counts.keys(), key=lambda k: counts[k])

    def is_type(self, entity):
        for d in self.declarations:
            if isinstance(d.relation, Subtype) and d.relation.entity2 == entity:
                return True
            if isinstance(d.relation, Member):
                if d.relation.entity2 == entity:
                    return True
                if d.relation.entity1 == entity:
                    return False
        return True

    def get_parents(self, entity):
        relation_type = Subtype if self.is_type(entity) else Member
        return [d.relation.entity2 for d in self.declarations if isinstance(d.relation, relation_type) and d.relation.entity1 == entity]


    def dfs(self, entity, visited):
        for parent in self.get_parents(entity):
            if parent not in visited:
                visited.add(parent)
                self.dfs(parent, visited)

    def get_all_ancestors(self, entity):
        ancestors = set()
        self.dfs(entity, ancestors)
        return ancestors

    # General query method, processing different types of
    # relations according to their specificities
    def query(self, entity, relname):
        if relname in ['member', 'subtype']:
            return [d.relation.entity2 for d in self.query_local(e1=entity, relname=relname)]

        assoc_type = self.relation_type_counts(relname)
        if assoc_type is None:
            return []

        ancestors = [entity] + sorted(self.get_all_ancestors(entity))
        if assoc_type == 'AssocSome':
            return self._query_assoc_some(ancestors, relname)
        elif assoc_type == 'AssocOne':
            return self._query_assoc_one(ancestors, relname)
        elif assoc_type == 'AssocNum':
            return self._query_assoc_num(ancestors, relname)

        return []

    def _query_assoc_some(self, ancestors, relname):
        vals = []
        for ent in ancestors:
            for d in self.declarations:
                if d.relation.name == relname and isinstance(d.relation, AssocSome) and d.relation.entity1 == ent:
                    vals.append(d.relation.entity2)
        return vals

    def _query_assoc_one(self, ancestors, relname):
        for ent in ancestors:
            candidate_vals = [d.relation.entity2 for d in self.declarations
                              if d.relation.name == relname and isinstance(d.relation, AssocOne) and d.relation.entity1 == ent]
            if candidate_vals:
                return [Counter(candidate_vals).most_common(1)[0][0]]
        return []

    def _query_assoc_num(self, ancestors, relname):
        for ent in ancestors:
            candidate_vals = [float(d.relation.entity2) for d in self.declarations
                              if d.relation.name == relname and isinstance(d.relation, AssocNum) and d.relation.entity1 == ent]
            if candidate_vals:
                return [sum(candidate_vals) / len(candidate_vals)]
        return []

class MyBN(BayesNet):

    def __init__(self):
        BayesNet.__init__(self)

    def mothers(self, var):
        moms = set()
        if var in self.dependencies:
            for mother_tuple in self.dependencies[var]:
                moms.update(mother_tuple[0])
                moms.update(mother_tuple[1])
        return moms

    def ancestors(self, var):
        visited = set()
        stack = [var]
        while stack:
            current = stack.pop()
            if current not in visited:
                visited.add(current)
                stack.extend(self.mothers(current) - visited)
        visited.discard(var)
        return visited

    def undirected_edges(self, variables):
        edges = set()
        for v in variables:
            moms = self.mothers(v)
            for m in moms:
                edges.add(tuple(sorted((v, m))))
            for m1, m2 in combinations(moms, 2):
                edges.add(tuple(sorted((m1, m2))))
        return list(edges)

    def test_independence(self, v1, v2, given):
        relevant_vars = self.build_relevant_vars(v1, v2, given)
        edges = self.undirected_edges(relevant_vars)
        given_set = set(given)
        final_edges = self.build_final_edges(edges, given_set)
        adj = self.build_adjacency_list(final_edges)
        found_path = self.bfs_path_exists(adj, v1, v2)
        final_edges = sorted(final_edges)
        independent = not found_path
        return (final_edges, independent)

    def build_relevant_vars(self, v1, v2, given):
        vars_set = set([v1, v2] + given)
        for v in [v1, v2] + given:
            vars_set.update(self.ancestors(v))
        return vars_set

    def build_final_edges(self, edges, given_set):
        final_edges = []
        for e in edges:
            if not (given_set & set(e)):
                final_edges.append(e)
        return final_edges

    def build_adjacency_list(self, edges):
        adj = defaultdict(set)
        for (x, y) in edges:
            adj[x].add(y)
            adj[y].add(x)
        return adj

    def bfs_path_exists(self, adj, start, goal):
        visited = set()
        queue = [start]
        while queue:
            cur = queue.pop()
            if cur == goal:
                return True
            if cur in visited:
                continue
            visited.add(cur)
            for neigh in adj[cur]:
                if neigh not in visited:
                    queue.append(neigh)
        return False

class MyCS(ConstraintSearch):

    def __init__(self,domains,constraints):
        ConstraintSearch.__init__(self,domains,constraints)

    def backtrack(self, domains, solutions=None, visited_solutions=None):
        if any(len(dom) == 0 for dom in domains.values()):
            return
        if all(len(dom) == 1 for dom in domains.values()):
            solution = {var: dom[0] for var, dom in domains.items()}
            solution_tuple = tuple(sorted(solution.items()))
            if solution_tuple not in visited_solutions:
                visited_solutions.add(solution_tuple)
                solutions.append(solution)
            return
        
        var = min((v for v in domains if len(domains[v]) > 1), key=lambda x: len(domains[x]))

        for value in domains[var]:
            new_domains = dict(domains)
            new_domains[var] = [value]
            self.propagate(new_domains, var)
            if not any(len(d) == 0 for d in new_domains.values()):
                self.backtrack(new_domains, solutions, visited_solutions)

    def search_all(self, domains=None):
        if domains is None:
            domains = self.domains
        
        solutions = []
        visited_solutions = set()
        self.backtrack(domains, solutions, visited_solutions)

        return solutions

def handle_ho_constraint(domains, constraints, variables, constraint):
    aux_var = ''.join(variables)
    var_domains = [domains[v] for v in variables]
    valid_tuples = [t for t in product(*var_domains) if constraint(t)]

    domains[aux_var] = valid_tuples

    for i, v in enumerate(variables):
        constraints[(aux_var, v)] = lambda av, xt, ov, x, idx=i: xt[idx] == x
        constraints[(v, aux_var)] = lambda ov, x, av, xt, idx=i: xt[idx] == x

