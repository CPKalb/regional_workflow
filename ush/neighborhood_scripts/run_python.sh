#!/bin/bash

date_array=(2021050400 2021052300 2021052600 2021052700)
#date_array=(2021050400)

for dte in ${date_array[@]}; do
    #for fhr in {1..2}; do
    for fhr in {1..36}; do
        python NEP_NMEP_plots_widths_thresh.py -t ${fhr} -m NEP -d ${dte} -w 27 -r 30 -s single_init
        python NEP_NMEP_plots_widths_thresh.py -t ${fhr} -m NEP -d ${dte} -w 27 -r 30 -s time_lag
        python NEP_NMEP_plots_widths_thresh.py -t ${fhr} -m NMEP -d ${dte} -w 27 -r 30 -s single_init
        python NEP_NMEP_plots_widths_thresh.py -t ${fhr} -m NMEP -d ${dte} -w 27 -r 30 -s time_lag
        python NEP_NMEP_plots_widths_thresh.py -t ${fhr} -m FREQ -d ${dte} -w 27 -r 30 -s single_init
        python NEP_NMEP_plots_widths_thresh.py -t ${fhr} -m FREQ -d ${dte} -w 27 -r 30 -s time_lag
    done
done
