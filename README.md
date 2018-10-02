# GPSFluxForecast
Work on the forecasting of GPS fluxes

## Predict GPS fluxes using K-D Trees

Details:
* 8 hour CXD Fluxes form Morley
* 1 energy: 1.6 MeV
* 1 L: L = 4.25-4.5
* 2001-2016 (or more)
* log fluxes (standardized?)
* choose 10 intervals
    * 5 storms
    * 5 non storms
* interval, 7 days prior, 21 days forward


Data: initial commit of pre-processed CXD data

Data source is the initial public release of CXD data (v1.03)
indexed at data.gov. The data are binned in time and McIlwain L
and then the slice between L=4.25 and L=4.5 is taken for 3 energies.
This file has 0.425MeV, 1MeV and 1.6 MeV. These were the data
presented by Morley et al. at the 2016 Fall AGU meeting (abstract
archived by NASA ADS with bibcode 2016AGUFMSM23C..07M). The time bin
is 8 hours. All available CXD data in each bin have been averaged
to obtain the mean flux. No data cleaning was performed prior to the
binning/averaging.



### Changelog:
* 2018-10-01: BAL - Initial discussions and outline of work
* 2018-10-02: SM - CXD Data
* 2018-10-02: BAL - CXD data prep and transformation into vectors for K-D
* 2018-10-02: BAL - OMNI data prep and transformation into vectors for K-D



