
import numpy as np

from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import ArrayWorldAdapter

import gym


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
            if the space is discrete: the nr n of allowed values, which are the integers 0 to n.

        checkbounds: callable
            clips a given vector to the bounds of the space and optionally emits a bounds_punishment if the bounds had been violated.
    """
    if isinstance(gym_space, gym.spaces.Box):
        n_dim = gym_space.shape[0]
        n_discrete = False
        lo, hi = gym_space.low, gym_space.high
        if verbose:
            print('lower bounds: {}\n upper bounds{}'.format(lo, hi))

        def checkbounds(action):
            bounded_action = np.clip(action, lo, hi)
            bounds_punishment = 0 * np.sum(abs(action - bounded_action))
            if bounds_punishment != 0 and verbose:
                print("action {} violated bounds {}, {}. executed bounded action {} and punished by {}".format(action, lo, hi, bounded_action, bounds_punishment))
            return bounded_action, bounds_punishment

    elif isinstance(gym_space, gym.spaces.Discrete):
        n_dim = 1
        n_discrete = gym_space.n

        def checkbounds(action):
            return (action, 0)
    else:
        # some OAI envs have multidimensional discrete action spaces
        # (represented as tuples of gym.spaces.Discrete or gym.spaces.MultiDiscrete).
        # We don't deal with that for now.
        raise Exception('OAI worldadapter currently requires environments with either continuous or binary discrete action spaces')
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
        return [
            {'name': 'env_id',
             'description': 'OpenAI environment ID',
             'default': 'CartPole-v0',
             'time_limit': 500}
        ]


class OAIGymAdapter(ArrayWorldAdapter):

    def __init__(self, world, uid=None, inertia=0., **data):
        super().__init__(world, uid, **data)

        # in case of a 1D discrete state space:
        # one sensor dimension for each possible state
        if self.world.n_discrete_states:
            self.add_flow_datasource("state", shape=(1, self.world.n_discrete_states))
        # for a continuous state space, sensor dimensions match the state space
        else:
            self.add_flow_datasource("state", shape=(1, self.world.n_dim_state))

        # similarly, separate dimension for each discrete action:
        if self.world.n_discrete_actions:
            self.add_flow_datatarget("action", shape=(1, self.world.n_discrete_actions))
        else:
            self.add_flow_datatarget("action", shape=(1, self.world.n_dim_action))

        self.add_flow_datasource("reward", shape=1)
        self.add_flow_datasource("is_terminal", shape=1)

        self.add_flow_datatarget("restart", shape=1)

        self.inertia = inertia
        self.last_action = 0
        self.t_this_episode = 0

    def update_data_sources_and_targets(self):
        bounds_punishment = 0
        self.t_this_episode += 1
        action_values = self.get_flow_datatarget('action').ravel()
        restart = self.get_flow_datatarget('restart')

        if restart > 0:
            obs = self.world.env.reset()
            r = 0
            terminal = False
        else:
            if self.world.n_discrete_actions:
                # For discrete action spaces, each action is represented by one datatarget dimension.
                # OAI expects some integer < n encoding which of the n available actions to take.
                # For that, we use the index of the most strongly activated datatarget dimension. This matches
                # well to e.g. a softmax layer feeding into the action datatarget.
                action = np.argmax(action_values)
            else:
                if self.inertia > 0:
                    action_values = self.last_action * self.inertia + action_values * (1 - self.inertia)
                    self.last_action = action_values
                action, bounds_punishment = self.world.checkbounds(action_values)

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

        self.set_flow_datasource("state", obs_vector)
        self.set_flow_datasource("reward", r + bounds_punishment)
        self.set_flow_datasource("is_terminal", int(terminal))
