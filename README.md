# Snake Game with Q-Learning

This is a small Python project where I trained a Snake agent using tabular Q-learning instead of a neural network.

The goal was to keep the learning side simple and readable:

- the agent stores state-action values in a Q-table
- the state is built from 11 hand-crafted features
- the action space is limited to 4 movement choices
- learning happens through reward updates after each move

There is no deep learning model here, just a lookup table that gradually improves as the agent plays more games.

## State and actions

The state is made from 11 binary features:

- danger straight
- danger left
- danger right
- moving up
- moving right
- moving down
- moving left
- food up
- food right
- food down
- food left

The agent can choose from 4 actions:

- move straight
- turn left
- turn right
- make a U-turn

## Running the project

Launch the desktop app:

```bash
python snake_q_learning.py
```

The Tkinter app includes:

- a fixed-size game window
- a training button for batch learning
- a watch mode for the current greedy policy
- a reset button to clear the Q-table

Run training only in the terminal:

```bash
python snake_q_learning.py --cli-train 1000
```

Example with optional settings:

```bash
python snake_q_learning.py --cli-train 1000 --width 12 --height 12 --seed 7
```

## Learning rule

The Q-table is updated with the standard Q-learning formula:

```text
Q(s, a) = Q(s, a) + alpha * (reward + gamma * max(Q(s', *)) - Q(s, a))
```

Where:

- `alpha` is the learning rate
- `gamma` is the discount factor
- `epsilon` controls exploration during training

## Notes

- The visual game uses Tkinter, so there are no external dependencies for the UI.
- Training starts noisy because the agent explores randomly at first.
- Over time, epsilon decays and the policy becomes more consistent.
