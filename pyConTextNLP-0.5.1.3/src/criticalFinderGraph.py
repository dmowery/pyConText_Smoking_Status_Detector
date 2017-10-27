#!/usr/bin/env python
#-*-coding: utf-8 -*- 
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.
"""criticalFinderGraph is a program that processes the impression section of dictated
radiology reports. pyContext is used to look for descriptions of acute critical
findings.

At this state, the program assumes that the reports are stored in a SQLite3 database.
The database should have a table named 'reports' with a field named 'impression'
although these values can be specified through the command line options."""
import sys

import os
from optparse import OptionParser
import sqlite3 as sqlite
import networkx as nx
import datetime, time
import pyConTextNLP.pyConTextGraph as pyConText 
import pyConTextNLP.helpers as helpers
import pyConTextNLP.itemData as itemData
import pyConTextNLP.html as html
#from critfindingItemData import *
import cPickle
import getpass
import xml.dom.minidom as minidom
import codecs

#from graphviz import *
"""helper functions to compute final classification"""

class criticalFinder(object):
    """This is the class definition that will contain the majority of processing
    algorithms for criticalFinder.
    
    The constructor takes as an argument the name of an SQLite database containing
    the relevant information.
    """
    def __init__(self, options):
        """create an instance of a criticalFinder object associated with the SQLite
        database.
        dbname: name of SQLite database
        """

        # Define queries to select data from the SQLite database
        # this gets the reports we will process
        self.query1 = '''SELECT %s,%s FROM %s'''%(options.id,options.report_text,options.table)
        

        t = time.localtime()

        self.save_dir = options.save_dir#+"-%s-%s-%s"%(t[0],t[1],t[2])

        count = 1
        if( not os.path.exists(self.save_dir) ):
            os.mkdir(self.save_dir)
        
        self.html_dir=self.save_dir+"/html/"
        if( not os.path.exists(self.html_dir) ):
            os.mkdir(self.html_dir)
            
            

        print options.dbname
        self.doGraphs = options.doGraphs
        self.allow_uncertainty = options.allow_uncertainty
        self.proc_category = options.category
        self.conn = sqlite.connect(options.dbname+".db")
        print options.dbname+".db"
        self.cursor = self.conn.cursor()
        print self.query1
        self.cursor.execute(self.query1)
        self.reports = self.cursor.fetchall()
                
        
        print "number of reports to process",len(self.reports)
        #raw_input('continue')
 

        tmp = os.path.splitext(options.odbname)
        outfile = tmp[0]+self.proc_category+"_%s.db"%(self.allow_uncertainty)
        rsltsDB = os.path.join(self.save_dir,outfile)
        if( os.path.exists(rsltsDB) ):
            os.remove(rsltsDB)
            
        
        #old database output by DM
        self.resultsConn = sqlite.connect(rsltsDB)
        self.resultsCursor = self.resultsConn.cursor()

