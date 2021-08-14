'''
Functions to calculate similarity based upon features
analysed from FANTASTIC and SynPy
'''
import glob
import os
import csv

# 3rd party imports
import rpy2.robjects as robjects

# Local application imports
from . import fantastic_interface
from . import synpy_interface
import parser.API.calculate_functions as calculate


def list_all_files_in_folder(folder=".", filetype=''):
    '''
    Return a list of all the files in the folder that
    have file type filetype.

    Parameters
    ---------
    folder: string, optional
            path to the folder
            (default is the relative path to the
            current working directory folder.)

    filetype: {"", "mscv", "csv", "rhy", "gp5", "gp"}
              The file extension for the files to find.

    Returns
    ------
    list
        A list containing the full path locations for all
        files in the folder with the specified file extension.

    '''
    valid_file_tag = {'', 'mcsv', 'csv', 'rhy', 'gp5'}
    if filetype not in valid_file_tag:
        raise ValueError("results: status must be one of %r." % valid_file_tag)

    if filetype is '':
        return glob.glob(folder + '/' + '*.*')
    if filetype is "mcsv":
        return glob.glob(folder + '/' + "*_mscv.csv")
    if filetype is "'csv'":
        return glob.glob(folder + '/' + "*.csv")
    if filetype is "rhy":
        return glob.glob(folder + '/' + "*.rhy")
    if filetype is "gp5":
        return glob.glob(folder + '/' + "*.gp5")
    if filetype is "gp":
        return glob.glob(folder + '/' + "*.gp[3-5]")


def merge_synpy_and_fantastic_features(
        mcsv_file_list,
        rhy_file_list,
        rhy_table_output='rhy_features.csv',
        save_location="all_features.csv",
        save_table=True,
):
    '''
    Compute the FANTASTIC features for the files in the mcsv_file_list
    and the SynPy features for the files in the rhy_file_list.
    Combine both into a single table/dataframe.

    Note: Make sure that fantastic_interface.load(fantastic_folder)
    has been called before using this function.
    '''

    # Make a csv file with the synpy features calculated
    synpy_interface.make_feature_table(rhy_file_list, output=rhy_table_output)

    # Make a quick function to read the synpy features
    # into r as a dataframe so it can 'merge' with the
    # fantastic features
    get_synpy_data = robjects.r('''
            synpy.data <- function(file = 'synpy_features.csv' ){
            data.frame(read.csv(file))
            }
        ''')

    fantastic_features = None
    for mcsv_file in mcsv_file_list:
        try:
            f = fantastic_interface.compute_features(
                [mcsv_file], write_out=False)
            if fantastic_features is None:
                fantastic_features = f
            else:
                fantastic_features = robjects.r['rbind'](fantastic_features, f)

        except:
            print("Error when analysing %s" % mcsv_file)

    try:
        all_features = robjects.r['merge'](fantastic_features,
                                           get_synpy_data(rhy_table_output))

        # Save the big table:
        if save_table:
            robjects.r['write.table'](
                x=all_features, file=save_location, sep=",", row_names=False)

        return all_features
    except:
        print("could not merge feature table")
        return False


def add_to_feature_table(mcsv_file_list, rhy_file_list, feature_table):
    '''
    Add compute the FANTASTIC features for the mcsv files in mcvs_file_list
    and the SynPy features for the rhy files in rhy_file_list
    and then add them to an existing feature_table
    '''

    df = merge_synpy_and_fantastic_features(
        mcsv_file_list,
        rhy_file_list,
        rhy_table_output="update_features.csv",
        save_table=False)

    feature_dataframe = read_in_feature_dataframe(feature_table)

    updated_feature_dataframe = robjects.r['rbind'](feature_dataframe, df)

    return updated_feature_dataframe


def combine_feature_tables(feature_table1, feature_table2):
    '''
    combine feature_table1 and feature_table2 into a single dataframe
    '''
    feature_table1 = read_in_feature_dataframe(feature_table1)
    feature_table2 = read_in_feature_dataframe(feature_table2)
    updated_feature_dataframe = robjects.r['rbind'](feature_table1,
                                                    feature_table2)

    return updated_feature_dataframe


