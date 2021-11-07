import geopandas as gpd
import pandas as pd

def areal(source, target, cols = [None], suffix = ''):
    """
    The areal weighting method interpolates data into target polygons by using the ratio of 
    intersected area to source area. It accepts two DataFrames – a source and target, a list of columns to be interpolated, 
    and an optional suffix for the new name of the interpolated column in the target DataFrame. In the function, 
    the source polygons are reindexed for summing later, and the areas of the source polygons are calculated. 
    The source and target are intersected, and the area of the intersected polygons is calculated. 
    Each intersected area is divided by the source area that encapsulates it for its areal weight. 
    The function then iterates through the selected columns and multiplies each value by the areal weight. 
    The target DataFrame is returned with the interpolated columns.

    :param source: DataFrame with values for interpolation.
    :type source: DataFrame
    :param target: DataFrame with polygons obtaining interpolated values.
    :type target: DataFrame   
    :param cols: Column(s) from source to be interpolated. 
    :type cols: list
    :param suffix: New name for interpolated columns. The default is ''
    :type suffix: str, optional
        

    :returns: Target DataFrame with interpolated columns added
    :rtype: DataFrame
    """

    #reindex for sum of interpolated results to merge later
    target['_index'] = target.index
    
    #calculate source areas
    source['source_area'] = source.geometry.area
    
    #intersect source and target
    joined1 = gpd.overlay(source, target, how = 'intersection')
    
    #calculate intersected areas
    joined1['intersect_area'] = joined1.geometry.area
    
    #calculate areal weight per intersected polygon
    joined1["AREAL_WT"] = joined1['intersect_area'] / joined1['source_area']    
    
    #interpolate designated columns, create list to include in target dataframe
    new_cols = []
    for col in cols:
        new_col = col + suffix
        new_cols.append(new_col)
        joined1[new_col] = joined1["AREAL_WT"] * joined1[col]
    
    #merge interpolated results to target dataframe
    results = joined1.groupby('_index').sum()
    final = pd.merge(target, results[new_cols], on='_index')
    del final['_index']
    return final