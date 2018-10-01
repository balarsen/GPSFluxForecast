import sys
import logging
import datetime as dt
import numpy as np
import scipy.stats
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import spacepy.datamodel as dm
import spacepy.pybats.ram as ram
import spacepy.pybats.kyoto as kyo
import spacepy.plot as splot
import verify

splot.style('default')

logging.basicConfig(level=logging.DEBUG,
                    format='%(message)s',
                    filename='metrics_all.log',
                    filemode='w')

def metrics(model, obs):
    metrics = verify.accuracy(model, obs)
    metrics['bias'] = verify.bias(model, obs)
    #Prediction Efficiency is generic skill score using MSE and climatology
    clim = obs.mean()
    metrics['PredEff'] = verify.skill(metrics['MSE'], verify.meanSquaredError(obs, clim))/100.0
    #linear fit params and Pearson-r, model is y and obs are x (y = mx+c)
    slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(obs, model)
    metrics['r'] = r_value
    metrics['Intercept'] = intercept
    metrics['Slope'] = slope

    return metrics

if __name__=='__main__':
    #load output from month-long run
    infile = sys.argv[1]
    ##infile = 'log_n000000.log'
    data = ram.LogFile(infile)

    useBiot = True
    useDPS = False

    #get Sym-H from Kyoto WDC
    #kyotodata = kyo.fetch('sym', data['time'][0], data['time'][-1]+dt.timedelta(minutes=1))
    #read Kyoto data from saved file
    kyotodata = dm.readJSONheadedASCII('kyotodata_Jan2005.txt')

    #make plot
    fig = plt.figure(figsize=(10,5))
    ax = fig.add_subplot(111)
    ax.plot(kyotodata['time'], kyotodata['sym-h'], color='black', label='Sym-H (Kyoto)')
    if useBiot and not useDPS:
        ax.plot(data['time'], data['dstBiot'], color='crimson', label='Sym-H (RAM)')
    elif useDPS and not useBiot:
        ax.plot(data['time'], data['dstRam'], color='crimson', label='Sym-H (RAM)')
    else:
        ax.plot(data['time'], data['dstBiot'], color='crimson', label='Sym-H (RAM/B-S)')
        ax.plot(data['time'], data['dstRam'], color='royalblue', label='Sym-H (RAM/DPS)')
    ax.set_ylabel('Sym-H [nT]')
    ax.set_xlim([data['time'][0]-dt.timedelta(minutes=1), data['time'][-1]])
    fig.autofmt_xdate()
    ax.legend()
    plt.tight_layout()
    plt.savefig('Jan2005_DstCompare_new.png')

    #make a scatterplot to illustrate the correlation/linear fit stats
    fig = plt.figure(figsize=(5,5))
    ax = fig.add_subplot(111)
    hb = ax.hexbin(kyotodata['sym-h'], data['dstBiot'], cmap='plasma', norm=LogNorm(), mincnt=1, alpha=0.7)
    cbar = plt.colorbar(mappable=hb)
    cbar.set_label('Counts')
    xvals = np.arange(-130, 70, 10)

    #Kyoto data is missing last point relative to model
    perform_dstRam = metrics(data['dstRam'], kyotodata['sym-h'])
    perform_dstBiot = metrics(data['dstBiot'], kyotodata['sym-h'])
    ax.plot(xvals, perform_dstBiot['Slope']*xvals+perform_dstBiot['Intercept'], 'r-', label='OLS')
    ax.plot(xvals, xvals, 'k--')
    ax.set_xlim([-125, 60])
    ax.set_ylim([-125, 60])
    ax.set_aspect('equal')
    ax.text(0.5, 1.05, 'y = {0:0.3f}x + {1:0.3f}'.format(perform_dstBiot['Slope'], perform_dstBiot['Intercept']),
                                                 horizontalalignment='center', transform=ax.transAxes)
    ax.set_xlabel('Sym-H (Observed) [nT]')
    ax.set_ylabel('Sym-H (Modeled) [nT]')
    if False:
        from sklearn.linear_model import TheilSenRegressor, RANSACRegressor
        #tsreg = TheilSenRegressor(random_state=77)
        reg = RANSACRegressor(random_state=77)
        reg.fit(kyotodata['sym-h'][:, np.newaxis], data['dstBiot'][:, np.newaxis])
        y_pred = reg.predict(xvals[:, np.newaxis])
        ax.plot(xvals, y_pred, 'm-', label='RANSAC')
        ax.legend()
    plt.tight_layout()
    plt.savefig('Jan2005_DstCompare_scatter_new.png')

    #now write metrics to log
    logging.info('=================')
    logging.info('===PERFORMANCE===')
    logging.info('=================')
    logging.info('N_points: {}\n'.format(len(data['dstBiot'])))

    if useBiot:
        logging.info('Biot-Savart')
        logging.info('=================')
        for key in perform_dstBiot:
            logging.info('{}: {:3.5f}'.format(key, perform_dstBiot[key]))
    if useDPS:
        logging.info('\nDPS')
        logging.info('=================')
        for key in perform_dstRam:
            logging.info('{}: {:3.5f}'.format(key, perform_dstRam[key]))
        logging.info('')
    
    if useBiot and useDPS:
        #How much better than the "RAM" method is the B-S method?
        pb = verify.percBetter(data['dstBiot'], data['dstRam'], kyotodata['sym-h'])
        logging.info('Percent Better: Biot-Savart method is better than DPS method {:3.3f}% of the time'.format(pb))

    logging.info('\nSource file: {}'.format(infile))


    #now do thresholded stats
    tvals = range(-100,10,1)
    threshStats = dm.SpaceData()
    threshStats['Threshold'] = dm.dmarray(tvals, attrs={'Notes': 'SYM-H threshold', 'Units': 'nT'})
    threshStats['HSS'] = dm.dmarray([0.0]*len(tvals), attrs={'Notes': 'Heidke Skill Score'})
    threshStats['PSS'] = dm.dmarray([0.0]*len(tvals), attrs={'Notes': 'Peirce Skill Score'})
    threshStats['POD'] = dm.dmarray([0.0]*len(tvals), attrs={'Notes': 'Probability of Detection'})
    threshStats['POFD'] = dm.dmarray([0.0]*len(tvals), attrs={'Notes': 'Probability of False Detection'})
    threshStats['FAR'] = dm.dmarray([0.0]*len(tvals), attrs={'Notes': 'False Alarm Ratio'})
    threshStats['FB'] = dm.dmarray([0.0]*len(tvals), attrs={'Notes': 'Frequency Bias'})
    threshStats['PC'] = dm.dmarray([0.0]*len(tvals), attrs={'Notes': 'Proportion Correct'})
    threshStats['Npredict'] = dm.dmarray([0.0]*len(tvals), attrs={'Notes': 'Number of "Events" predicted'})
    for idx, symThresh in enumerate(tvals):
        obs = kyotodata['sym-h']<=symThresh
        pred = data['dstBiot']<=symThresh
        ctab = verify.Contingency2x2.fromBoolean(pred, obs)
        ctab.summary()
        threshStats['HSS'][idx] = ctab.attrs['HeidkeScore']
        threshStats['PSS'][idx] = ctab.attrs['PeirceScore']
        threshStats['POD'][idx] = ctab.attrs['POD']
        threshStats['POFD'][idx]= ctab.attrs['POFD']
        threshStats['FAR'][idx] = ctab.attrs['FAR']
        threshStats['FB'][idx]  = ctab.attrs['Bias']
        threshStats['PC'][idx]  = ctab.attrs['PC']
        threshStats['Npredict'][idx] = ctab.sum(axis=1)[0]
        del obs
        del pred
    threshStats.toJSONheadedASCII('threshold_stats.txt', depend0='Threshold', order=['Threshold'])