def compute_similarity_using_both_sets_of_features(
        feature_dataframe,
        features=robjects.StrVector([
            "p.range", "p.std", "p.entropy", "i.abs.range", "i.abs.mean",
            "i.abs.std", "i.mode", "i.entropy", "d.range", "d.median",
            "d.mode", "d.entropy", "d.eq.trans", "d.half.trans",
            "d.dotted.trans", "len", "glob.duration", "note.dens", "h.contour",
            "step.cont.glob.var", "step.cont.loc.var", "int.cont.glob.dir",
            "int.cont.grad.mean", "int.cont.grad.std", "tonalness",
            "tonal.clarity", "tonal.spike", "mode",
            "PRS.mean_syncopation_per_bar", "KTH.mean_syncopation_per_bar",
            "LHL.mean_syncopation_per_bar", "SG.mean_syncopation_per_bar",
            "TMC.mean_syncopation_per_bar", "TOB.mean_syncopation_per_bar",
            "WNBD.mean_syncopation_per_bar"
        ]),
        eucl_stand=True):
    '''
    Compute the similarity matrix based upon fantastic and synpy features
    for the data in feature_dataframe

    Note: Make sure that fantastic_interface.load(fantastic_folder)
    has been called before using this function.
    '''

    # load r stuff just incase:
    fantastic_interface.load()

    feature_dataframe = read_in_feature_dataframe(feature_dataframe)

    # Make a similarity function that takes a dataframs
    robjects.r('''
        data.frame.feature.similarity <- function(df.in = data.frame(),mel.fns=list.files(path=dir,pattern=".csv"),dir=".",features=c("p.range","step.cont.glob.var","tonalness","d.eq.trans"),use.segmentation=FALSE,method="euclidean",eucl.stand=TRUE,corpus.dens.list.fn=NULL,average=TRUE){


        #source("Feature_Similarity.R")
        require(cluster)

        # This is the melody features that similarity is calculated on...
        # can have a dataframe input here...
        if(length(df.in) == 0){
        mel.feat <- compute.features(melody.filenames=mel.fns,dir=dir,output="melody.wise",use.segmentation=use.segmentation)
        }else{
        mel.feat <-df.in
        }

        mel.feat.new <- as.data.frame(mel.feat[,features])


        row.names(mel.feat.new) <- mel.feat[,"file.id"]
        colnames(mel.feat.new) <- features
        sim <- NULL
        if(average==FALSE){

        for(i in seq(along=features)){
          sim[[paste(method,features[i],sep=".")]] <- compute.sim(mel.feat.new[,features[i]],features[i],row.names(mel.feat.new),method,eucl.stand,corpus.dens.list.fn)}
        }
        else{sim[["av.sim"]] <- compute.sim(mel.feat.new,features,row.names(mel.feat.new),method,eucl.stand,corpus.dens.list.fn) }

        sim
        }
    ''')

    if eucl_stand:
        sim_matrix = robjects.globalenv['data.frame.feature.similarity'](
            df_in=feature_dataframe, features=features)
    else:
        sim_matrix = robjects.globalenv['data.frame.feature.similarity'](
            df_in=feature_dataframe, features=features, eucl_stand=False)

    return sim_matrix


def read_in_feature_dataframe(feature_dataframe):
    '''
    read in the feature dataframe, if feature_dataframe return it
    if feature_dataframe is a file location for a csv file
    read it in as a dataframe then return it.
    '''
    if isinstance(feature_dataframe, robjects.vectors.DataFrame):
        print("is already a dataframe input")

    if isinstance(feature_dataframe, str):

        print("Reading feature dataframe from csv...")
        read_feature_csv = robjects.r('''
                    read.feature.csv <- function(file = 'all_features.csv' ){
                    data.frame(read.csv(file))
                    }
                ''')
        feature_dataframe = read_feature_csv(feature_dataframe)

    return feature_dataframe


def combine_synpy_and_fantastic_features_for_two_notes(measure,
                                                       two_notes,
                                                       rhy_file,
                                                       r_data_frame=False,
                                                       save_table=False):
    """Compute the FANTASTIC features for the 2 notes in the measure,
    then combine these with the SynPy Features.

    """

    FANTASTIC_features = calculate.calculate_FANTASTIC_features_for_note_pair(
        two_notes[0], two_notes[1], measure)

    SynPy_features = synpy_interface.compute_features(rhy_file)

    # combine: chunk_FANTASTIC_features + chunk_SynPy_features
    # then return the list:
    combined_features = [
        SynPy_features[0], FANTASTIC_features["p.range"],
        FANTASTIC_features["p.entropy"], FANTASTIC_features["p.std"],
         FANTASTIC_features["i.abs.mean"],
        FANTASTIC_features["i.abs.std"], FANTASTIC_features["i.mode"],
        FANTASTIC_features["i.entropy"], FANTASTIC_features["d.range"],
        FANTASTIC_features["d.median"], FANTASTIC_features["d.mode"],
        FANTASTIC_features["d.entropy"], FANTASTIC_features["len"],
        FANTASTIC_features["glob.duration"], FANTASTIC_features["note.dens"]
    ] + SynPy_features[1:]

    if r_data_frame:
        feature_header = [
            'file.id', "p.range", "p.entropy", "p.std",
            "i.abs.mean", "i.abs.std", "i.mode", "i.entropy", "d.range",
            "d.median", "d.mode", "d.entropy", "len", "glob.duration",
            "note.dens", "PRS.mean_syncopation_per_bar",
            "KTH.mean_syncopation_per_bar", "LHL.mean_syncopation_per_bar",
            "SG.mean_syncopation_per_bar", "TMC.mean_syncopation_per_bar",
            "TOB.mean_syncopation_per_bar", "WNBD.mean_syncopation_per_bar"
        ]

        # write out the csv file that combines that features.
        with open('2_note_features.csv', mode='w') as csv_file:
            feature_writer = csv.writer(csv_file)
            feature_writer.writerow(feature_header)
            feature_writer.writerow(combined_features)
        # read in the csvfile as a dataframe and find most similar.
        feature_df = read_in_feature_dataframe("2_note_features.csv")

        if os.path.isfile("2_note_features.csv") and not save_table:
            os.remove("2_note_features.csv")

        return feature_df

    else:
        return combined_features
