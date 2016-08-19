# -*- coding: utf-8 -*-
"""
Created on Tue Mar 22 03:51:13 2016

@author: jnsebgosselin
"""
import csv

def genereate_LaTex_summary(dirname):
    filename = dirname +  '/'
    with open(filename, 'r') as f:
        reader = list(csv.reader(f, delimiter='\t'))
        reader = reader[1:]
    
    
    
    
    
#        ftex = [['\\documentclass[]{article}'],
#                ['\\usepackage{booktabs}'],
#                ['\\usepackage{setspace}'],
#                ['\\usepackage{siunitx}'],
#                ['\\usepackage{fixltx2e}'],
#                ['\\begin{document}'],
#                ['\\begin{table}[!p]'],
#                ['\\centering'],
#                ['\\setstretch{1.25}'],
#                [('\\caption{List of weather stations located' +
#                  'in the study area and related information' +
#                  'about location coordinate, altitude, missing data' +
#                  'and yearly averages for the 1980-2009 period.}')],
#                ['\\resizebox{1.\linewidth}{!}{'],
#                ['\\begin{tabular}{'],
#                ['  S[table-format = 2]'],
#                ['l'],
#                ['*2S[table-format = 2.2]'],
#                ['  S[table-format = 3.1]'],
#                ['*4S[table-format = 2.1]'],
#                ['  S[table-format = 2.1]'],
#                ['  S[table-format = -1.1]' ],
#                ['  S[table-format = 1.1]'],
#                ['  S[table-format = 4.1]}'],
#                ['\\toprule'],
#                [('\\multicolumn{5}{c}{} & \\multicolumn{4}{c}{\\% of ' +
#                  'days with missing data} & \\multicolumn{4}{c}' +
#                  '{Yearly Averages}\\\\')],
#                ['\\cmidrule(lr){6-9}\\cmidrule(lr){10-13}'],
#                [('{\\#} & {Station} & {Lat.} & {Lon.} & {Alt.} & '+
#                  '{T\\textsubscript{max}} & {T\\textsubscript{min}} & '+
#                  '{T\\textsubscript{mean}} & {P\\textsubscript{tot}} &' +
#                  '{T\\textsubscript{max}} & {T\\textsubscript{min}} & ' +
#                  '{T\\textsubscript{mean}} & {P\\textsubscript{tot}} \\\\')],
#                [('& {name} & {\\SIUnitSymbolDegree N} & '+
#                  '{\\SIUnitSymbolDegree W} & {m} & {\\%} & {\\%} & {\\%} & '+
#                  '{\\%} & {\\SIUnitSymbolCelsius} & {\\SIUnitSymbolCelsius}'+
#                  ' & {\\SIUnitSymbolCelsius} & {mm} \\\\')],
#                ['\\midrule']
#                ]
#        for i in range(len(self.STANAME)):           
#            time_start = xldate_from_date_tuple((self.DATE_START[i, 0],
#                                                 self.DATE_START[i, 1],
#                                                 self.DATE_START[i, 2]), 0)
#    
#            time_end = xldate_from_date_tuple((self.DATE_END[i, 0],
#                                               self.DATE_END[i, 1],
#                                               self.DATE_END[i, 2]), 0)                                               
#            Ndata = float(time_end - time_start + 1)
#            
#            ftex.append([('%d & %s & %0.2f & %0.2f & %0.1f'
#                          ) % (i, self.STANAME[i], 
#                               self.LAT[i], self.LON[i], self.ALT[i])])
#            
#            for var in range(len(self.VARNAME)):
#                ftex[-1][0] += ' & %0.1f' % (self.NUMMISS[i, var] / Ndata * 100)
#            ftex[-1][0] += '\\\\'
#              
#        ftex.extend([['\\bottomrule'],
#                     ['\\end{tabular}}'],
#                     ['\\label{tab:selectedStations}'],
#                     ['\\end{table}'],
#                     ['\\end{document}']
#                     ])
#                     
#        fname = 'test.tex'
#        with open(fname, 'w') as f:
#            writer = csv.writer(f, delimiter='\t', lineterminator='\n')
#            writer.writerows(ftex)
            
if __name__ == '__main__':
    dirname = '../Projects/Monteregie Est/Meteo/Output'
    genereate_LaTex_summary(dirname)
    print 'coucou'