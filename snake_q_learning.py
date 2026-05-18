import argparse
import random
import tkinter as tk
from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, List, Optional, Tuple


Point = Tuple[int, int]
State = Tuple[int, ...]


UP = (0, -1)
RIGHT = (1, 0)
DOWN = (0, 1)
LEFT = (-1, 0)
DIRECTIONS = [UP, RIGHT, DOWN, LEFT]

ACTION_STRAIGHT = 0
ACTION_LEFT = 1
ACTION_RIGHT = 2
ACTION_UTURN = 3
ACTION_NAMES = {
    ACTION_STRAIGHT: "Straight",
    ACTION_LEFT: "Left",
    ACTION_RIGHT: "Right",
    ACTION_UTURN: "U-Turn",
}


def add_points(a: Point, b: Point) -> Point:
    return a[0] + b[0], a[1] + b[1]


def rotate_direction(direction: Point, action: int) -> Point:
    idx = DIRECTIONS.index(direction)
    if action == ACTION_STRAIGHT:
        return DIRECTIONS[idx]
    if action == ACTION_LEFT:
        return DIRECTIONS[(idx - 1) % 4]
    if action == ACTION_RIGHT:
        return DIRECTIONS[(idx + 1) % 4]
    if action == ACTION_UTURN:
        return DIRECTIONS[(idx + 2) % 4]
    raise ValueError(f"Unsupported action: {action}")


@dataclass
class StepResult:
    reward: float
    done: bool
    score: int


class SnakeEnv:
    def __init__(self, width: int = 12, height: int = 12, seed: Optional[int] = None) -> None:
        self.width = width
        self.height = height
        self.random = random.Random(seed)
        self.snake: Deque[Point] = deque()
        self.direction: Point = RIGHT
        self.food: Point = (0, 0)
        self.score = 0
        self.steps = 0
        self.starvation_limit = width * height * 2
        self.reset()

    def reset(self) -> State:
        start_x = self.width // 2
        start_y = self.height // 2
        self.snake = deque(
            [
                (start_x, start_y),
                (start_x - 1, start_y),
                (start_x - 2, start_y),
            ]
        )
        self.direction = RIGHT
        self.score = 0
        self.steps = 0
        self.food = self._spawn_food()
        return self.get_state()

    def _spawn_food(self) -> Point:
        occupied = set(self.snake)
        choices = [
            (x, y)
            for x in range(self.width)
            for y in range(self.height)
            if (x, y) not in occupied
        ]
        return self.random.choice(choices)

    def _is_collision(self, point: Point, include_tail: bool = True) -> bool:
        x, y = point
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return True

        body = list(self.snake)
        if not include_tail and body:
            body = body[:-1]
        return point in body

    def _food_distance(self) -> int:
        head = self.snake[0]
        return abs(head[0] - self.food[0]) + abs(head[1] - self.food[1])

    def get_state(self) -> State:
        head = self.snake[0]
        forward = rotate_direction(self.direction, ACTION_STRAIGHT)
        left_dir = rotate_direction(self.direction, ACTION_LEFT)
        right_dir = rotate_direction(self.direction, ACTION_RIGHT)

        point_straight = add_points(head, forward)
        point_left = add_points(head, left_dir)
        point_right = add_points(head, right_dir)

        state = (
            int(self._is_collision(point_straight)),
            int(self._is_collision(point_left)),
            int(self._is_collision(point_right)),
            int(self.direction == UP),
            int(self.direction == RIGHT),
            int(self.direction == DOWN),
            int(self.direction == LEFT),
            int(self.food[1] < head[1]),
            int(self.food[0] > head[0]),
            int(self.food[1] > head[1]),
            int(self.food[0] < head[0]),
        )
        return state

    def step(self, action: int) -> StepResult:
        self.steps += 1
        old_distance = self._food_distance()
        new_direction = rotate_direction(self.direction, action)
        next_head = add_points(self.snake[0], new_direction)

        will_eat = next_head == self.food
        if self._is_collision(next_head, include_tail=will_eat):
            return StepResult(reward=-10.0, done=True, score=self.score)

        self.direction = new_direction
        self.snake.appendleft(next_head)

        reward = -0.1
        if will_eat:
            self.score += 1
            # Reset the starvation counter whenever the snake makes progress.
            self.steps = 0
            reward = 12.0
            if len(self.snake) == self.width * self.height:
                return StepResult(reward=reward + 25.0, done=True, score=self.score)
            self.food = self._spawn_food()
        else:
            self.snake.pop()
            new_distance = self._food_distance()
            if new_distance < old_distance:
                reward += 0.4
            elif new_distance > old_distance:
                reward -= 0.4

        if self.steps >= self.starvation_limit:
            return StepResult(reward=-5.0, done=True, score=self.score)

        return StepResult(reward=reward, done=False, score=self.score)


