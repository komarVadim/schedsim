#!/bin/sh

sudo apt-get install -y python-numpy
sudo apt-get install -y python-matplotlib
sudo apt-get install -y python-blist

python experiment_weibull.py 0.25 test