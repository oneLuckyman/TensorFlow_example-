import gym,os
import numpy as np 
import matplotlib 
from matplotlib import pyplot as plt

matplotlib.rcParams['font.size'] = 18
matplotlib.rcParams['figure.titlesize'] = 18
matplotlib.rcParams['figure.figsize'] = [9, 7]
matplotlib.rcParams['font.family'] = ['KaiTi']
matplotlib.rcParams['axes.unicode_minus'] = False

import tensorflow as tf 
from tensorflow import keras 
from tensorflow.keras import layers,optimizers,losses 
from PIL import Image
env = gym.make('CartPole-v1')
env.seed(100)
tf.random.set_seed(100)
np.random.seed(100)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
assert tf.__version__.startswith('2.')

learning_rate = 0.0002
gama = 0.98

class Policy(keras.Model):
    # 定义策略网络，生成动作的概率分布
    def __init__(self):
        super(Policy,self).__init__()
        self.data = []  # 记录轨迹
        # 输入4个输入层，输出2个输出层，即动作的左右
        self.fc1 = layers.Dense(128, kernel_initializer='he_normal')
        self.fc2 = layers.Dense(2, kernel_initializer='he_normal')
        # 优化器
        self.optimizer = optimizers.Adam(lr=learning_rate)

    def call(self, inputs, training = None):
        # 状态输入s的shape为向量：[4]
        x = tf.nn.relu(self.fc1(inputs))
        x = tf.nn.softmax(self.fc2(x), axis = 1)
        return x

    def put_data(self, item):
        # 记录r, log_P(a|s)
        self.data.append(item)

    def train_net(self, tape):
        # 计算梯度并更新策略网络参数。tape为梯度记录器
        R = 0   # 终结状态的初始回报为0
        global gamma
        for r, log_prob in self.data[::-1]: #逆序取
            R = r + gamma * R       # 计算每个时间戳的回报
            # 每个时间戳的都会计算梯度
            # grad_R = -log_prob * R
            loss = -log_prob * R
            with tape.stop_recording():
                # 优化策略网络
                grads = tape.gradient(loss, self.trainable_variables)
                # print(grads)
                self.optimizer.apply_gradients(zip(grads, self.trainable_variables))
        self.data = []  # 清空轨迹
    
def main():
    pi = Policy()   # 创建策略网络
    pi(tf.random.normal((4,4)))
    pi.summary()
    score = 0.0     # 初始分数
    print_interval = 20 # 打印间隔
    returns = []

    for n_epi in range(400):
        s = env.reset() # 回到游戏初始状态，返回s0
        with tf.GradientTape(persistent=True) as tape:
            for t in range(501):    # CartPole-v1 forced to terminates at 500 step.
                # 送入状态向量，获取策略
                s = tf.constant(s, dtype = tf.float32)
                # s: [4] => [1,4]
                s = tf.expand_dims(s, axis = 0)
                prob = pi(s)    # 动作分布：[1,2]
                # 从类别分布中选择动作，shape为[1]
                a = tf.random.categorical(tf.math.log(prob), 1)[0]
                int(a.numpy())  # Tensor转int
                s_prime, r, done, info = env.step(a)
                # 记录动作a和动作产生的奖励r
                # prob shape为[1,2]
                pi.put_data((r, tf.math.log(prob[0][a])))
                s = s_prime     # 刷新状态
                score += r      # 奖励累加

                env.render()

                if done:    # 当前episode终止
                    break
            # episode 终止后，训练一次网络
            pi.train_net(tape)
        del tape 

        if n_epi%print_interval == 0 and n_epi != 0:
            returns.append(score/print_interval)
            print(f"# of episode :{n_epi}, avg score : {score/print_interval}")
            score = 0.0
    env.close() # 关闭环境

    plt.plot(np.arange(len(returns)) * print_interval, returns)
    plt.plot(np.arange(len(returns)) * print_interval, returns, 's')
    plt.xlabel('回合数')
    plt.ylabel('总回报')
    plt.savefig('reinforce-tf-cartpole.png')

if __name__ == '__main__':
    main()
            