#         
        self.resultsCursor.execute("""CREATE TABLE alerts (
            reportid TEXT,
            smokingStatus TEXT,
            report TEXT)""")
        


        # Create the itemData object to store the modifiers for the  analysis
        # starts with definitions defined in pyConText and then adds
        # definitions specific for peFinder
        
        #DM - addition
        self.context=pyConText.ConTextDocument()
        mods=itemData.instantiateFromCSV(options.lexical_kb)
        trgs=itemData.instantiateFromCSV(options.Hx_kb)
        
        self.modifiers = itemData.itemData()
        for mod in mods.keys():
            self.modifiers.prepend(mods[mod])
  
        self.targets = itemData.itemData()
        for trg in trgs.keys():
            self.targets.prepend(trgs[trg])

        
        
    def initializeOutput(self, rfile, lfile, dfile): 
        self.outString = u"""<?xml version="1.0"?>\n"""
        self.outString += u"""<markup>\n""" 
        #self.outString += u"""<pyConTextNLPVersion> %s </pyConTextNLPVersion>\n"""%pyConTextNLP.__version__
        self.outString += u"""<operator> %s </operator>\n"""%getpass.getuser()
        self.outString += u"""<date> %s </date>\n"""%time.ctime()
        self.outString += u"""<dataFile> %s </dataFile>\n"""%rfile
        self.outString += u"""<lexicalFile> %s </lexicalFile>\n""" %lfile
        self.outString += u"""<domainFile> %s </domainFile>\n""" %dfile  
        
    def closeOutput(self):
        self.outString +=u"""</markup>\n"""
        
    def getOutput(self):
        return self.outString
 

    def analyzeReport(self,csv,eHOST, idName,report, modFilters = ['indication','pseudoneg','probable_negated_existence',
                          'definite_negated_existence', 'probable_existence',
                          'definite_existence','future', 'historical', 'cigarette_units', 'frequency', 
                          'amount', 'current', 'past', 'cessation', "initiation","pack_year", ]
        ):
        """given an individual radiology report, creates a pyConTextSql
        object that contains the context markup

        report: a text string containing the radiology reports
        mode: which of the pyConText objects are we using: disease
        modFilters: """

        self.context = pyConText.ConTextDocument()
        targets=self.targets
        modifiers = self.modifiers
        if modFilters == None :
           modFilters = ['indication','pseudoneg','probable_negated_existence',
                          'definite_negated_existence', 'probable_existence',
                          'definite_existence', 'future', 'historical', 'cigarette_units', 'frequency', 
                          'amount', 'current', 'past', 'cessation', "initiation","pack_year", ]

        
        fo=open(os.getcwd()+"/eHOST_FILES/corpus/%s"%idName, "w")
        fo.write(report.strip())
        fo.close()
        
        splitter = helpers.sentenceSplitter()
        sentences = splitter.splitSentences(report)
        count = 0

        
        for s in sentences:

            markup=pyConText.ConTextMarkup()
            markup.setRawText(s)
            markup.cleanText() 
            markup.markItems(modifiers, mode="modifier")
            markup.markItems(targets, mode="target")
            markup.pruneMarks()
            markup.applyModifiers()
            markup.dropInactiveModifiers()
            count += 1
            
            self.context.addMarkup(markup)

            
        idName, sevFlag, htmlStr = html.mark_document_with_html(csv, eHOST, idName,self.context)

            
        self.outString+= self.context.getXML()+u"\n"
        print self.context.getXML()#;raw_input()
        return  idName, sevFlag,  htmlStr 
            


    def plotGraph(self):
        cntxt = self.context["disease"]
        g = cntxt.getDocumentGraph()
        ag = nx.to_pydot(g, strict=True)
        gfile = os.path.join(self.save_dir,
                             "report_%s_unc%s_%s_critical.pdf"%(self.proc_category,
                                                                self.allow_uncertainty,
                                                          self.currentCase))
        ag.write(gfile,format="pdf")
    def processReports(self):
        """For the selected reports (training or testing) in the database,
        process each report with peFinder
        """
        count = 0
        fout=open(self.save_dir+"/timePerDocument.txt","w")
        fout.write("documentName\tstart\tend\tdelta\n")
        csvFile=open(self.save_dir+"/structured_predicates.txt", "w")
        eHOST=open(self.save_dir+"/eHOST_annotations.txt", "w")
        eHOST.write("File Name\tTerm\tSentence Span\tClass\n")
        
        outpath=os.getcwd()+"/eHOST_FILES/"
        if not os.path.exists(outpath):
            os.mkdir(outpath)
            
        outpath=os.getcwd()+"/eHOST_FILES/corpus"
        if not os.path.exists(outpath):
            os.mkdir(outpath)
        
        for r in self.reports:            

            startTime=time.time()
            self.currentCase = r[0]
            self.currentText = r[1].lower()
            self.outString+= u"<case>\n"
            self.outString+= u"<docName> %s </docName>\n"%r[0]
            idName, sevFlag,findingsStr=self.analyzeReport(csvFile,eHOST, r[0],self.currentText, 
                                modFilters=['indication','pseudoneg','probable_negated_existence',
                          'definite_negated_existence', 'probable_existence',
                          'definite_existence', 'historical', 'cigarette_units', 'frequency', 
                          'amount', 'current', 'past', 'cessation', "initiation","pack_year"])
            
            self.outString+= u"</case>\n"
            endTime=time.time()

            self.recordResults(idName ,sevFlag,findingsStr) 


            try: fout.write("%s\t%s\t%s\t%s\n"%(idName, str(startTime),str(endTime), str(endTime-startTime)))
            except: pass
        csvFile.close()
        fout.close()
    
    def recordResults(self, idName, smokingStatus,findingsStr):

        query = """INSERT INTO alerts (reportid, smokingStatus, report) VALUES (?,?,?)"""
        self.resultsCursor.execute(query,(self.currentCase ,smokingStatus,findingsStr))
        fileName="%s.html"%idName
        fo=open(self.html_dir+fileName,"w")
        fo.write(findingsStr)
        fo.close()
        
        
        
    def cleanUp(self):     
        self.resultsConn.commit()

        

        
