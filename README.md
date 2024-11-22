Rainbow
=======
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE.md)

Rainbow: Combining Improvements in Deep Reinforcement Learning [[1]](#references).

Results and pretrained models can be found in the [releases](https://github.com/Kaixhin/Rainbow/releases).

- [x] DQN [[2]](#references)
- [x] Double DQN [[3]](#references)
- [x] Prioritised Experience Replay [[4]](#references)
- [x] Dueling Network Architecture [[5]](#references)
- [x] Multi-step Returns [[6]](#references)
- [x] Distributional RL [[7]](#references)
- [x] Noisy Nets [[8]](#references)

Run the original Rainbow with the default arguments:

```
python main.py
```

Data-efficient Rainbow [[9]](#references) can be run using the following options (note that the "unbounded" memory is implemented here in practice by manually setting the memory capacity to be the same as the maximum number of timesteps):

```
python main.py --target-update 2000 \
               --T-max 100000 \
               --learn-start 1600 \
               --memory-capacity 100000 \
               --replay-frequency 1 \
               --multi-step 20 \
               --architecture data-efficient \
               --hidden-size 256 \
               --learning-rate 0.0001 \
               --evaluation-interval 10000
```

Note that pretrained models from the [`1.3`](https://github.com/Kaixhin/Rainbow/releases/tag/1.3) release used a (slightly) incorrect network architecture. To use these, change the padding in the first convolutional layer from 0 to 1 (DeepMind uses "valid" (no) padding).

Requirements
------------

- [Plotly](https://plot.ly/)
- [PyTorch](http://pytorch.org/)

References
----------

[1] [Rainbow: Combining Improvements in Deep Reinforcement Learning](https://arxiv.org/abs/1710.02298)  
[2] [Playing Atari with Deep Reinforcement Learning](http://arxiv.org/abs/1312.5602)  
[3] [Deep Reinforcement Learning with Double Q-learning](http://arxiv.org/abs/1509.06461)  
[4] [Prioritized Experience Replay](http://arxiv.org/abs/1511.05952)  
[5] [Dueling Network Architectures for Deep Reinforcement Learning](http://arxiv.org/abs/1511.06581)  
[6] [Reinforcement Learning: An Introduction](http://www.incompleteideas.net/sutton/book/ebook/the-book.html)  
[7] [A Distributional Perspective on Reinforcement Learning](https://arxiv.org/abs/1707.06887)  
[8] [Noisy Networks for Exploration](https://arxiv.org/abs/1706.10295)  
[9] [When to Use Parametric Models in Reinforcement Learning?](https://arxiv.org/abs/1906.05243)  