class QLearningAgent:
    def __init__(
        self,
        alpha: float = 0.15,
        gamma: float = 0.9,
        epsilon: float = 1.0,
        epsilon_min: float = 0.02,
        epsilon_decay: float = 0.995,
    ) -> None:
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.q_table: Dict[State, List[float]] = {}

    def _ensure_state(self, state: State) -> List[float]:
        if state not in self.q_table:
            self.q_table[state] = [0.0, 0.0, 0.0, 0.0]
        return self.q_table[state]

    def choose_action(self, state: State, exploit_only: bool = False) -> int:
        q_values = self._ensure_state(state)
        if not exploit_only and random.random() < self.epsilon:
            return random.randrange(4)

        best_value = max(q_values)
        best_actions = [index for index, value in enumerate(q_values) if value == best_value]
        return random.choice(best_actions)

    def update(self, state: State, action: int, reward: float, next_state: State, done: bool) -> None:
        q_values = self._ensure_state(state)
        next_q_values = self._ensure_state(next_state)
        target = reward if done else reward + self.gamma * max(next_q_values)
        q_values[action] += self.alpha * (target - q_values[action])

    def decay_exploration(self) -> None:
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)


class Trainer:
    def __init__(self, env: SnakeEnv, agent: QLearningAgent) -> None:
        self.env = env
        self.agent = agent
        self.episode_scores: List[int] = []
        self.best_score = 0
        self.total_episodes = 0

    def run_episode(self, exploit_only: bool = False) -> int:
        state = self.env.reset()
        done = False

        while not done:
            action = self.agent.choose_action(state, exploit_only=exploit_only)
            result = self.env.step(action)
            next_state = self.env.get_state()

            if not exploit_only:
                self.agent.update(state, action, result.reward, next_state, result.done)

            state = next_state
            done = result.done

        if not exploit_only:
            self.agent.decay_exploration()

        self.total_episodes += 1
        self.best_score = max(self.best_score, self.env.score)
        self.episode_scores.append(self.env.score)
        return self.env.score

    def average_score(self, last_n: int = 100) -> float:
        scores = self.episode_scores[-last_n:]
        if not scores:
            return 0.0
        return sum(scores) / len(scores)


