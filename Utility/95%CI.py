from statsmodels.stats.proportion import proportion_confint
print(proportion_confint(count=0, nobs=788, alpha=(1 - 0.95),method='wilson'))
print([i*100 for i in proportion_confint(count=18, nobs=78+18, alpha=(1 - 0.95),method='wilson')])
print([i*100 for i in proportion_confint(count=194, nobs=194+355, alpha=(1 - 0.95),method='wilson')])
