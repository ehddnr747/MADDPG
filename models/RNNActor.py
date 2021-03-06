import tflearn
import tensorflow as tf
import numpy as np

class Actor(object):


    def __init__(self, sess, state_dim, action_dim,learning_rate, tau, batch_size,action_steps):

        #the length of state dim might be 1 or 3(height,width,channels)

        self.sess = sess
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.learning_rate = learning_rate
        self.tau = tau
        self.batch_size = batch_size
        self.action_steps = action_steps
        self.single_action_dim = int(self.action_dim / self.action_steps)


        self.inputs, self.out, self.initial_state = self.create_actor_network()

        self.network_params = tf.trainable_variables()

        self.target_inputs, self.target_out, self.target_initial_state = self.create_actor_network()

        self.target_network_params = tf.trainable_variables()[len(self.network_params):]

        self.update_target_network_params = \
            [self.target_network_params[i].assign(tf.multiply(self.network_params[i], self.tau)) +\
                                        tf.multiply(self.target_network_params[i],1. - self.tau) \
                for i in range(len(self.target_network_params))]

        self.initialize_target_network_params = \
            [self.target_network_params[i].assign(self.network_params[i])
             for i in range(len(self.target_network_params))]

        self.action_gradient = tf.placeholder(tf.float32, [None, self.action_dim])

        self.actor_gradients = list(
            map(lambda x:tf.div(x,self.batch_size),
                tf.gradients(self.out, self.network_params, -self.action_gradient)
                ))


        self.optimize = tf.train.AdamOptimizer(self.learning_rate).\
            apply_gradients(zip(self.actor_gradients,self.network_params))

        self.num_trainable_vars = len(self.network_params) + len(self.target_network_params)

    def create_actor_network(self):

        # if len(self.state_dim) == 3:
        #     inputs = tflearn.input_data(shape=[None,*(self.state_dim)])
        #     net = tflearn.layers.conv.conv_2d(incoming=inputs, nb_filter = 16, filter_size = 7, activation='ReLU')
        #     net = tflearn.layers.conv.conv_2d(incoming=net, nb_filter = 16, filter_size = 7, activation = 'ReLU')
        #     net = tflearn.layers.conv.conv_2d(incoming=net, nb_filter = 16, filter_size =7, activation = 'ReLU')
        #     net = tflearn.fully_connected(net, 100 ,activation='ReLU')
        #     net = tflearn.fully_connected(net, 100, activation='ReLU')
        #
        #     w_init = tflearn.initializations.uniform(minval=-0.003, maxval=0.003)
        #
        #     out = tflearn.fully_connected(net, self.action_dim, activation = 'tanh', weights_init=w_init)
        #
        #     return inputs, out

        if len(self.state_dim) == 1:
            initial_state = tflearn.input_data(shape=[None,self.single_action_dim])

            inputs = tflearn.input_data(shape=[None, *self.state_dim])
            net = tflearn.fully_connected(inputs, 400,weight_decay=0.0)
            net = tflearn.activations.relu(net)
            net = tflearn.fully_connected(net,300, weight_decay=0.0)
            net = tflearn.activations.relu(net)

            w_init = tflearn.initializations.uniform(minval=-0.003,maxval=0.003)

            out = tflearn.fully_connected(net, self.action_dim, \
                                          weights_init=w_init, weight_decay=0.0)

            cell = tf.nn.rnn_cell.BasicRNNCell(num_units=self.single_action_dim,activation="tanh")

            outs = []

            states = initial_state

            for _ in range(self.action_steps):
                temp_action, states = cell(out, states)
                outs.append(temp_action)

            outs = tflearn.merge(outs,mode="concat",axis=1)

            return inputs, outs, initial_state


        else:
            assert 1 == 0, "wrong state dim input"


    def train(self, inputs, a_gradient):
        self.sess.run(self.optimize, feed_dict ={
            self.inputs: inputs,
            self.action_gradient: a_gradient,
            self.initial_state : np.zeros([inputs.shape[0],self.single_action_dim])
        })

    def predict(self, inputs):
        return self.sess.run(self.out, feed_dict={
            self.inputs: inputs,
            self.initial_state: np.zeros([inputs.shape[0], self.single_action_dim])
        })

    def predict_target(self, inputs):
        return self.sess.run(self.target_out, feed_dict={
            self.target_inputs: inputs,
            self.target_initial_state: np.zeros([inputs.shape[0], self.single_action_dim])
        })

    def update_target_network(self):
        self.sess.run(self.update_target_network_params)

    def get_num_trainable_vars(self):
        return self.num_trainable_vars

    def initialize_target(self):
        self.sess.run(self.initialize_target_network_params)