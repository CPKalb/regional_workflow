#!/glade/work/wmayfield/conda-envs/hiwt/bin/python

import matplotlib
matplotlib.use('Agg')
from mpl_toolkits.basemap import Basemap
import scipy
from scipy import signal
from scipy import *
from scipy import ndimage
import skimage
from skimage.morphology import label
from skimage.measure import regionprops
import math
from math import radians, tan, sin, cos, pi, atan, sqrt, pow, asin, acos
import pylab as P
import numpy as np
from numpy import NAN
import sys
import netCDF4 as nc
from optparse import OptionParser
from netcdftime import utime
import os
import time as timeit
from optparse import OptionParser
import pygrib
import radar_info
from radar_info import *
import imageio
import news_e_post_cbook
from news_e_post_cbook import *
import news_e_plotting_cbook_v2_NEP_may27
from news_e_plotting_cbook_v2_NEP_may27 import *
import datetime as dt
import importlib

parser = OptionParser()
parser.add_option("-t", dest="hr", type="int", help = "forecast hour to process")
parser.add_option("-m", dest="method", type="str", help = "neighborhood method")
parser.add_option("-r", dest="th", type="str", help = "threshold")
parser.add_option("-w", dest="wid", type="str", help = "width")
parser.add_option("-d", dest="date", type="str", help = "Input date to process, YYYYmmddHH")
parser.add_option("-s", dest="model", type="str", help = "Input model to process, must contain either single_init or time_lag and can have threshold tacked on to the end")
(options, args) = parser.parse_args()
hr = options.hr
th = options.th
wid = options.wid
method = options.method
date = options.date
model = options.model

#exp_dir = '/glade/scratch/mahakian/hiwt_data/SPPT_Spring/'
#exp_dir = '/glade/p/ral/jntp/will/ENS_data/rrfs_sfe_2021'
#exp_dir = '/glade/p/ral/jntp/will/ENS_data/rrfs_sfe_2021/time-lagged'
#exp_dir = '/glade/p/ral/jntp/will/ENS_data/single_init_verif/'
#exp_dir = '/glade/work/wmayfield/ensemble/neighborhood/width_thresh_tests/'

exp_dir = '/glade/scratch/kalb/Ensemble_design/gen_ens_prod/'+model

#hr = 9
#date = '2021052700'
#model = 'single-init'
#model = 'time-lagged'
#method='FREQ'

dz_thresh       = 30    #composite reflectivity
mrms_dz_thresh  = 30    #MRMS composite reflectivity
smoothing = 49
out_dir = '/glade/scratch/kalb/Ensemble_design/plots/neighborhood/'+method+'/'+date
out_path = out_dir+'/'+date+'_'+model+'_'+method+str(dz_thresh)+'_width'+str(wid)+'_'


if not os.path.exists(out_dir):
    os.makedirs(out_dir)

#################################### User-Defined Variables:  #####################################################

#### Distance thresholds from nearest 88D if using radmask: 
range_min = 5000.
range_max = 180000.

ne = 1 #number of members (member 00 is the deterministic)

plot_alpha      = 0.4           #transparency value for filled contour plots
neighborhood    = 15            #neighborhood for local probability-matched mean (not used here, but required by plotting subroutine)

#nep_levs = [0.0, .05, .1, .15, .2, .25, .3, .35, .4, .45, .5, .55, .6]

#################################### Threshold Values:  #####################################################

aws_thresh      = 0.005  #azimuthal wind shear (MRMS)
uh_2to5_thresh = 45.     #2-5 km UH


#### Colors for each member in paintball plot (taken from cb_colors object in news_e_plotting_cbook_v2.py) ####

#paintball_colors = [cb_colors.red5, cb_colors.blue5, cb_colors.green5, cb_colors.orange5, cb_colors.purple5, cb_colors.q8, cb_colors.q12, cb_colors.q10, cb_colors.b7]
##this one for time-lagged?
#paintball_colors = [cb_colors.b7, cb_colors.blue5, cb_colors.blue7, cb_colors.purple5, cb_colors.q5, cb_colors.red5, cb_colors.q6, cb_colors.q4, cb_colors.red7]


#################################### Basemap Variables:  #####################################################

plot_resolution      = 'h'
area_thresh_map = 1000.

damage_files = '' #['/Volumes/fast_scr/pythonletkf/vortex_se/2013-11-17/shapefiles/extractDamage_11-17/extractDamagePaths']


####################################### Find CLUE grib2 files to plot: ######################################################

total_clue_files = ne

#clue_files = ['m1_natlevf012.grib2', 'm1_natlevf012.grib2', 'm2_natlevf012.grib2', 'm3_natlevf012.grib2', 'm4_natlevf012.grib2']
clue_files = []

