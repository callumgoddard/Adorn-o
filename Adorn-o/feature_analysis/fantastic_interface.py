'''
Python interface for FANTASTIC:
http://www.doc.gold.ac.uk/isms/m4s/FANTASTIC_docs.pdf
'''

# Standard library imports
import os
import pkg_resources

# 3rd party imports
import rpy2.robjects as robjects

# Set the default folder with the FANTASTIC R scripts
FANTASTIC_folder = pkg_resources.resource_filename(__name__, 'FANTASTIC')


def load(fantastic_dir=FANTASTIC_folder):
    '''
    Load FANTASTIC into rp2 instance
    '''

    # stores the working directory
    working_directory = os.getcwd()

    # Changes the directory to where FANTASTIC is located
    # loads in the Fantastic.R file.
    robjects.r['setwd'](fantastic_dir)
    robjects.r('''
         source('Fantastic.R')
         ''')
    # return to the original working directory.
    robjects.r['setwd'](working_directory)

    return


def compute_features(mcsv_file_list, write_out=True):
    '''
    Compute the fantastic features for the mcsv files in mcsv_file_list
    '''
    assert isinstance(mcsv_file_list, list), "Must be a list of mcsv files"

    # call the compute features and return the dataframe
    return robjects.r['compute.features'](mcsv_file_list, write_out=write_out)


def feature_similarity(
        mcsv_file_list,
        features=robjects.StrVector([
            "p.range", "p.std", "p.entropy", "i.abs.range", "i.abs.mean",
            "i.abs.std", "i.mode", "i.entropy", "d.range", "d.median",
            "d.mode", "d.entropy", "d.eq.trans", "d.half.trans",
            "d.dotted.trans", "len", "glob.duration", "note.dens", "h.contour",
            "step.cont.glob.var", "step.cont.loc.var", "int.cont.glob.dir",
            "int.cont.grad.mean", "int.cont.grad.std", "tonalness",
            "tonal.clarity", "tonal.spike", "mode"
            ]),
        eucl_stand=True):
    '''
    Calculate the similarity between the mcsv files in mcsv_file_list
    '''
    assert isinstance(mcsv_file_list, list), "Must be a list of mcsv files"

    return robjects.r['feature.similarity'](
        mcsv_file_list, features=features, eucl_stand=eucl_stand)
