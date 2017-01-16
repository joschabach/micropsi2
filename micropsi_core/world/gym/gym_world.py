
import numpy as np


from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import ArrayWorldAdapter

import gym

floatX = 'float32' # where do we configure this?


def inspect_space(gym_space, verbose=False):
    """
    find the dimensionaltity and (if discrete) number of values of an OAI state/action space

    Params
    ----
        gym_space : open ai `gym.spaces.Box` or `gym.spaces.Discrete object`

    Returns
    ----
        n_dim: int
            nr of dimensions of the space

        n_discrete: int or None
            if the space is discrete: the nr n of allowed values, which are the integers {0,...,n}

        checkbounds: callable
            clips a given vector to the bounds of the space and optionally emits a punishment if the bounds had been violated.
    """
    if isinstance(gym_space, gym.spaces.Box):
        n_dim = gym_space.shape[0]
        n_discrete = False
        lo, hi = gym_space.low, gym_space.high
        if verbose:
            print('lower bounds: {}\n upper bounds{}'.format(lo, hi))
        def checkbounds(action):
            bounded_action = np.clip(action, lo, hi)
            punishment = 0 * np.sum(abs(action - bounded_action))
            if punishment != 0:
                print("action {} violated bounds {}, {}. executed bounded action {} and punished by {}".format(action, lo, hi, bounded_action, punishment))
            return bounded_action, punishment

    elif isinstance(gym_space, gym.spaces.Discrete):
        n_dim = 1
        n_discrete = gym_space.n
        checkbounds = lambda action: (action,0)
    else:
        # some OAI envs have discrete action spaces with
        # more than 2 action choices, or even multiple dimensions
        # with some nr of discrete choices in each. so far we don't
        # deal with that.
        raise Exception('OAI worldadapter currently requires environments with continuous or 1D discrete state/action spaces')
    return n_dim, n_discrete, checkbounds


class OAIGym(World):

    supported_worldadapters = ['OAIGymAdapter']

    def __init__(self, filename, world_type="OAIGym", name="", owner="", engine=None, uid=None, version=1, config={}):
        World.__init__(self, filename, world_type=world_type, name=name, owner=owner, uid=uid, version=version)

        self.env = gym.make(config['env_id'])
        self.time_limit = config['time_limit']

        self.n_dim_state, self.n_discrete_states, _ = inspect_space(self.env.observation_space)
        self.n_dim_action, self.n_discrete_actions, self.checkbounds = inspect_space(self.env.action_space, verbose=True)

        self.rendering = True

    @classmethod
    def get_config_options(cls):
        print('### oai world get config')
        return [
            {'name': 'env_id',
             'description': 'OpenAI environment ID',
             'default': 'CartPole-v0',
             'time_limit': 500}
        ]



class OAIGymAdapter(ArrayWorldAdapter):

    def __init__(self, world, uid=None, inertia=0., **data):
        super().__init__(world, uid, **data)

        # 1D discrete state space: one data source for each possible state
        if self.world.n_discrete_states:
            for k in range(self.world.n_discrete_states):
                self.add_datasource("s%d" % k)
        # continuous state space: one data source for each state dimension
        else:
            for state_dim in range(self.world.n_dim_state):
                self.add_datasource("s%d" % state_dim)

        # 1D discrete action space: one data target for each possible action
        if self.world.n_discrete_actions:
            for k in range(self.world.n_discrete_actions):
                self.add_datatarget("a%d" % k)
        # continuous action space: one data target for each action dimension
        else:
            for action_dim in range(self.world.n_dim_action):
                self.add_datatarget("a%d" % action_dim)

        self.add_datatarget("restart")

        self.add_datasource("reward")
        self.add_datasource("is_terminal")
        self.inertia = inertia
        self.last_action = 0
        self.t_this_episode = 0

    def update_data_sources_and_targets(self):
        # print('\nworldadapter.update, datatarget values:\n', self.datatarget_values)
        self.t_this_episode += 1
        action_values = self.datatarget_values[0:-1] # all datatarget values except 'restart'
        restart = self.datatarget_values[-1]
        punishment = 0

        if restart > 0:
            obs = self.world.env.reset()
            r = 0
            terminal = False
        else:
            if self.world.n_discrete_actions:
                # for discrete action spaces, each action is represented by one datatarget, and
                # considered active if it's nonzero. the agent needs to make sure only one is active.
                # OAI expects an integer < n, encoding which of the n available actions to take. so:
                action = np.where(action_values)[0]
                if len(action)>1:
                    raise Exception('Cannot do multiple actions at the same time in a discrete, 1D action space.')
                elif len(action) == 0:
                    action = 0
                    print('No action given - choosing first action')
                else:
                    action = action[0].item()
            else:
                if self.inertia > 0:
                    action_values = self.last_action*self.inertia + action_values*(1-self.inertia)
                    self.last_action = action_values
                action, punishment = self.world.checkbounds(action_values)

            obs, r, terminal, info = self.world.env.step(action)

        if self.world.rendering:
            self.world.env.render()

        if self.world.n_discrete_states:
            # for discrete state spaces, OAI returns its observation as a single integer < n,
            # indicating which of the n states it is in. we have one data source for each state,
            # taking values 0 or 1. so:
            obs_vector = np.zeros(self.world.n_discrete_states)
            obs_vector[obs] = 1
        else:
            obs_vector = obs

        if self.t_this_episode >= self.world.time_limit:
            terminal = True
            self.t_this_episode = 0

        state = np.concatenate([obs_vector, [r+punishment], [int(terminal)]])
        self.datasource_values = np.array(state, dtype=floatX)
        # print('\nworldadapter.update, datasource values:\n', self.datasource_values)

    def reset_datatargets(self):
        """ resets (zeros) the datatargets """
        self.datatarget_values[:] = 0.0


if __name__ == '__main__':

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

    for env_id in environment_ids:
        env = gym.make(env_id)
        print(env.spec.id)
        print('obs:, ', env.observation_space)
        print('action:', env.action_space)
        print()
        # import ipdb; ipdb.set_trace(context=6)