def modifies(g,n,modifiers):
    pred = g.predecessors(n)
    if( not pred ):
        return False
    pcats = [n.getCategory().lower() for n in pred]
    
    return bool(set(pcats).intersection([m.lower() for m in modifiers]))
    
def getParser():
    """Generates command line parser for specifying database and other parameters"""
    parser = OptionParser()

    parser.add_option("-l","--lexical_kb",dest='lexical_kb',default='./docsConText_KnowledgeBase_modifiers.txt',
                       help='name of file for lexical knowledge base')
    parser.add_option("-k","--Hx_kb",dest='Hx_kb',default='./docsConText_KnowledgeBase_targets.txt',
                       help='name of file for Hx knowledge base')
    parser.add_option("-d","--db",dest='dbname',
                       help='name of db containing reports to parse', default="./patient_corpus")
    parser.add_option("-x","--xml",dest='xfile',default='./SHx_pyConText_output_mentions_test',
                       help='name of xml output file for Hx predictions')
    parser.add_option("-o","--odb",dest='odbname',
                       help='name of db containing results', default="SHx_Results_test")
    parser.add_option("-s","--save_dir",dest='save_dir',default='./reportsOutput/',
                       help='directory in which to store graphs of markups')
    parser.add_option("-z","--html_dir",dest='html_dir',default='./reportsOutput/html/',
                       help='directory in which to store html markups per document')
    parser.add_option("-t","--table",dest='table',default='reports',
                       help='table in database to select data from')
    parser.add_option("-i","--id",dest='id',default='reportid',
                       help='column in table to select identifier from')
    parser.add_option("-g", "--graph",action='store_true', dest='doGraphs',default=False)
    parser.add_option("-r","--report",dest='report_text',default='report',
                       help='column in table to select report text from')
    parser.add_option("-c","--category",dest='category',default='ALL',
                       help='category of critical finding to search for. If ALL, all categories are processed')
    parser.add_option("-u","--uncertainty_allowed",dest="allow_uncertainty",
                       action="store_true",default=False)
    parser.add_option("-b","--status",dest="status", default="smokingStatus",
                      help='smoking status label')
    return parser

def main():
    #python criticalFinderGraph.py -d patient_corpus.db
    

    parser = getParser()
    (options, args) = parser.parse_args()
    if( options.dbname == options.odbname ):
        raise ValueError("output database must be distinct from input database")        
    pec = criticalFinder(options)
    pec.initializeOutput(options.dbname+".db", options.lexical_kb, options.Hx_kb)
    pec.processReports()
    pec.closeOutput()
    xmlStr=pec.getOutput()
    fout=codecs.open(options.save_dir+"SHx_mentions_test.xml","w","utf-8" )
    fout.write(xmlStr)
    fout.close()
    pec.cleanUp()

    
    
if __name__=='__main__':
    
    main()