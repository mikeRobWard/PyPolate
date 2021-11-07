import geopandas as gpd
import pandas as pd

def parcel(zone, parcel, tu_col, ru_col, ba_col, ra_col, cols = [None]):     
   
    """The parcel based method disaggregates population from a large geography to the tax lot level by using residential 
    area and number of residential units as proxies for population distribution. It accepts two DataFrames, a zone DataFrame 
    with geography and population, and a parcel DataFrame which contain geography, total units per parcel, residential units per parcel, 
    building area per parcel, and residential area per parcel. This method returns a DataFrame at the tax lot level that has two calculated columns of 
    disaggregated population, one based on residential area and one based on residential units.
    
    :param zone: DataFrame to be interpolated
    :type zone: DataFrame
    :param parcel: Parcel DataFrame
    :type parcel: DataFrame
    :param tu_col: Column name from parcel DataFrame containing total number of units
    :type tu_col: str
    :param ru_col: Column name from parcel DataFrame containing number of residential units
    :type ru_col: str
    :param ba_col: Column name from parcel DataFrame containing building area
    :type ba_col: str
    :param ra_col: Column name from parcel DataFrame containing residential area
    :type ra_col: str
    :param cols: Column names from Zone DataFrame containing values to interpolate. Can accept one or more columns
    :type cols: list
    
    :return: The parcel level DataFrame with two interpolated fields added for each column of input: One derived from residential units, and another derived from adjusted residential area
    :rtype: DataFrame
    """    
    
    # make copies of zone and parcel dataframes
    ara_parcel = parcel.copy()
    zonecopy = zone.copy()
    
    # calculate ara for parcels
    ara_parcel['M'] = ara_parcel.apply(lambda x: 1 if x[ra_col]==0 and x[ru_col] !=0 else 0, axis=1)
    ara_parcel['ara'] = (ara_parcel['M'] *((ara_parcel[ba_col] * ara_parcel[ru_col]) / ara_parcel[tu_col])) + ara_parcel[ra_col]
    
    # sum ara for zone
    zonecopy['_bindex'] = zonecopy.index
    ara_zone = gpd.overlay(zonecopy, ara_parcel, how='intersection')
    ara_zone = ara_zone.groupby('_bindex')['ara'].sum().reset_index(name='ara_zone')         
            
    # calculate RU for zone
    ru_zone = gpd.overlay(zonecopy, parcel, how='intersection')
    ru_zone = ru_zone.groupby('_bindex')[ru_col].sum().reset_index(name='ru_zone')  
    
    # Calculate dasymetrically derived populations based on RU and ara
    intp_zone = gpd.overlay(zonecopy, ara_parcel, how='intersection')
    intp_zone = intp_zone.merge(ru_zone, on='_bindex')
    intp_zone = intp_zone.merge(ara_zone, on='_bindex')
    new_cols = []
    for col in cols:
        new_col = 'ru_derived_' + col 
        new_cols.append(new_col)
        intp_zone[new_col] = intp_zone[col] * intp_zone[ru_col] / intp_zone['ru_zone']
    new_cols = []    
    for col in cols:
        new_col = 'ara_derived_' + col 
        new_cols.append(new_col)
        intp_zone[new_col] = intp_zone[col] * intp_zone['ara'] / intp_zone['ara_zone']
    
    # drop generated columns that were just for calculations and indexing
    intp_zone.drop(['M', '_bindex', 'ara', 'ru_zone', 'ara_zone'], axis=1, inplace = True)
    return intp_zone