#for members in [1,2,3,4,5,6,7,8,9]:
#print(f'/thresh{th}/gen_ens_prod/gen_ens_prod_FV3_RRFSE_SINGLE_INIT_REFC_20210527_{hr:02d}0000V.nc')
#clue_files.append(f'thresh{th}/gen_ens_prod/gen_ens_prod_FV3_RRFSE_SINGLE_INIT_REFC_20210527_{hr:02d}0000V.nc')
#gen_ens_prod_RRFSE_TIME_LAG_REFC_MRMS_20210527_060000V.nc
#print(f'/thresh{th}/gen_ens_prod/gen_ens_prod_RRFSE_SINGLE_INIT_REFC_MRMS_20210527_{hr:02d}0000V.nc')
#clue_files.append(f'thresh{th}/gen_ens_prod/gen_ens_prod_RRFSE_TIME_LAG_REFC_MRMS_20210527_{hr:02d}0000V.nc')

# Get valid time to grab file
cur_date = dt.datetime.strptime(date,'%Y%m%d%H')
valid_date = (cur_date + dt.timedelta(hours=int(hr))).strftime('%Y%m%d%H')
clue_files.append(date + '/gen_ens_prod_RRFSE_'+model.upper()+'_REFC_MRMS_'+valid_date[0:8]+'_'+valid_date[8:10]+'0000V.nc')

if model[0:11] == 'single_init':
    paintball_colors = [cb_colors.red5, cb_colors.blue5, cb_colors.green5, cb_colors.orange5, cb_colors.purple5, cb_colors.q8, cb_colors.q12, cb_colors.q10, cb_colors.b7]
elif model[0:11] == 'time_lag':
    paintball_colors = [cb_colors.b7, cb_colors.blue5, cb_colors.blue7, cb_colors.purple5, cb_colors.q5, cb_colors.red5, cb_colors.q6, cb_colors.q4, cb_colors.red7]
else:
    print('Model must say either single_init or time_lagged')
    exit()

print (clue_files)
print(exp_dir)

# #### change variable by changing number in dz_record = fin[]
mem = 0
for f, clue_file in enumerate(clue_files):
   exp_file = os.path.join(exp_dir, clue_file)
   print(exp_file)

   try:
#      fin = pygrib.open(exp_file)
      ds = nc.Dataset(exp_file)
      print ("Opening %s \n" % exp_file)
   except:
      print ("%s does not exist! \n" % exp_file)
      sys.exit(1)

####### Read CLUE record to plot: #######

   print(ds)

   wid2 = int(wid)*int(wid)

   if method == 'FREQ':
      refc_nep = ds['REFC_L0_ENS_FREQ_ge'+str(dz_thresh)][:]
   elif method == 'NEP': 
      refc_nep = ds['REFC_L0_ENS_NEP_ge'+str(dz_thresh)+'_NBRHD' + str(wid2)][:]
   elif method == 'NMEP':
      refc_nep = ds['REFC_L0_ENS_NMEP_ge'+str(dz_thresh)+'_NBRHD'+str(wid2)+'_GAUSSIAN1'][:]
   else:
        print("must specify nrighborhood probs method")
#   dz_record = fin[1282] #composite reflectivity  (for SRW APP runs)
#   dz_record = fin[39] #composity reflectivity (RRFS HWT SFE 2021)
#   print (dz_record)

   print(refc_nep.shape)
  # print(refc_nmep_40.shape)

################### If first file - initialize plotting domain: ############################

   if (f == 0):
#### Read record to plot (DZ here) values and grid information: #### 
      #dz = dz_record.values
      #print (dz.shape, np.max(dz), np.min(dz))

      #lats, lons = dz_record.latlons()
      lats = ds['lat'][:]
      lons = ds['lon'][:]
     # dz_qc = np.zeros((ne, dz.shape[0], dz.shape[1])) ### Initialize final plotting field
      dz_qc = np.zeros((ne, refc_nep.shape[0], refc_nep.shape[1])) ### Initialize final plotting field

      if date == '2021052700':
         #May 27 plains case
         plot_ne_lat = 46
         plot_ne_lon = -90
         plot_sw_lat = 33
         plot_sw_lon = -105
      elif date == '2021052600':
         plot_ne_lat = 46
         plot_ne_lon = -95
         plot_sw_lat = 33
         plot_sw_lon = -110
      elif date == '2021052300':
         plot_ne_lat = 49
         plot_ne_lon = -95
         plot_sw_lat = 36
         plot_sw_lon = -110
      elif date == '2021050400':
         plot_ne_lat = 38
         plot_ne_lon = -82
         plot_sw_lat = 25
         plot_sw_lon = -97
      else:
        print('plot bounds not set for this date')

#### Set corners of domain to plot: ####
     # plot_ne_lat = 45.
     # plot_ne_lon = -90.
     # plot_sw_lat = 29.
     # plot_sw_lon = -104.