class SnakeQLearningApp:
    def __init__(self, cell_size: int = 28) -> None:
        self.env = SnakeEnv(width=12, height=12)
        self.agent = QLearningAgent()
        self.trainer = Trainer(self.env, self.agent)

        self.cell_size = cell_size
        self.margin = 12
        self.training_running = False
        self.play_running = False
        self.games_played = 0
        self.play_delay_ms = 55
        self.board_cells: Dict[Point, int] = {}
        self.eye_ids: List[int] = []
        self.action_text_id: Optional[int] = None

        self.root = tk.Tk()
        self.root.title("Snake Q-Learning")
        self.root.configure(bg="#f6f1e7")

        board_width = self.env.width * self.cell_size
        board_height = self.env.height * self.cell_size
        window_width = board_width + (self.margin * 2)
        window_height = board_height + 128

        self.canvas = tk.Canvas(
            self.root,
            width=board_width,
            height=board_height,
            bg="#14342b",
            highlightthickness=0,
        )
        self.canvas.pack(padx=self.margin, pady=(self.margin, 8))
        self.canvas.pack_propagate(False)

        controls = tk.Frame(self.root, bg="#f6f1e7")
        controls.pack(fill="x", padx=self.margin, pady=(0, self.margin))

        self.train_button = tk.Button(controls, text="Train 500 Episodes", command=self.start_training)
        self.train_button.pack(side="left", padx=(0, 8))

        self.play_button = tk.Button(controls, text="Watch Best Policy", command=self.start_play)
        self.play_button.pack(side="left", padx=(0, 8))

        self.reset_button = tk.Button(controls, text="Reset Agent", command=self.reset_agent)
        self.reset_button.pack(side="left")

        self.status_var = tk.StringVar()
        self.status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
            justify="left",
            bg="#f6f1e7",
            fg="#1f2a24",
            font=("Segoe UI", 10),
            wraplength=window_width - (self.margin * 2),
            height=2,
        )
        self.status_label.pack(fill="x", padx=self.margin, pady=(0, self.margin))

        self.root.resizable(False, False)
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.minsize(window_width, window_height)
        self.root.maxsize(window_width, window_height)

        self._build_board()
        self._set_status("Ready to train a table-based Q-learning snake.")
        self._draw_board()

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)

    def reset_agent(self) -> None:
        self.training_running = False
        self.play_running = False
        self.agent = QLearningAgent()
        self.trainer = Trainer(self.env, self.agent)
        self.games_played = 0
        self.env.reset()
        self._draw_board()
        self._set_status("Agent reset. Q-table cleared.")

    def start_training(self) -> None:
        if self.training_running:
            return
        self.play_running = False
        self.training_running = True
        self._set_status("Training 500 episodes...")
        self._train_chunk(remaining=500, chunk_size=25)

    def _train_chunk(self, remaining: int, chunk_size: int) -> None:
        if not self.training_running:
            return

        current_chunk = min(remaining, chunk_size)
        for _ in range(current_chunk):
            self.trainer.run_episode(exploit_only=False)

        self._draw_board()
        avg_score = self.trainer.average_score()
        self._set_status(
            "Training... "
            f"Episodes: {self.trainer.total_episodes} | "
            f"Best score: {self.trainer.best_score} | "
            f"Avg(100): {avg_score:.2f} | "
            f"Epsilon: {self.agent.epsilon:.3f} | "
            f"Known states: {len(self.agent.q_table)}"
        )

        remaining -= current_chunk
        if remaining > 0:
            self.root.after(1, lambda: self._train_chunk(remaining, chunk_size))
        else:
            self.training_running = False
            self._set_status(
                "Training complete. "
                f"Episodes: {self.trainer.total_episodes} | "
                f"Best score: {self.trainer.best_score} | "
                f"Avg(100): {self.trainer.average_score():.2f}"
            )

    def start_play(self) -> None:
        if self.play_running:
            return
        self.training_running = False
        self.play_running = True
        self.games_played = 0
        self.env.reset()
        self._set_status("Running the learned greedy policy.")
        self._play_step()

    def _play_step(self) -> None:
        if not self.play_running:
            return

        state = self.env.get_state()
        action = self.agent.choose_action(state, exploit_only=True)
        result = self.env.step(action)
        self._draw_board(action=action)

        if result.done:
            self.games_played += 1
            summary = (
                f"Policy game {self.games_played} finished | "
                f"Score: {result.score} | "
                f"Best learned score: {self.trainer.best_score} | "
                f"Known states: {len(self.agent.q_table)}"
            )
            self._set_status(summary)
            self.env.reset()
            self.root.after(500, self._play_step)
            return

        self._set_status(
            f"Watching policy | Score: {self.env.score} | "
            f"Action: {ACTION_NAMES[action]} | "
            f"Known states: {len(self.agent.q_table)}"
        )
        self.root.after(self.play_delay_ms, self._play_step)

    def _build_board(self) -> None:
        for x in range(self.env.width):
            for y in range(self.env.height):
                x1 = x * self.cell_size
                y1 = y * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                cell_id = self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill="#173d31",
                    outline="#1c4739",
                    width=1,
                )
                self.board_cells[(x, y)] = cell_id

        self.action_text_id = self.canvas.create_text(
            8,
            8,
            anchor="nw",
            fill="#f6f1e7",
            text="",
            font=("Segoe UI", 10, "bold"),
        )

        self.eye_ids = [
            self.canvas.create_oval(0, 0, 0, 0, fill="#102018", outline=""),
            self.canvas.create_oval(0, 0, 0, 0, fill="#102018", outline=""),
        ]

    def _draw_cell(self, point: Point, color: str) -> None:
        cell_id = self.board_cells[point]
        self.canvas.itemconfig(cell_id, fill=color)

    def _position_head_eyes(self, head: Point) -> None:
        x1 = head[0] * self.cell_size
        y1 = head[1] * self.cell_size
        eye_offset = self.cell_size // 4
        eye_size = max(2, self.cell_size // 10)

        coords = [
            (
                x1 + eye_offset,
                y1 + eye_offset,
                x1 + eye_offset + eye_size,
                y1 + eye_offset + eye_size,
            ),
            (
                x1 + self.cell_size - eye_offset - eye_size,
                y1 + eye_offset,
                x1 + self.cell_size - eye_offset,
                y1 + eye_offset + eye_size,
            ),
        ]
        for eye_id, eye_coords in zip(self.eye_ids, coords):
            self.canvas.coords(eye_id, *eye_coords)

    def _draw_board(self, action: Optional[int] = None) -> None:
        for x in range(self.env.width):
            for y in range(self.env.height):
                self._draw_cell((x, y), "#173d31")

        self._draw_cell(self.env.food, "#f95738")

        for idx, segment in enumerate(self.env.snake):
            color = "#9fe870" if idx == 0 else "#5fcf65"
            self._draw_cell(segment, color)

        head = self.env.snake[0]
        self._position_head_eyes(head)

        if action is not None:
            self.canvas.itemconfig(self.action_text_id, text=f"Action: {ACTION_NAMES[action]}")
        else:
            self.canvas.itemconfig(self.action_text_id, text="")

    def run(self) -> None:
        self.root.mainloop()


def run_cli_training(episodes: int, width: int, height: int, seed: Optional[int]) -> None:
    env = SnakeEnv(width=width, height=height, seed=seed)
    agent = QLearningAgent()
    trainer = Trainer(env, agent)

    for episode in range(1, episodes + 1):
        score = trainer.run_episode(exploit_only=False)
        if episode % 100 == 0 or episode == episodes:
            print(
                f"Episode {episode:5d} | "
                f"score={score:2d} | "
                f"best={trainer.best_score:2d} | "
                f"avg100={trainer.average_score():.2f} | "
                f"epsilon={agent.epsilon:.3f} | "
                f"states={len(agent.q_table)}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Snake game with a table-based Q-learning agent.")
    parser.add_argument("--cli-train", type=int, default=0, help="Train for N episodes without opening the UI.")
    parser.add_argument("--width", type=int, default=12, help="Board width for CLI training.")
    parser.add_argument("--height", type=int, default=12, help="Board height for CLI training.")
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed.")
    args = parser.parse_args()

    if args.cli_train > 0:
        run_cli_training(args.cli_train, args.width, args.height, args.seed)
        return

    app = SnakeQLearningApp()
    app.run()


if __name__ == "__main__":
    main()
