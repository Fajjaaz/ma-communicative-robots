""" Filename:     RL.py
    Author(s):    Thomas Bellucci
    Description:  Implementation of Upper Confidence Bounds (UCB) used to
                  select Thoughts generated by the RLChatbot to verbalize.
    Date created: Nov. 11th, 2021
"""

import json
import os
import random

import matplotlib.pyplot as plt
import numpy as np


class UCB:
    def __init__(self, c=2, tmax=1e10):
        """Initializes an instance of the Upper Confidence Bound
        (UCB) reinforcement learning algorithm.

        params
        float c:          controls level of exploration
        float tmax:       number of timesteps in which uncertainty of choices
                          are taken into account (exploitation when t > tmax)

        float t:          timestep
        float decay:      decay rate of exploration constant c
        float Q:          stores the estimate of the expected reward for each action
        float N:          stores the number of updates performed on each action

        returns: UCB object
        """
        self.__Q = dict()
        self.__N = dict()

        self.__t = 1
        self.__c = c
        self.__decay = c / tmax

    # Utils

    def load(self, filename):
        """Reads utility values from file.

        params
        str filename: filename of file with utilities.

        returns: None
        """
        if filename is None:
            return

        if not os.path.isfile(filename):  # File exists?
            print("WARNING %s does not yet exist" % filename)
            return

        with open(filename, "r") as file:
            data = json.load(file)
            self.__c = data["metadata"]["c"]
            self.__t = data["metadata"]["t"]
            self.__decay = data["metadata"]["decay"]

            for action, values in data["data"].items():
                self.__Q[action] = values["value"]
                self.__N[action] = values["count"]

    def save(self, filename):
        """Writes the value and uncertainty tables to a JSON file.

        params
        str filename: filename of the ouput file.

        returns: None
        """
        # Format metadata (c, t, decay) and value estimates as JSON.
        data = {
            "metadata": {"c": self.__c, "t": self.__t, "decay": self.__decay},
            "data": dict(),
        }

        for action in self.__Q.keys():
            if self.__N[action] > 0:
                data["data"][action] = {
                    "value": self.__Q[action],
                    "count": self.__N[action],
                    "uncertainty": self.__uncertainty(action),
                }
        # Write to file
        with open(filename, "w") as file:
            json.dump(data, file)

    # Learning

    def __uncertainty(self, action):
        """Computes the uncertainty associated with the current action
        as the upper confidence bound of the current average.

        params
        str action: an action

        returns:    UCB score of the action
        """
        return self.__c * np.sqrt(np.log(self.__t) / self.__N[action])

    def select_action(self, actions):
        """Selects an action from the set of available actions that maximizes
        the average observed reward, taking into account uncertainty.

        params
        list actions: List of actions from which to select

        returns: action
        """
        action_scores = []
        for action in actions:

            # Compute UCB score for each element of the action
            score = []
            for elem in action.split():

                # Add unseen elements to table
                if elem not in self.__Q:
                    self.__Q[elem] = 0
                    self.__N[elem] = 0

                # Score action
                if self.__N[elem] == 0:
                    score += [np.inf]  # ensures all actions are sampled at least once
                else:
                    score += [self.__Q[elem] + self.__uncertainty(elem)]

            # Convert element-scores into action score
            action_scores.append((action, np.mean(score)))

        # Greedy selection
        selected_action, _ = max(action_scores, key=lambda x: x[1])
        return selected_action

    def update_utility(self, action, reward):
        """Updates the action-value table (Q) by incrementally updating the
        reward estimate of the action elements with the observed reward.

        params
        str action:    selected action (with elements elem that are scored)
        float reward:  reward obtained after performing the action

        returns: None
        """
        # Update value estimates
        for elem in action.split():
            self.__N[elem] += 1
            self.__Q[elem] = self.__Q[elem] + (reward - self.__Q[elem]) / self.__N[elem]

        # Update exploration constant
        self.__t += 1
        self.__c = max(self.__c - self.__decay, 0)

    # Plotting

    def plot(self, max_bars=16):
        """Plots the value estimates for each action and their associated
        uncertainties in a bar plot.

        params
        float margin: Margin between bars

        returns: None
        """
        total_rewards = sum(self.__N.values())  # empty value table?
        if total_rewards == 0:
            print("WARNING Cannot plot empty value table")
            return

        # Estimate value/uncertainty of actions
        a, q, u = [], [], []
        for action in sorted(list(self.__Q.keys())):
            if self.__N[action] > 0:
                a += [action]
                q += [self.__Q[action]]
                u += [self.__uncertainty(action)]

        # Reduce number of bars if > max_bars
        if len(a) > max_bars:
            idx = random.sample(range(len(a)), max_bars)
            a = [a[i] for i in idx]
            q = list(np.array(q)[idx])
            u = list(np.array(u)[idx])

        # Draw barplots for U and Q
        fig = plt.figure(figsize=(10, 5), tight_layout=True)
        plt.suptitle("$t=${}, $c=${}".format(self.__t, round(self.__c, 3)))

        plt.subplot(1, 2, 1)
        plt.ylabel("$Uncertainty$ $(U)$")
        plt.xlabel("$Actions$ $(a)$")
        plt.xticks(range(len(a)), a, rotation=45, ha="right")
        plt.bar(range(len(a)), u)

        plt.subplot(1, 2, 2)
        plt.ylabel("$Value$ $(Q)$")
        plt.xlabel("$Actions$ $(a)$")
        plt.xticks(range(len(a)), a, rotation=45, ha="right")
        plt.bar(range(len(a)), q)
        plt.show()


"""
# Toy example with binomial rewards
if __name__ == "__main__":
    num_actions = 10
    actions = np.arange(num_actions).astype(str)
    prob_reward = np.linspace(0.0, 1.0, num_actions)
    N = 150

    ucb = UCB(10, 200)
    for k in range(N):
        # What actions are available?
        n = np.random.randint(3, num_actions)
        idx = np.random.choice(np.arange(num_actions), size=n, replace=False)

        # What action to we pick?
        sampled_actions = actions[idx]
        action = ucb.select_action(sampled_actions)
        print(sampled_actions, action)

        # Draw reward from binomial distribution
        reward = np.random.binomial(1, prob_reward[int(action)])

        # Update action reward
        ucb.update_utility(action, reward)

    ucb.plot()
"""