#SPRING OUT
    #  plot_ne_lat = 40
     # plot_ne_lon = -88
      #plot_sw_lat = 25
      #plot_sw_lon = -108
#SPRING TEXAS
      #plot_ne_lat = 40
      #plot_ne_lon = -90
      #plot_sw_lat = 25
      #plot_sw_lon = -106
#May 27 plains case
      #plot_ne_lat = 46
      #plot_ne_lon = -90
      #plot_sw_lat = 33
      #plot_sw_lon = -105
#WINTER
      #plot_ne_lat = 36.
      #plot_ne_lon = -83.5
      #plot_sw_lat = 30.
      #plot_sw_lon = -92.
        
#### Set information for Lambert Conformal projection ####
      plot_cen_lat = (plot_sw_lat + plot_ne_lat) / 2.
      plot_stand_lon = (plot_sw_lon + plot_ne_lon) / 2.

      sw_lat = lats[0,0]
      sw_lon = lons[0,0] 
      ne_lat = lats[-1,-1]
      ne_lon = lons[-1,-1] 

      cen_lat = (sw_lat + ne_lat) / 2.
      cen_lon = (sw_lon + ne_lon) / 2. 
      stand_lon = cen_lon
      true_lat1 = 30. 
      true_lat2 = 60.

      resolution = 'c'
      area_thresh = 10000. 
      damage_files = []

#### Basemap instance for converting to a Lambert Confromal projection: ####
      map = Basemap(llcrnrlon=sw_lon, llcrnrlat=sw_lat, urcrnrlon=ne_lon, urcrnrlat=ne_lat, projection='lcc', lat_1=true_lat1, lat_2=true_lat2, lat_0=cen_lat, lon_0=cen_lon, resolution = resolution, area_thresh = area_thresh)

#### Convert lat/lon to y/x relative to domain center: ####
      x_offset, y_offset = map(cen_lon, cen_lat)
      x, y = map(lons[:], lats[:])

      x = x - x_offset
      y = y - y_offset

#### Begin code for masking regions near/far from nearest 88D: #### 

      x_ravel = x.ravel()
      y_ravel = y.ravel()

      x_y = np.dstack([y_ravel, x_ravel])[0]
      x_y_tree = scipy.spatial.cKDTree(x_y)

################### Load locations of 88d sites from radar_sites object: ############################

      rad_x, rad_y = map(np.asarray(radar_sites.lon), np.asarray(radar_sites.lat))
      rad_x = rad_x - x_offset
      rad_y = rad_y - y_offset

################### Create KD Tree of radar site x/y locations: ############################

      rad_x_y = np.dstack([rad_y, rad_x])[0]
      rad_tree = scipy.spatial.cKDTree(rad_x_y)

################### Find points in radar blanking region: ############################

      near_rad_points = x_y_tree.query_ball_tree(rad_tree, range_min)
      far_rad_points = x_y_tree.query_ball_tree(rad_tree, range_max)

      rad_mask = x * 0.
      rad_mask = rad_mask.ravel()

################### Set points in radar blanking region to 1 in radmask: ############################

      for i in range(0,len(near_rad_points)):
         if (len(near_rad_points[i]) > 0.):
            rad_mask[i] = 1.

      for i in range(0,len(far_rad_points)):
         if (len(far_rad_points[i]) == 0.):
            rad_mask[i] = 1.

      rad_mask = rad_mask.reshape(x.shape[0],x.shape[1])

#### End Radar masking code (set following line equal to 'dz'): ####

#      dz_qc[mem,:,:] = np.where(rad_mask < 1., refc_nep, 0.)
      dz_qc[mem,:,:] = np.where(rad_mask < 10000., refc_nep, 0.)
      mem = mem + 1
   else: ## if not the first file
      dz = dz_record.values
#      dz_qc[mem,:,:] = np.where(rad_mask < 1., refc_nep, 0.)
      dz_qc[mem,:,:] = np.where(rad_mask < 10000., refc_nep, 0.)
      mem = mem + 1 

   ds.close()
   del ds
   total_clue_files = total_clue_files + len(clue_files)

#################### Observation data#####################
day_dt = dt.datetime(int(date[:4]),int(date[4:6]),int(date[6:8]))
now_dt = day_dt + dt.timedelta(hours=int(hr))

day = now_dt.strftime('%Y%m%d')
hour = now_dt.strftime('%H')

#mrms_path = '/glade/scratch/wmayfield/HIWT_expts/obs_data/mrms/proc/'+day+'/'
#mrms_file = 'MergedReflectivityQCComposite_Lambert_'+day+'-'+hour+'0000.grib2'
#print('Obs file: ' + mrms_path + mrms_file)
#fin_mrms=pygrib.open(mrms_path + mrms_file)
#mrms_record = fin_mrms[1]
#dz_mrms = mrms_record.values
#latsv, lonsv = mrms_record.latlons()

