import rpy2.robjects as robjects
import csv
import numpy
from rpy2.robjects import r, pandas2ri
from rpy2.robjects.packages import importr
import os.path
import pandas as pd
import pandas.rpy.common as com

pandas2ri.activate()

MASS = importr('MASS')
zipfR = importr('zipfR')

synpy_features = [
    'source', 'model_name', 'syncopation_by_bar', 'number_of_bars',
    'summed_syncopation', 'mean_syncopation_per_bar', 'bars_with_valid_output',
    'bars_without_valid_output', 'number_of_bars_not_measured'
]


class FANTASTIC(object):
    def __init__(self):

        # self.working_directory = robjects.r('getwd()')
        self.working_directory = os.getcwd()
        # print robjects.r('getwd()')
        robjects.r['setwd']('similarity/FANTASTIC/')
        # print robjects.r('getwd()')
        robjects.r('''
     source('Fantastic.R')
     ''')
        robjects.r['setwd'](self.working_directory)
        # print robjects.r('getwd()')

        # R object wrapper for FANTASTIC Function compute.features.from.mcsv.files
        # NOTE: use.segmentation = FALSE - this is to avoid using the poly.contour features which appear to cause
        # some issues with AIC from the MASS R Package.
        robjects.r('''
        compute.features.from.mcsv.files <- function(folder = 'mcsv_files', return.folder = '../'){
            setwd(folder)
            out <- compute.features(melody.filenames = list.files(pattern = ".csv"), dir = '.', output = "melody.wise", use.segmentation = FALSE, write.out = FALSE)
            setwd(return.folder)
            return(out)
            }
        ''')

        # R object wrapper for FANTASTIC Function feature.similarity.from.folder
        robjects.r('''
        feature.similarity.from.folder <- function(folder = 'mcsv_files', return.folder = '../' ){
            setwd(folder)
            out <- feature.similarity(
                            mel.fns=list.files(pattern=".csv"),
                            dir=".",
                            features=c("p.range",
                                    "p.std",
                                    "p.entropy",
                                    "i.abs.range",
                                    "i.abs.mean",
                                    "i.abs.std",
                                    "i.mode",
                                    "i.entropy",
                                    "d.range",
                                    "d.median",
                                    "d.mode",
                                    "d.entropy",
                                    "d.eq.trans",
                                    "d.half.trans",
                                    "d.dotted.trans",
                                    "len",
                                    "glob.duration",
                                    "note.dens",
                                    "h.contour",
                                    "step.cont.glob.var",
                                    "step.cont.loc.var",
                                    "int.cont.glob.dir",
                                    "int.cont.grad.mean",
                                    "int.cont.grad.std",
                                    "int.cont.dir.changes",
                                    "int.cont.class",
                                    "poly.coeff1",
                                    "poly.coeff2",
                                    "poly.coeff3",
                                    "tonalness",
                                    "tonal.clarity",
                                    "tonal.spike",
                                    "mode"
                                    ),
                            use.segmentation=FALSE,
                            method="euclidean",
                            eucl.stand=TRUE,
                            corpus.dens.list.fn=NULL,
                            average=TRUE)
            setwd(return.folder)
            return(out)
            }
        ''')
        # R object wrapper for FANTASTIC Function feature.similarity.from.folder
        robjects.r('''
    feature.similarity.from.file <- function(file = 'mcsv_files', return.folder = '../' ){
        out <- compute.features(melody.filenames=file,dir=".",output="melody.wise", use.segmentation=FALSE, write.out=FALSE)
        return(out)
        }
    ''')

        # R function that gets the synpy features from a csv file.
        robjects.r('''
            synpy.data <- function(file = 'synpy_features.csv' ){
            data.frame(read.csv(file))
            }
        ''')
        self.compute_features = robjects.globalenv[
            'compute.features.from.mcsv.files']
        self.get_synpy_data = robjects.globalenv['synpy.data']
        self.compute_features_from_file = robjects.globalenv[
            'feature.similarity.from.file']

    def merge_synpy_and_fantastic_features(
            self, mcsv_folder='mcsv', synpy_features='synpy_features.csv'):
        all_features = robjects.r['merge'](self.compute_features(mcsv_folder),
                                           self.get_synpy_data(synpy_features))
        return all_features


# feature.similarity(mel.fns=list.files(path=dir,pattern=".csv"), dir=".", features=c("p.range","step.cont.glob.var","tonalness","d.eq.trans"), use.segmentation=FALSE, method="euclidean", eucl.stand=TRUE, corpus.dens.list.fn=NULL, average=TRUE)

# Calcuates the feature similarity from a dataframe containing features for tracks
# and works out the similarity between the tracks based on the features
# specified in "features"


def feature_similarity(feature_df, features, return_df=False, eucl_stand=True):
    # feature.similarity(mel.fns=list.files(path=dir,pattern=".csv"), dir=".", features=c("p.range","step.cont.glob.var","tonalness","d.eq.trans"), use.segmentation=FALSE, method="euclidean", eucl.stand=TRUE, corpus.dens.list.fn=NULL, average=TRUE)

    if eucl_stand:
        sim_matrix = robjects.globalenv['callums.feature.similarity'](
            df_in=feature_df, features=features)
    else:
        sim_matrix = robjects.globalenv['callums.feature.similarity'](
            df_in=feature_df, features=features, eucl_stand=False)

    if return_df:
        sim_matrix = com.convert_robj(sim_matrix)
        sim_matrix = sim_matrix['av.sim']
    #sim_matrix = com.convert_robj(sim_matrix[0][0])
    return sim_matrix


# Default feature removed:
# features=robjects.r('''c("p.range",
#                                   "WNBD.summed_syncopation"
#                               )''')
