import gym
import torch
import torch.optim as optim

import utils
import models
import agents
import trainers

### Consts ###############################
N_EPISODE = 100
BUFFER_SIZE = 10000
TRAIN_INTERVAL = 4
INITIAL_WAIT_INTERVAL = 100
BATCH_SIZE = 32
POLICY_UPDATE_INTERVAL = 1000
LR = 0.0003
FRAME_SKIP = 1
SAVE_EPISODE_INTERVAL = 100
##########################################


if __name__ == '__main__':
    env = gym.make('Breakout-v0')

    nAction = env.action_space.n
    buffer = utils.ReplayBuffer(BUFFER_SIZE)

    Q = models.QNet(nAction)
    Q.train()
    QTarget = models.QNet(nAction)
    QTarget.eval()

    opt = optim.Adam(Q.parameters(), lr=LR)

    agent = agents.Agent(nAction, Q)
    trainer = trainers.Trainer(Q, QTarget, opt)

    t = 0
    action = env.action_space.sample()
    for episode in range(N_EPISODE):
        print("episode: %d\n" % (episode + 1))

        observation = env.reset()
        state = torch.cat([utils.preprocess(observation)] * 4, 1)
        sum_reward = 0

        # Exploration loop
        done = False
        while not done:
            env.render()

            if t % FRAME_SKIP == 0:
                action = agent.getAction(state)

            observation, reward, done, _ = env.step(action)
            nextState = torch.cat([state.narrow(1, 1, 3), utils.preprocess(observation)], 1)

            buffer.push(utils.Step(state, action, reward, nextState))
            state = nextState
            sum_reward += reward
            t += 1

            if t < INITIAL_WAIT_INTERVAL:
                continue

            if t % TRAIN_INTERVAL == 0:
                batch = buffer.sample(BATCH_SIZE)
                trainer.update(batch)

            if t % POLICY_UPDATE_INTERVAL == 0:
                QTarget.load_state_dict(Q.state_dict())

        print("  reward %f\n" % sum_reward)

        if episode % SAVE_EPISODE_INTERVAL == 0:
            torch.save(Q.state_dict(), "results/%d.pth" % (episode + 1))
            print("  model saved")

    torch.save(Q.state_dict(), "results/model.pth")
    env.close()