#print(latsv.shape)


#mrms_path = '/glade/p/ral/jntp/will/ENS_data/single_init_verif/'+day+'00/mem1/metprd/grid_stat/'
mrms_path = '/glade/scratch/kalb/Ensemble_design/mrms_grid_stat/mem1/'+date+'/'
#mrms_file = 'grid_stat_FV3_RRFSE_SINGLE_INIT_mem1_REFC_MRMS_'+hour+'0000L_'+day+'_'+hour+'0000V_pairs.nc'
#mrms_file = 'grid_stat_FV3_RRFSE_SINGLE_INIT_mem1_REFC_MRMS_'+hour+'0000L_'+day+'_'+hour+'0000V_pairs.nc'
mrms_file = 'grid_stat_RRFSE_SINGLE_INIT_mem1_REFC_MRMS_'+str(hr).zfill(2)+'0000L_'+valid_date[0:8]+'_'+valid_date[8:10]+'0000V_pairs.nc'
ds_mrms = nc.Dataset(mrms_path+mrms_file)
#dz_mrms = ds_mrms['OBS_MergedReflectivityQCComposite_Z500_FULL_ge'+str(mrms_dz_thresh)+'_NBRHD_'+str(smoothing)][:]
dz_mrms = ds_mrms['OBS_MergedReflectivityQCComposite_Z500_FULL_ge'+str(mrms_dz_thresh)][:]
latsv = ds_mrms['lat'][:]
lonsv = ds_mrms['lon'][:] 

#dz_mrms = np.where(dz_mrms >= mrms_dz_thresh, dz_mrms, 0.)
print (dz_mrms.shape)

################### Create paintball plot for current date/time: ############################

#dz_qc = np.where(dz_qc >= dz_thresh, dz_qc, 0.)
max_dz = np.max(dz_qc)
print('Max value: ' + str(max_dz))

nep_levs = np.arange(0,.95+.1,.1)


dz_count = len(dz_qc[dz_qc >= uh_2to5_thresh]) / ne #Ensemble mean # of gridpoints exceeding threshold 
mrms_count = 0. 


################################### Initialize plot attributes using 'web plot' objects from news_e_plotting_cbook_v2.py:  #####################################################

#uh2to5_paint_plot = v_plot('uh2to5_paint', '', '', cb_colors.blue6, cb_colors.gray6, [0.003, 1000.], [44., 1000.], [cb_colors.gray8], paintball_colors, '', '', 'max', 0.6, neighborhood)
dz_paint_plot = v_plot('dz_paint', '', '', cb_colors.blue6, cb_colors.gray6, [29., 1000.], [39., 1000.], [cb_colors.gray8], paintball_colors, '', '', 'max', 0.6, neighborhood)
#refc_paint_plot = v_plot('refc', '', '', cb_colors.blue6, cb_colors.gray6, [29., 1000.], [39., 1000.], [cb_colors.gray8], paintball_colors, '', '', 'max', 0.6, neighborhood)
refc_paint_plot = v_plot('refc', '', '', cb_colors.blue6, cb_colors.gray6, [29., 1000.], nep_levs, [cb_colors.gray8], paintball_colors, '', '', 'neither', 0.6, neighborhood)


#### Create figure for plotting using news_e_plotting_cbook_v2.py ####

plot_map, fig, ax1, ax2, ax3 = create_fig(plot_sw_lat, plot_sw_lon, plot_ne_lat, plot_ne_lon, true_lat1, true_lat2, cen_lat, cen_lon, damage_files, plot_resolution, area_thresh_map, verif='False')
plot_x, plot_y = plot_map(lons[:], lats[:])
plot_mrms_x, plot_mrms_y = plot_map(lonsv[:], latsv[:])

domain = 'full'
dz_paint_plot.name = date + '_rad_dz_paint'


# Need to grab MRMS grib2 data, cutoff at mrms threshold, and put into mrms_dz... check size to see if it matches!
#### Create paintball plot using news_e_plotting_cbook_v2.py ####
#mrms_dz = dz_qc[0,:,:] * 0. ###dummy variable for plotting (assumes no MRMS data to plot)

print(out_path)

paintqc_plot(plot_map, fig, ax1, ax2, ax3, plot_x, plot_y, plot_mrms_x, plot_mrms_y, refc_paint_plot, dz_mrms, dz_qc, rad_mask, mrms_count, dz_count, hr,f'REFC_'+method+'_'+str(dz_thresh)+f' {model} {date} hour {hr} width{wid} thresh0p{th}','', domain, out_path, 1, 0, method, dz_thresh)
