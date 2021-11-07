import geopandas as gpd
import pandas as pd


def binary(source, ancillary, exclude_col=(), 
                  exclude_val= [None], suffix= '', cols= [None]):
    """This method accepts two DataFrames - a source DataFrame which should contain the values that will be interpolated - and 
    an ancillary DataFrame containing a column with categorical geographic data such as land use types. The function 
    also takes an input called exclusion field which allows the user to pass in the name of the column that contains the categorical data. 
    Another input, exclusion value(s), allows the user to pass in a list of values that appear within the exclusion field column. 
    The values that are passed to exclusion field will be dropped from the ancillary DataFrame before it is spatially 
    intersected with the source DataFrame so that the geography of the exclusionary values is not included in the intersected DataFrame. 
    This effectively turns the ancillary DataFrame into a mask, which masks out the geography of all values that were passed to exclusion value. 
    Returns a DataFrame that has the masked areas clipped and the interpolation values disaggregated based on areal weight to the non-clipped zones.
    
    :param source: Name of Dataframe that contains values that should be interpolated
    :type source: str
    :param ancillary: Name of dataframe containing ancillary geometry data, used to mask source dataframe
    :type ancillary: str
    :param exclude_col: Column name from ancillary dataframe that contains exclusionary values
    :type exclude_col: str
    :param exclude_val: Values from exclude_col that should be removed during binary mask operation
    :type exclude_val: list
    :param suffix: Suffix that should be added to the column names that are interpolated
    :type suffix: str, optional
    :param cols: Column names that should be interpolated
    :type cols: list
    
    :return: Source dataframe with interpolated columns added
    :rtype: dataframe
    """    
    # index group 
    source['division'] = source.index
           
    #drop excluded rows from ancillary data
    binary_mask = ancillary[exclude_col].isin(exclude_val)
    ancillary = ancillary[~binary_mask]
    
    #drop all columns except geometry before join (don't want data from ancillary in final df)
    ancillary = ancillary[['geometry']]
          
    #intersect source file and ancillary file
    mask = gpd.overlay(source, ancillary, how='intersection')
    
    #calculate and store areas of intersected zone
    mask['intersectarea'] = (mask.area)  

    #calculate sum of polygon areas by tract
    masksum = mask.groupby('division')['intersectarea'].sum()
    
    # merge summmed areas back to main dataframe
    target = mask.merge(masksum, on='division')
    
    # calculate areal weight of areas
    target["AREAL_WT"] = target['intersectarea_x'] / target['intersectarea_y']

    # loop through columns that user wants to interpolate, add suffix
    new_cols = []
    for col in cols:
        new_col = col + suffix
        new_cols.append(new_col)
        target[new_col] = target["AREAL_WT"] * target[col]
    
    # drop generated columns
    output = target
    output = output.drop(['division','intersectarea_x','intersectarea_y', 'AREAL_WT'], axis=1)
    return output