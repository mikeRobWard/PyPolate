<h1 align= "center">
PyPolate
<p>
    <img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/mikeRobWard/spatial-interpolation-toolbox?style=social">
    <a href="https://twitter.com/intent/follow?screen_name=MWard_GIS">
        <img src="https://img.shields.io/twitter/follow/MWard_GIS?style=social&logo=twitter"
            alt="follow on Twitter"></a>
    <a href="https://github.com/login?return_to=https%3A%2F%2Fgithub.com%2FmikeRobWard">
        <img alt="GitHub followers" src="https://img.shields.io/github/followers/mikeRobWard?style=social" alt="follow on GitHub">
        </a>
</p>
</h1>

Python tools for interpoolating spatial data

<h2>Table of Contents</h2>

- [Introduction](#introduction)
- [Examples](#examples)
  - [Interpolating car crash data with areal weighting](#interpolating-car-crash-data-with-areal-weighting)
  - [Masking land-use categories with the binary method](#masking-land-use-categories-with-the-binary-method)
  - [Setting land-use category thresholds with the limiting variable method](#setting-land-use-category-thresholds-with-the-limiting-variable-method)
  - [Assigning weights to land-use categories with the n-class method](#assigning-weights-to-land-use-categories-with-the-n-class-method)
  - [Disaggregating population with the parcel method](#disaggregating-population-with-the-parcel-method)
    - [Description](#description)
  - [Refining parcel method with the Cadastral-Based Expert Dasymetric System](#refining-parcel-method-with-the-cadastral-based-expert-dasymetric-system)

## Introduction 

PyPolate is an open source project to make interpolating geospatial data in python easier. Geometric operations in PyPolate are performed by Geopandas. PyPolate currently works with spatial vector data and implements six different methods of spatial interpolation.

## Examples

### Interpolating car crash data with areal weighting

For this example, we will be using open data from Philadelphia. The first shapefile is [crash data aggregated by Traffic Analysis zone (TAZ)](https://github.com/CityOfPhiladelphia/crash-data). The second shapefile is [Census Block Groups](https://www.opendataphilly.org/dataset/census-block-groups).


![aw_test](https://user-images.githubusercontent.com/67876029/139040847-80f13d49-a526-400a-928c-c0a3f422ac21.png)

In this example, we want to interpolate the number of crashes from TAZ in the source layer, to Census Block group in our target layer. We can see from the crash-data attributes that the field for aggregated crashes is named `Count_` 

    pypolate.areal(carcrash.df, census.df, Count_, '_intp')

If you map the output DataFrame and compare it to the input DataFrame, this is what it should look like:

![aw_output](https://user-images.githubusercontent.com/67876029/139040841-f38711a3-7b1d-4bdf-a709-4037d2f5eb70.png)

### Masking land-use categories with the binary method

In this example, we will use the [Philadelphia crash data](https://github.com/CityOfPhiladelphia/crash-data) again, but this time we will use [land use data](https://www.opendataphilly.org/dataset/land-use) as an ancillary data source. Let's take a look at our data:

![bm_test](https://user-images.githubusercontent.com/67876029/139185323-6125cfad-9faa-4032-8066-6e6bfc82d316.png)

This method will use the land use DataFrame to mask out certain land use types from the crash data DataFrame. Car crashes definitely shouldn’t happen on water, and there may be other land use types you’d want to mask out. For this example, let’s assume that we want to interpolate the car crash data to just residential land use. Here’s what our inputs should look like:

    pypolate.binary(carcrash.df, landuse.df, 'C_DIG1', [2,3,4,5,6,7,8,9],  '_intp', [Count_])

The field containing land use types is named `C_DIG1`, which contains a numbered value corresponding to the land use type. Residential corresponds to `1`, so we will exclude all other values. The output of this interpolation should look similar to this:

![bm_output](https://user-images.githubusercontent.com/67876029/139191000-5ac637d4-0f8f-4959-877e-be3af21e4f7c.png)

### Setting land-use category thresholds with the limiting variable method

For this example, we can continue to use the [Philadelphia crash data](https://github.com/CityOfPhiladelphia/crash-data) and [Philadelphia land use data](https://www.opendataphilly.org/dataset/land-use). Our starting data will look like this:

![bm_test](https://user-images.githubusercontent.com/67876029/139185323-6125cfad-9faa-4032-8066-6e6bfc82d316.png)

Calling the limiting variable method will look like this:

    pypolate.lim_var(carcrash.df, landuse.df, 'C_DIG1', {1: 100, 2: 50, 3: 50}, [Count_], 'TAZ', '_intp')

And the output of the limiting variable function will look like this:

![lv_output](https://user-images.githubusercontent.com/67876029/139199364-c723ca5e-52c4-4a44-b4c8-2d6b7bf0daf6.png)

### Assigning weights to land-use categories with the n-class method

For testing the n-class method, we can continue using the [Philadelphia crash data](https://github.com/CityOfPhiladelphia/crash-data) and [Philadelphia land use data](https://www.opendataphilly.org/dataset/land-use). Our starting data will look like this again:

![bm_test](https://user-images.githubusercontent.com/67876029/139185323-6125cfad-9faa-4032-8066-6e6bfc82d316.png)

The inputs for n-class method are very similar to the limiting variable method, but instead of passing in a dictionary of thresholds based on square units, we pass in percentages as a decimal for our thresholds. The percentages should add up to 100%, regardless of how many classes you are splitting between. For this example, we’ll assign 75% to residential, 20% to commercial, and 5% to industrial:

    pypolate.n_class(carcrash.df, landuse.df, 'C_DIG1', {1: 0.75, 2: 0.20, 3: 0.05}, [Count_], 'TAZ', '_intp')

The output should look something like this:

![nc_output](https://user-images.githubusercontent.com/67876029/139212211-2f38b991-ef5a-4cbf-ab2e-bcb9f4e558a5.png)

### Disaggregating population with the parcel method

#### Description

For the parcel method, we will use [tax lot data from NYC's MapPLUTO](https://www1.nyc.gov/site/planning/data-maps/open-data/dwn-pluto-mappluto.page), and [population at the census block group level from TIGER/Line](https://www.census.gov/cgi-bin/geo/shapefiles/index.php). Our data will look like this to begin:

![pm_input](https://user-images.githubusercontent.com/67876029/139622142-f5ded048-5742-4fd3-93d0-5cf730354aaf.png)

The data that we will be interpolating is population, which is currently aggregated in census block groups. Using the parcel method, the population can be disaggregated into individual parcels. Our inputs should look like this:

    pypolate.parcel(block_group.df, parcels.df, 'UnitsTotal', 'UnitsRes', 'BldgArea', 'ResArea', [population])


The parcel method will interpolate population into two new columns which are calculated from different inputs. One of the new columns is named ara_derived (derived from adjusted residential area), and the other column is named ru_derived (derived from number of residential units). Below are the results of the parcel method, one map for each interpolation type:

![pm_ara_output](https://user-images.githubusercontent.com/67876029/139627908-ebce82a4-7031-4f73-a822-197fd73b7894.png)

![pm_ru_output](https://user-images.githubusercontent.com/67876029/139627913-7241e00d-d358-4aa9-998c-0802620bb531.png)


### Refining parcel method with the Cadastral-Based Expert Dasymetric System

Like the parcel method, we’ll be using census block groups containing population, and parcel data. In addition, we are also using a larger census zone DataFrame (which also contains population) that the smaller census zone nests inside, in this case census tracts.

The CEDS method works perfectly with census data, but theoretically will work with any two geographies that nest without intersecting.

Our input data will look like this if plotted:

![es_input](https://user-images.githubusercontent.com/67876029/139633064-46b40ecf-3030-4c98-aba0-4ebbfe39773c.png)

![parcels](https://user-images.githubusercontent.com/67876029/139633355-0e88f2f1-471b-48f4-987f-15b3e141811d.JPG)

For our inputs, the columns that we are interpolating (population) needs to have the same column name in both source DataFrames (tracts and block groups). Other than that condition, the inputs for CEDS are very similar to the parcel method.

    pypolate.expert(tracts.df, block_group.df, parcels.df, 'UnitsTotal', 'UnitsRes', 'BldgArea', 'ResArea', [population])

The mapped output of these inputs should look similar to this (the field `expert_sys` is mapped here):

![es_output](https://user-images.githubusercontent.com/67876029/139705022-f6045f26-9f2b-4d24-ae00-af0723e4695e.png)

The dataframe that results from the CEDS method contains both the `ru_derived` and `ara_derived` interpolations for population, as well as a new field named `expert_sys`. As seen in the dataframe below, CEDS determines whether to use `ru_derived` or `ara_derived` to measure population, on a census block group basis. In Block Group 3 of `GEOID` 360610271003 CEDS chooses the `ru_derived` population, then chooses the `ara_derived` population for block group 1 of `GEOID` 360610277001.

![es_pandas](https://user-images.githubusercontent.com/67876029/139714535-e98147e3-a1b4-43dd-b13d-8b8fe0b08afb.JPG)

