#!/usr/bin/env python

from __future__ import print_function
from __future__ import absolute_import

import cPickle
import numpy
import glob
import sys, os, gc
import h5py

from .generate_cloudlets import generate_cloudlets
from .cluster_cloudlets import cluster_cloudlets
from .make_graph import make_graph
from .output_cloud_data import output_cloud_data

try:
    from netCDF4 import Dataset
except:
    try:
        from netCDF3 import Dataset
    except:
        from pupynere import netcdf_file as Dataset

#-------------------

def load_data(filename):
    input_file = Dataset(filename)
        
    core = input_file.variables['core'][:].astype(bool)
    condensed = input_file.variables['condensed'][:].astype(bool)
    plume = input_file.variables['plume'][:].astype(bool)
    u = input_file.variables['u'][:].astype(numpy.double)
    v = input_file.variables['v'][:].astype(numpy.double)
    w = input_file.variables['w'][:].astype(numpy.double)
        
    input_file.close()

    return core, condensed, plume, u, v, w

#---------------

def main(MC, save_all=True):
    sys.setrecursionlimit(10000)
    input_dir = MC['input_directory']
    nx = MC['nx']
    ny = MC['ny']
    nz = MC['nz']
    nt = MC['nt']
    
    cloudlet_items = ['core', 'condensed', 'plume', 'u_condensed', 'v_condensed', \
        'w_condensed', 'u_plume', 'v_plume', 'w_plume']

    filelist = glob.glob('%s/*' % input_dir)
    filelist.sort()

    #if (len(filelist) != nt):
    #    raise Exception("Only %d files found, nt=%d files expected" % (len(filelist), nt))

    if not os.path.exists('output'):
        os.mkdir('output')
    if not os.path.exists('hdf5'):
        os.mkdir('hdf5')

    # # TODO: Parallelize file access (multiprocessing) 
    # for n, filename in enumerate(filelist):
    #     print("generate cloudlets; time step: %d" % n)
    #     core, condensed, plume, u, v, w = load_data(filename)

    #     cloudlets = generate_cloudlets(core, condensed, plume, u, v, w, MC)
        
    #     # TEST: linear calls instead of for lodop to speed this up?
    #     with h5py.File('hdf5/cloudlets_%08g.h5' % n, "w") as f:
    #         for i in range(len(cloudlets)):
    #             grp = f.create_group(str(i))
    #             for var in cloudlet_items:
    #                 if(var in ['core', 'condensed', 'plume']):
    #                     dset = grp.create_dataset(var, data=cloudlets[i][var][...])
    #                 else:
    #                     deset = grp.create_dataset(var, data=cloudlets[i][var])
    
#----cluster----

    print("Making clusters")

    cluster_cloudlets(MC)

#----graph----

    print("make graph")

    cloud_graphs, cloud_noise = make_graph(MC)
    #(cloud_graphs, cloud_noise) = cPickle.load(open('pkl/graph_data.pkl', 'r'))
    
    print("\tFound %d clouds" % len(cloud_graphs))

    #cPickle.dump((cloud_graphs, cloud_noise), open('pkl/graph_data.pkl', 'wb'))
            
#----output----

    # TODO: Parallelize file output (multiprocessing)
    for n in range(nt):
        print("output cloud data, time step: %d" % n)
        output_cloud_data(cloud_graphs, cloud_noise, n, MC)
            
