import geopandas as gpd
import pandas as pd

def expert(large_zone, small_zone, parcel, tu_col, ru_col, ba_col, ra_col, intp_col):
        
    """The CEDS method works in conjunction with the parcel based method to determine whether adjusted residential area or number of residential 
    units are a more accurate determinant when disaggregating population. The CEDS method accepts three DataFrames, two zone DataFrames that must 
    nest with each other and contain geometry and population, and a parcel DataFrame that contains geometry, total units per parcel, residential units per parcel, 
    building area per parcel, and residential area per parcel. The parcel based method is called twice inside the CEDS method, once using the larger zone DataFrame as an 
    input, and once using the smaller nested zone DataFrame as an input to the parcel method. The populations at the tax lot level that were derived from the large zone 
    are then reaggregated back up to the small zone level. The absolute value of the difference between the large zone based populations and small zone estimated population 
    are then calculated. Finally, for each parcel, if the absolute difference between the large zone based population and the small zone estimated population based 
    on residential units is less than or equal to the absolute difference between the large zone population and small zone estimated population based on adjusted residential area, 
    then the population estimate from the small zone based on residential units is determined to be the more accurate disaggregation. Otherwise, the 
    population estimate from the small zone based on adjusted residential area is determined by the CEDS method to be the more accurate measure of disaggregation. 
    This method returns one DataFrame at the tax lot level with the parcel based method calculations, plus an additional column that contains the selected outcome of the CEDS method.
    
    :param large_zone: DataFrame with larger geography
    :type large_zone: Dataframe
    :param small_zone: DataFrame with smaller geography
    :type small_zone: Dataframe
    :param parcel: Parcel DataFrame
    :type parcel: DataFrame
    :param tu_col: Column name from parcel DataFrame containing total number of units
    :type tu_col: str
    :param ru_col: Column name from parcel DataFrame containing number of residential units
    :type ru_col: str
    :param ba_col: Column name from parcel DataFrame containing building area
    :type ba_col: str
    :param ra_col: Column name from parcel DataFrame containing residential area
    :type ra_col: string
    :param intp_col: Column name from Zone DataFrame containing values to interpolate. Only accepts one column
    :type intp_col: str
    
    :return: Dataframe at parcel level containing interpolated values based on expert system implementation
    :rtype: DataFrame
    """    
    
    # index small_zone
    small_zone['index_s'] = small_zone.index
    
    # call parcel method on large interpolation zone
    expert_large = parcel_method(large_zone, parcel, tu_col, ru_col, ba_col, ra_col, [intp_col])    
    # call parcel method on small interpolation zone
    expert_small = parcel_method(small_zone, parcel, tu_col, ru_col, ba_col, ra_col, [intp_col])
       
    # overlay the interpolated large zone with small zone, so that it can later by grouped by small zone index
    expert = gpd.overlay(expert_large, small_zone, how='intersection')
    
    # sum ara at small zone level
    expert_ara = expert.groupby('index_s')['ara_derived_' + intp_col].sum().reset_index(name='expert_ara')    
    # sum ru at small zone level
    expert_ru = expert.groupby('index_s')['ru_derived_' + intp_col].sum().reset_index(name='expert_ru')
    
    # merge ru and ara into same dataframe
    expert_parcel = expert_ara.merge(expert_ru, on = 'index_s')
    
    # pop diff calculation
    expert_parcel['ara_diff'] = abs(expert_small[intp_col] - expert_parcel['expert_ara'])
    expert_parcel['ru_diff'] = abs(expert_small[intp_col] - expert_parcel['expert_ru'])
    
    # merge the aggregated data back with the small zone interpolated parcel dataframe
    expert_parcel = expert_small.merge(expert_parcel, on='index_s')
    
    # apply the expert system
    expert_parcel['expert_system_interpolation'] = expert_parcel.apply(lambda x: x['ru_derived_' + intp_col] 
                                                           if x['ru_diff']<=x['ara_diff']
                                                           else x['ara_derived_' + intp_col], axis=1)
    expert_parcel.drop(['index_s', 'expert_ara', 'expert_ru', 'ara_diff', 'ru_diff'], axis=1, inplace = True)
    return expert_parcel
