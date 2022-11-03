#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 16 21:37:14 2022

@author: surrealpartisan
"""

import numpy as np

def drugname():
    syl1 = np.random.choice(['Ab', 'Bra', 'Cil', 'Tra', 'Cog', 'I', 'Bri'])
    syl2 = np.random.choice(['la', 'mo', 'de', 'ca', 'fe', 'ma', 'te'])
    syl3 = np.random.choice(['cil', 'xyl', 'max', 'xium', 'dal', 'dium', 'span', 'lix'])
    return syl1+syl2+syl3