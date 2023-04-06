#!/bin/bash

#cd /glade/u/home/kalb/Ensemble_T_E
#conda activate paintball
#cd paintball

date_array=(2021052300 2021052600 2021052700)

for dte in ${date_array[@]}; do
    for fhr in {0..36}; do
        python paintball_plots.py -t ${fhr} -d ${dte} -m single_init_30dbz
        python paintball_plots.py -t ${fhr} -d ${dte} -m time_lagged_30dbz
    done
done