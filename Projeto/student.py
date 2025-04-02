# TEAM MEMBER NAMES AND NUMBERS: José Mendes(114429), Abel Teixeira(113655), Hugo Sousa(112733)

import asyncio
import getpass
import json
import os
import random
import websockets
import heapq

class SnakeAgent:
    def __init__(self, server_address="localhost:8000", agent_name="student"):
        self.server_address = server_address
        self.agent_name = agent_name
        self.key = "d"
        self.opposite_directions = {"w": "s", "s": "w", "a": "d", "d": "a"}
        self.directions = ["w", "a", "s", "d"]
        self.no_food_counter = 0
        self.last_directions = []
        self.map_size = None
        self.full_map = None
        self.target = None
        self.traverse = True
        self.food_memory = set()

    @staticmethod
    def manhattan_distance(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def a_star(self, start, goal, snake_body, traverse, sight):
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.manhattan_distance(start, goal)}

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path

            for direction in self.directions:
                neighbor = self.calculate_new_position(current, direction)
                if not traverse and self.is_collision(neighbor, snake_body, sight):
                    continue

                tentative_g_score = g_score[current] + 1
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.manhattan_distance(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return []

    def avoid_collisions_with_body(self, head, body, sight):
        def evaluate_move(move, head):
            distance = None
            if move == "w":
                for y in range(head[1] - 1, -2, -1):
                    if self.is_collision_with_body((head[0], y), body, sight):
                        distance = abs(head[1] - y)
                        break
            elif move == "s":
                for y in range(head[1] + 1, self.map_size[1]):
                    if self.is_collision_with_body((head[0], y), body, sight):
                        distance = abs(head[1] - y)
                        break
            elif move == "a":
                for x in range(head[0] - 1, -2, -1):
                    if self.is_collision_with_body((x, head[1]), body, sight):
                        distance = abs(head[0] - x)
                        break
            elif move == "d":
                for x in range(head[0] + 1, self.map_size[0]):
                    if self.is_collision_with_body((x, head[1]), body, sight):
                        distance = abs(head[0] - x)
                        break
            return float("inf") if distance is None else distance

        new_position = self.calculate_new_position(head, self.key)
        if not self.is_collision_with_body(new_position, body, sight):
            return self.key

        valid_moves = []
        perpendicular_moves = ["a", "d"] if self.key in ["w", "s"] else ["w", "s"]
        for move in perpendicular_moves:
            move_distance = evaluate_move(move, head)
            valid_moves.append((move, move_distance))

        return max(valid_moves, key=lambda x: x[1])[0] if valid_moves else self.key

    def calculate_direction(self, head, target, current_key, snake_body, sight):
        def is_safe_move(new_head):
            if self.traverse:
                return new_head not in snake_body
            return new_head not in snake_body and not self.is_collision(new_head, snake_body, sight)

        if head[0] < target[0] and current_key != "a":
            new_head = (head[0] + 1, head[1])
            if is_safe_move(new_head):
                return "d"
        if head[0] > target[0] and current_key != "d":
            new_head = (head[0] - 1, head[1])
            if is_safe_move(new_head):
                return "a"
        if head[1] < target[1] and current_key != "w":
            new_head = (head[0], head[1] + 1)
            if is_safe_move(new_head):
                return "s"
        if head[1] > target[1] and current_key != "s":
            new_head = (head[0], head[1] - 1)
            if is_safe_move(new_head):
                return "w"
        return current_key

    def avoid_collisions(self, current_key, head, body, sight):
        def evaluate_move(move, head):
            distance = None
            if move == "w":
                for y in range(head[1] - 1, -2, -1):
                    if self.is_collision((head[0], y), body, sight):
                        distance = abs(head[1] - y)
                        break
            elif move == "s":
                for y in range(head[1] + 1, self.map_size[1] + 1):
                    if self.is_collision((head[0], y), body, sight):
                        distance = abs(head[1] - y)
                        break
            elif move == "a":
                for x in range(head[0] - 1, -2, -1):
                    if self.is_collision((x, head[1]), body, sight):
                        distance = abs(head[0] - x)
                        break
            elif move == "d":
                for x in range(head[0] + 1, self.map_size[0] + 1):
                    if self.is_collision((x, head[1]), body, sight):
                        distance = abs(head[0] - x)
                        break
            return float("inf") if distance is None else distance

        new_position = self.calculate_new_position(head, current_key)
        if not self.is_collision(new_position, body, sight):
            return current_key

        valid_moves = []
        perpendicular_moves = ["a", "d"] if current_key in ["w", "s"] else ["w", "s"]
        for move in perpendicular_moves:
            move_distance = evaluate_move(move, head)
            if move_distance != -1:
                valid_moves.append((move, move_distance))

        return max(valid_moves, key=lambda x: x[1])[0] if valid_moves else current_key

    def calculate_new_position(self, head, direction):
        x, y = head
        if direction == "w":
            return (x, 23) if y - 1 < 0 and self.traverse else (x, y - 1)
        if direction == "s":
            return (x, 0) if y + 1 >= 24 and self.traverse else (x, y + 1)
        if direction == "a":
            return (47, y) if x - 1 < 0 and self.traverse else (x - 1, y)
        if direction == "d":
            return (0, y) if x + 1 >= 48 and self.traverse else (x + 1, y)
        return head

    def is_collision(self, position, body, sight):
        x, y = position
        borda_x = [-1, self.map_size[0]]
        borda_y = [-1, self.map_size[1]]
        return (
            x <= borda_x[0] or x >= borda_x[1] or y <= borda_y[0] or y >= borda_y[1]
            or self.full_map[x][y] == 1
            or sight.get(str(x), {}).get(str(y), 0) == 4
            or (x, y) in body
        )

    def is_collision_with_body(self, position, body, sight):
        x, y = position
        return sight.get(str(x), {}).get(str(y), 0) == 4 or (x, y) in body

    def get_random_empty_position(self):
        empty_positions = [
            (x, y)
            for x in range(self.map_size[0])
            for y in range(self.map_size[1])
            if self.full_map[x][y] == 0 and (self.traverse or self.full_map[x][y] != 1)
        ]
        return random.choice(empty_positions) if empty_positions else None

    def update_full_map(self, sight):
        for x, row in sight.items():
            for y, tile in row.items():
                x, y = int(x), int(y)
                if self.full_map[x][y] == 0:
                    self.full_map[x][y] = 5

    def reset_full_map_to_zeros(self):
        for x in range(self.map_size[0]):
            for y in range(self.map_size[1]):
                if self.full_map[x][y] == 5:
                    self.full_map[x][y] = 0

    async def agent_loop(self):
        async with websockets.connect(f"ws://{self.server_address}/player") as websocket:
            await websocket.send(json.dumps({"cmd": "join", "name": self.agent_name}))
            while True:
                try:
                    state = json.loads(await websocket.recv())

                    if "size" in state and "map" in state:
                        self.map_size = state["size"]
                        self.full_map = state["map"]
                        continue
                    if "body" not in state or "sight" not in state:
                        continue

                    snake_head = tuple(state["body"][0])
                    snake_body = [tuple(pos) for pos in state["body"]]
                    sight = state["sight"]
                    self.traverse = state["traverse"]
                    food_positions = [
                        (int(x), int(y))
                        for x in sight
                        for y, value in sight[x].items()
                        if value in [2, 3]
                    ]
                    self.food_memory.update(food_positions)

                    if self.food_memory:
                        self.no_food_counter = 0
                        closest_food = min(
                            self.food_memory,
                            key=lambda pos: abs(pos[0] - snake_head[0]) + abs(pos[1] - snake_head[1]),
                        )
                        path = self.a_star(snake_head, closest_food, snake_body, self.traverse, sight)
                        if path:
                            self.key = self.calculate_direction(snake_head, path[0], self.key, snake_body, sight)
                        if snake_head == closest_food:
                            self.food_memory.remove(closest_food)
                        self.target = None
                    else:
                        if self.target is None:
                            self.no_food_counter += 1
                            self.update_full_map(sight)

                        if self.no_food_counter > 10 and self.target is None:
                            self.target = self.get_random_empty_position()
                            if self.target:
                                path = self.a_star(snake_head, self.target, snake_body, self.traverse, sight)
                                if path:
                                    self.key = self.calculate_direction(snake_head, path[0], self.key, snake_body, sight)
                            self.reset_full_map_to_zeros()

                        if snake_head == self.target:
                            self.no_food_counter = 0
                            self.reset_full_map_to_zeros()
                            self.target = None
                        else:
                            if self.target:
                                path = self.a_star(snake_head, self.target, snake_body, self.traverse, sight)
                                if path:
                                    next_move = path[0]
                                    self.key = self.calculate_direction(snake_head, next_move, self.key, snake_body, sight)
                        if self.no_food_counter > 25:
                            self.target = (self.get_random_empty_position())
                            self.no_food_counter = 0

                    self.key = self.avoid_collisions_with_body(snake_head, snake_body, sight)

                    if not self.traverse:
                        self.key = self.avoid_collisions(self.key, snake_head, snake_body, sight)

                    self.last_directions.append(self.key)
                    if len(self.last_directions) > 5:
                        self.last_directions.pop(0)

                    await websocket.send(json.dumps({"cmd": "key", "key": self.key}))

                except websockets.exceptions.ConnectionClosedOK:
                    return


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    SERVER = os.environ.get("SERVER", "localhost")
    PORT = os.environ.get("PORT", "8000")
    NAME = os.environ.get("NAME", getpass.getuser())
    agent = SnakeAgent(server_address=f"{SERVER}:{PORT}", agent_name=NAME)
    loop.run_until_complete(agent.agent_loop())
