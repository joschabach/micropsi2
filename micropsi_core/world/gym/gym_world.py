
import numpy as np


from micropsi_core.world.world import World
from micropsi_core.world.worldadapter import ArrayWorldAdapter

import gym

"OpenAI Gym interface"

class OAIGym(World):

    supported_worldadapters = ['OAIGymAdapter']

    def __init__(self, filename, world_type="OAIGym", name="", owner="", engine=None, uid=None, version=1, config={}):
        World.__init__(self, filename, world_type=world_type, name=name, owner=owner, uid=uid, version=version)

        self.env = gym.make('CartPole-v0')

        self.n_dim_state = self.env.observation_space.shape[0]
        if isinstance(self.env.action_space, gym.spaces.Discrete):
            # the gym cartpole env happens to have a discrete action space
            self.n_dim_action = 1
            self.n_action_options = self.env.action_space.n # this 2 in the cartpole env, meaning integers {0,1} are allowed
        else:
            raise NotImplementedError()

class OAIGymAdapter(ArrayWorldAdapter):

    def __init__(self, world, uid=None, **data):
        super().__init__(world, uid, **data)

        for state_dim in range(self.world.n_dim_state):
            self.add_datasource("s%d" % state_dim)

        for action_dim in range(self.world.n_dim_action):
            self.add_datatarget("a%d" % action_dim)

        self.add_datatarget("restart")

        self.add_datasource("reward")
        self.add_datasource("is_terminal")



    def update_data_sources_and_targets(self):
        # print('\nworldadapter.update, datatarget values:\n', self.datatarget_values)

        action = self.datatarget_values[0:self.world.n_dim_action]
        restart = self.datatarget_values[self.world.n_dim_action]

        if restart > 0:
            self.reset_simulation_state()
            return

        if self.world.n_action_options == 2:
            action = int(action > 0.5) # converts float actions to 0 or 1
        else:
            raise NotImplementedError()

        obs, r, terminal, info = self.world.env.step(action)
        self.world.env.render()

        state = np.concatenate([obs, [r], [int(terminal)]])
        # if terminal:
        #     print('terminal')
        self.datasource_values =  state

        # print('\nworldadapter.update, datasource values:\n', self.datasource_values)

    def reset_simulation_state(self):
        obs = self.world.env.reset()
        self.world.env.render()
        self.datasource_values = np.concatenate([obs, [0], [0]])
        # print('\nworldadapter did reset, new datasource values:\n', self.datasource_values)

    def reset_datatargets(self):
        """ resets (zeros) the datatargets """
        self.datatarget_values[:] = 0.0