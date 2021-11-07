import geopandas as gpd
import pandas as pd

def n_class(source, ancillary, class_col, class_dict, cols = [None], source_identifier = '', suffix = ''):
    """
    The n-class method interpolates data into disaggregated target polygons by assigning weights to area-class categories. 
    It accepts two DataFrames – a source and ancillary (landuse most common), the area-class column in the ancillary DataFrame, 
    a dictionary for specifying percentages to each area-class, a list of columns to be interpolated, an optional source identifier, 
    and an optional suffix for the new name of the interpolated column. Like areal weighting, source polygons are reindexed and the area of each is calculated.
    The dictionary values are placed into a new percentage field and their keys are matched with the specified area-class column. 
    After intersecting, the areal weight for each new polygon is calculated and multiplied by its corresponding user-defined percentage. 
    Each of those products is then divided by the sum of all the products per source polygon. That fraction is called class_weight and is 
    multiplied by column values for interpolation. The target DataFrame is returned with interpolated columns.


    :param source: DataFrame with values for interpolation.
    :type source: DataFrame
    :param ancillary: DataFrame with area-class map categories.
    :type ancillary: DataFrame 
    :param class_col: Area-class categories.
    :type class_col: str     
    :param class_dict: Area-class categories with assigned percentages.
    :type class_dict: dict        
    :param cols: Column(s) from source to be interpolated.
    :type cols: list        
    :param source_identifier: Column that identifies source polygons. The default is ''
    :type source_identifier: str, optional
    :param suffix: New name for interpolated columns. The default is ''
    :type suffix: str, optional
        
    :return: Target DataFrame with interpolated columns.
    :rtype: DataFrame
    """

    #calculate source area
    source['source_area'] = source.geometry.area
    
    #reindex source for grouping sums later
    source['_index'] = source.index
    
    #assign percentages to landuse classes
    for key, value in class_dict.items():
        ancillary.loc[ancillary[class_col]== key, '_percent']=value
    
    #intersect source and ancillary data
    join1 = gpd.overlay(source, ancillary, how='intersection')
    
    #calculate intersected areas
    join1['intersect_area']=join1.geometry.area
    
    #calculate areal weight
    join1['arealwt']=join1['intersect_area']/join1['source_area']
    
    #multiply areal weight by user defined percentages
    join1['class_weight']=join1['_percent'] * join1['arealwt']
    
    #sum of areal weight times percentage per source polygon
    totals = join1.groupby('_index')['class_weight'].sum()
    totals.rename('temp_sum', inplace=True)
    join1 = join1.merge(totals, on ='_index')
    
    #fraction for interpolation
    join1['class_frac'] = join1['class_weight']/join1['temp_sum']
    
    #interpolate designated columns, create list to include in final dataframe
    new_cols = []
    for col in cols:
        new_col = col + suffix
        new_cols.append(new_col)
        join1[new_col] = join1['class_frac']*join1[col]
    
    #filter target dataframe
    if source_identifier:
        target = join1[[source_identifier, class_col, "geometry", *new_cols]]
    else:
        target = join1[[class_col, "geometry", *new_cols]]
      
    return target