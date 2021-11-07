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

def  lim_var(source, ancillary, class_col, class_dict, cols = [None], source_identifier = '', suffix = ''):
    """
    The limiting variable method interpolates data into disaggregated target polygons by setting thresholds to area-class categories. 
    It accepts two DataFrames – a source and ancillary (landuse most common), the area-class column in the ancillary DataFrame, 
    a dictionary for specifying thresholds to each area-class, a list of columns to be interpolated, an optional source identifier, 
    and an optional suffix for the new name of the interpolated column. Source polygons are reindexed and the area of each is calculated, 
    an intersection is performed, and intersected areas are calculated. The values of the dictionary are placed in a new threshold field and their keys 
    are matched with the specified area-class category. After the areal weight is found, a copy of the dictionary is made with values of none 
    or 0 removed (these correspond to the class with no threshold). Starting with the most restrictive, the specified columns are 
    multiplied by their areal weight and clipped at the specified threshold per square unit. 
    The area that has been used is decremented from the source area and areal weight is recalculated. 
    The most restrictive class is then removed from the dictionary, and this process repeats until all the classes have been removed from the dictionary. 
    Finally, the remaining data is interpolated into the class with no restriction. The target DataFrame is returned with interpolated columns.
    
    :param source: DataFrame with values for interpolation
    :type source: DataFrame
    :param ancillary: DataFrame with area-class map categories.
    :type ancillary: DataFrame
    :param class_col: Area-class categories
    :type class_col: str
    :param class_dict: Area-class categories with assigned thresholds per square unit. Classes with no threshold should be assigned None. Classes with no data should not be included in dictionary.
    :type class_dict: dict
    :param cols: Column(s) from source to be interpolated
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
    
    #reindex for summing excess data and used area per source polygon
    source['_index'] = source.index
    
    #intersect source and ancillary
    join1 = gpd.overlay(source, ancillary, how='intersection')
    
    #calculate intersected areas
    join1['intersect_area']=join1.geometry.area
    
    #Assign thresholds to area classes
    for key, value in class_dict.items():
        join1.loc[join1[class_col]== key, 'threshold']=value
    
    #start interpolation for designated columns; create new_cols for target dataframe
    new_cols = []
    for col in cols:
        source_copy = col + 'copy'
        if suffix:
            new_col = col + suffix
        else:
            new_col = '_' + col
        new_cols.append(new_col)
        
        #calculate areal weight
        join1['arealwt']=join1['intersect_area']/join1['source_area']
    
        #copy column for interpolation (lambda in loop doesn't work first time without this)
        join1[source_copy] = join1[col]
        
        #set new_col to 0 (lambda in loop doesn't work first time without this)
        join1[new_col] = 0
        
        #create used area column - move area that will never be used
        join1['used_area'] = join1.apply(lambda x: x['intersect_area'] if x[class_col] not in class_dict.keys() else 0, axis=1)
    
        #create copy of class_dict for multiple columns, drop values of None
        class_dict_copy = {key:val for key, val in class_dict.items() if val != None and val != 0}
        
        while class_dict_copy != {}:
        
            #interpolate
            join1[new_col] = join1.apply(lambda x: x['arealwt']*x[source_copy] if x[class_col] == min(class_dict_copy, key = class_dict_copy.get) else x[new_col], axis=1)
        
            #if new column exceeds threshold, new column gets threshold density
            join1[new_col] = join1[new_col].clip(upper = join1['threshold']*join1['intersect_area'])
               
            #add up successfully interpolated data and decrement
            totals = join1.groupby('_index')[new_col].sum()
            totals.rename('temp_sum', inplace=True)
            join1 = join1.merge(totals, on='_index')
            join1[source_copy] = join1[col] - join1['temp_sum']
            
            #copy used area for decrementing
            join1['used_area'] = join1.apply(lambda x: x['intersect_area'] if x[class_col] == min(class_dict_copy, key = class_dict_copy.get) else x['used_area'], axis=1)
            
            #add up successfully interpolated areas and decrement 
            totals2 = join1.groupby('_index')['used_area'].sum()
            totals2.rename('temp_area_sum', inplace=True)
            join1 = join1.merge(totals2, on ='_index')
            join1['source_area_copy'] = join1['source_area'] - join1['temp_area_sum']
            
            #recalculate areal weight
            join1['arealwt'] = join1['intersect_area']/join1['source_area_copy']
            
            #remove tempsum
            del join1['temp_sum']
            
            #remove temp_area_sum
            del join1['temp_area_sum']
            
            #remove minimum from dictionary
            del class_dict_copy[min(class_dict_copy, key = class_dict_copy.get)]

        #replace null values with 0 for classes with no restriction
        join1.fillna(0, inplace=True)
        
        #interpolate least restrictive
        join1[new_col] = join1.apply(lambda x: x['arealwt']*x[source_copy] if x[class_col] in class_dict and x['threshold'] == 0 else x[new_col], axis=1)

    #filter target dataframe
    if source_identifier:
        target = join1[[source_identifier, class_col, "geometry", *new_cols]]
    else:
        target = join1[[class_col, "geometry", *new_cols]]
        
    return target

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