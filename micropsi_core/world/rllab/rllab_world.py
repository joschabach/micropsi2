
import numpy as np
from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import ArrayWorldAdapter

from rllab.envs.box2d.cartpole_env import CartpoleEnv
from rllab.envs.box2d.double_pendulum_env import DoublePendulumEnv
from rllab.envs.normalized_env import normalize


class RLlabWorld(World):

    supported_worldadapters = ['RllabAdapter']

    def __init__(self, filename, world_type="Island", name="", owner="", engine=None, uid=None, version=1, config={}):
        World.__init__(self, filename, world_type=world_type, name=name, owner=owner, uid=uid, version=version)
        self.env = normalize(CartpoleEnv())

        self.n_dim_state = self.env.observation_space.flat_dim
        self.n_dim_action = self.env.action_dim


class RllabAdapter(ArrayWorldAdapter):

    def __init__(self, world, uid=None, **data):
        super().__init__(world, uid, **data)

        for state_dim in range(self.world.n_dim_state):
            self.add_datasource("s%d" % str(state_dim))

        for action_dim in range(self.world.n_dim_action):
            self.add_datatarget("a%d" % str(action_dim))

    def update_data_sources_and_targets(self):
        action = self.datatarget_values

        observation, reward, terminal = self.world.env.step(action)
        state = np.concatenate([observation, reward, terminal])

        self.datasource_values = state
