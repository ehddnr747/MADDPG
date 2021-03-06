import tflearn
import tensorflow as tf
import numpy as np

class Critic(object):
    """
    Input (s,a)
    Output Q(s,a)
    """

    def __init__(self,sess, state_dim, action_dim, learning_rate, tau, gamma, num_actor_vars,critic_reg_weight):
        self.sess= sess
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.learning_rate = learning_rate
        self.tau = tau
        self.gamma = gamma
        self.critic_reg_weight = critic_reg_weight

        self.critic_origin_type = "origin"
        self.inputs, self.action, self.out = self.create_critic_network(network_type=self.critic_origin_type,\
                                                                        l2_weight=self.critic_reg_weight)
        print("Critic origin type :",self.critic_origin_type)

        self.network_params = tf.trainable_variables()[num_actor_vars:]

        self.target_inputs, self.target_action, self.target_out = self.create_critic_network(network_type="target")

        self.target_network_params = tf.trainable_variables()[(len(self.network_params)+num_actor_vars):]


        self.update_target_network_params = \
            [self.target_network_params[i].assign(tf.multiply(self.network_params[i],self.tau)\
                                                  + tf.multiply(self.target_network_params[i],1. - self.tau))
                for i in range(len(self.target_network_params))]

        self.initialize_target_network_params = \
            [self.target_network_params[i].assign(self.network_params[i])
             for i in range(len(self.target_network_params))]

        self.predicted_q_value = tf.placeholder(tf.float32, [None, 1])

        self.loss = tflearn.mean_square(self.out, self.predicted_q_value)

        self.optimize = tf.train.AdamOptimizer(
            self.learning_rate).minimize(self.loss+tf.reduce_sum(tf.losses.get_regularization_losses()))

        self.action_grads = tf.gradients(self.out, self.action)


    def create_critic_network(self,network_type="origin", l2_weight = 0.0):
        assert network_type in ["origin","target"]

        # if len(self.state_dim) == 3:
        #     inputs = tflearn.input_data(shape=[None, *self.state_dim])
        #     action = tflearn.input_data(shape=[None, self.action_dim])
        #
        #     net = tflearn.conv_2d(incoming=inputs, nb_filter=16, filter_size=7, activation='ReLU')
        #     net = tflearn.conv_2d(incoming=net, nb_filter=16, filter_size=7, activation='ReLU')
        #     net = tflearn.conv_2d(incoming=net, nb_filter=16, filter_size=7, activation='ReLU')
        #
        #     t1 = tflearn.fully_connected(net, 100, activation='ReLU')
        #     t2 = tflearn.fully_connected(action, 100, activation='ReLU')
        #
        #     net = tflearn.layers.merge_ops.merge([t1,t2],mode="concat",axis=1)
        #
        #     w_init = tflearn.initializations.uniform(minval=-0.003,maxval=0.003)
        #
        #     out = tflearn.fully_connected(net, 1, weights_init=w_init)
        #
        #     return inputs, action, out

        if len(self.state_dim) == 1:
            inputs = tflearn.input_data(shape=[None, *self.state_dim])
            action = tflearn.input_data(shape=[None, self.action_dim])

            input = tflearn.merge([inputs,action],mode="concat",axis=1)

            if(network_type == "origin"):
                net = tflearn.fully_connected(input, 400, regularizer="L2", weight_decay= l2_weight)
            else:
                net = tflearn.fully_connected(input, 400, weight_decay=0.0)

            net = tflearn.activations.relu(net)

            if (network_type == "origin"):
                net = tflearn.fully_connected(input, 300, regularizer="L2", weight_decay= l2_weight)
            else:
                net = tflearn.fully_connected(input, 300, weight_decay=0.0)
            net = tflearn.activations.relu(net)

            # linear layer connected to 1 output representing Q(s,a)
            # Weights are init to Uniform[-3e-3, 3e-3]
            w_init = tflearn.initializations.uniform(minval=-0.003, maxval=0.003)

            if (network_type == "origin"):
                out = tflearn.fully_connected(net, 1, regularizer="L2", weight_decay= l2_weight, weights_init=w_init)
            else:
                out = tflearn.fully_connected(net, 1, weight_decay=0.0, weights_init=w_init)

            return inputs, action, out

            # """
            # inputs = tflearn.input_data(shape=[None, *self.state_dim])
            # action = tflearn.input_data(shape=[None, self.action_dim])
            #
            # net = tflearn.fully_connected(inputs,400)
            # #net = tflearn.layers.normalization.batch_normalization(net)
            # net = tflearn.activations.relu(net)
            #
            # t1 = tflearn.fully_connected(net,300,activation='ReLU')
            # t2 = tflearn.fully_connected(action, 30, activation='sigmoid')
            # t2 = tflearn.fully_connected(t2, 30, activation='ReLu')
            # t2 = tflearn.fully_connected(t2, 30, activation='sigmoid')
            #
            # net = tflearn.layers.merge_ops.merge([t1,t2],mode="concat",axis=1)
            #
            # w_init = tflearn.initializations.uniform(minval=-0.003, maxval=0.003)
            #
            # out = tflearn.fully_connected(net, 1, weights_init= w_init)
            #
            # return inputs, action, out
            # """

        else:
            assert 0 == 1, "error in create_critic_network, state_dim not matches"

    def train(self, inputs, action, predicted_q_value):

        return self.sess.run([self.out, self.optimize], feed_dict={
            self.inputs : inputs,
            self.action : action,
            self.predicted_q_value : predicted_q_value
        })


    def predict(self, inputs, action):
        return self.sess.run(self.out, feed_dict={
            self.inputs: inputs,
            self.action: action
        })

    def predict_target(self,inputs,action):
        return self.sess.run(self.target_out, feed_dict={
            self.target_inputs: inputs,
            self.target_action: action
        })

    def action_gradients(self, inputs, actions):
        return self.sess.run(self.action_grads, feed_dict={
            self.inputs: inputs,
            self.action: actions
        })

    def update_target_network(self):
        self.sess.run(self.update_target_network_params)

    def initialize_target(self):
        self.sess.run(self.initialize_target_network_params)
