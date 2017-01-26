import gym

environment_ids = ['CartPole-v0',
                    'CartPole-v1',
                    'Acrobot-v1',
                    'MountainCar-v0',
                    'MountainCarContinuous-v0',
                    'Pendulum-v0',
                    'LunarLander-v2',
                    'LunarLanderContinuous-v2',
                    'BipedalWalker-v2',
                    'Copy-v0',
                    'Reverse-v0',
                     ]

envs = {}
for env_id in environment_ids:
    env = gym.make(env_id)
    envs[env_id] = env
    print(env.spec.id)
    print('obs:, ', env.observation_space)
    print('action:', env.action_space)
    print()
    # import ipdb; ipdb.set_trace(context=6)