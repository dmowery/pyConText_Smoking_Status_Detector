'''
Created on May 22, 2015

@author: daniellemowery
'''
"""Module containing functions for generating various display options for pyConTextNLP

Originally written by Brian Chapman; significantly adapted and extended by Danielle Mowery"""


import copy
from utils import get_document_markups

def __sort_by_span(nodes):
    n = copy.copy(nodes)
    n.sort(key=lambda x: x.getSpan())
    return n

def __insert_color(txt,s,c):
    """insert HTML span style into txt. The span will change the color of the 
    text located between s[0] and s[1]:
    txt: txt to be modified
    s: span of where to insert tag
    c: color to set the span to"""

    return '<span style="color: %s">'%c+\
           txt +'</span>'

def mark_text(csvFile, eHOST, imageID, docScope, scope,txt,nodes,colors = {"name":"red","pet":"blue"}):

    sentStart,sentFinish=scope
    end=sentFinish

    docSentStart=docScope-end
    docScope+=sentFinish
    
    if not nodes:
        return txt, docScope
    else:
        predicateFlag=False

        nodesLst=[]
        semanticLst=[]
        for n in nodes:
            
            ##Add the category and its value to nodesLst for output

            if (n.getCategory()=="TOBACCO_PIPE") or (n.getCategory()=="TOBACCO_CIGAR") or (n.getCategory()=="TOBACCO_CIGARETTES"): 
                semanticLst.append("Type: %s"%n.getCategory().lower()); semanticLst.append("Smoking Tobacco: %s"%n.getPhrase().lower())
                predicateFlag=True
            elif (n.getCategory()=="TOBACCO") or (n.getCategory()=="CURRENT_TOBACCO") or (n.getCategory()=="PAST_TOBACCO") or (n.getCategory()=="NO_TOBACCO"): predicateFlag=True
            elif (n.getCategory()=="CIGARETTE_UNITS"): predicateFlag=True
            
            if n.getCategory() == "AMOUNT": semanticLst.append("Number: %s"%n.getPhrase())
            
            #non smoker - never 
            if( (n.getCategory()=="PROBABLE_NEGATED_EXISTENCE") or (n.getCategory()=="DEFINITE_NEGATED_EXISTENCE")): t="a"; semanticLst.append("Negation: %s"%n.getPhrase().lower())
             
            #past smoker - ex-smoker 
            elif (n.getCategory()=="PAST_TOBACCO"): t="b"; semanticLst.append("Historical: %s"%n.getPhrase().lower())
            
            #non smoker - non-smoker
            elif (n.getCategory()=="NO_TOBACCO"): t="c"; semanticLst.append("Negation: %s"%n.getPhrase().lower())

            #current smoker -  quit 
            elif (n.getCategory()=="CESSATION") : t="d"; semanticLst.append("End: %s"%n.getCategory().lower())
            
            #current smoker - if 
            elif (n.getCategory()=="FUTURE") : t="e"; semanticLst.append("Hypothetical/Future: %s"%n.getPhrase().lower())
            
            #past smoker - years ago
            elif ((n.getCategory()=="DATE") or (n.getCategory()=="POINT") ): t="f"; semanticLst.append("Date: %s"%n.getPhrase())
            
            #current smoker - cigs
            elif (n.getCategory()=="CIGARETTE_UNITS")  :t="g"; semanticLst.append("Units: %s"%n.getPhrase())
            
            #in the past
            elif (n.getCategory()=="HISTORICAL"):t="h"; semanticLst.append("Historical: %s"%n.getPhrase().lower())
            
            #recently 
            elif (n.getCategory()=="CURRENT" ):t="i"; semanticLst.append("Recent: %s"%n.getPhrase().lower())
            
            elif (n.getCategory()=="INITIATION"): t="i"; semanticLst.append("Start: %s"%n.getCategory().lower())
            
            #current smoker - each week
            elif (n.getCategory()=="FREQUENCY")  :t="j"; semanticLst.append("Frequency: %s"%n.getPhrase())
            
            elif (n.getCategory()=="PACK_YEAR"): semanticLst.append("Pack years: %s"%n.getPhrase())
            

            #unsure or nothing stated
            else:  
                t=n.getCategory()
            
            nodesLst.append(t)
            
        nodesLst.sort()
        semanticLst.sort()

        
        if predicateFlag==True:
           #non smoker - never smoked
           if ("a" in nodesLst) and ("b" in nodesLst): cSent="NON-SMOKER"
           #past smoker - ex-smoker
           elif ("b" in nodesLst): cSent="PAST SMOKER"
           #non smoker - non-smoker
           elif ("c" in nodesLst): cSent="NON-SMOKER"
           #past smoker -  quit in date or point in time
           elif ("d" in nodesLst) and ("f" in nodesLst): cSent="PAST SMOKER"
           #current smoker - if you decide to quit
           elif ("d" in nodesLst) and ("e" in nodesLst): cSent="CURRENT SMOKER"
           #current smoker - please quit
           elif ("d" in nodesLst) and ("i" in nodesLst): cSent="CURRENT SMOKER" 
           #non smoker - no hx of smoking 
           elif ("a" in nodesLst) and ("h" in nodesLst): cSent="NON-SMOKER"
           #past smoker - tobacco usage in the past or former smoker --
           elif ("h" in nodesLst): cSent="PAST SMOKER"
           #current smoker - does not want to quit
           elif ("d" in nodesLst) and ("a" in nodesLst): cSent="CURRENT SMOKER"
           #current smoker - quantity/frequency
           elif ("g" in nodesLst) and ("j" in nodesLst): cSent="CURRENT SMOKER"
           #past smoker -  quit smoking
           elif ("d" in nodesLst) and not("a" in nodesLst): cSent="PAST SMOKER"
           #current smoker -  long standing smoking hx
           elif ("i" in nodesLst): cSent="CURRENT SMOKER"
           #denies smoking
           elif ("a" in nodesLst): cSent="NON-SMOKER"
           # any other default with smoking mention
           elif not("a" in nodesLst): cSent="CURRENT SMOKER"
           
           
           else: cSent="UNKNOWN"
        else: cSent="UNKNOWN"
        

        #write logic to check for all fields
        csvFile.write("%s\t%s\t%s\n"%(imageID, cSent, "\t".join(semanticLst)))

        docSentStart=docScope-sentFinish
        eHOST.write("%s\t%s\t%s\t%s\n"%(imageID, txt, str((docSentStart,docScope)), cSent))
        
        
        return  __insert_color(txt,n.getSpan(),colors.get(n.getCategory()[0],cSent)), docScope
                                 


def mark_document_with_html(csvFile,eHOST, imageID,doc,colors = {"name":"red","pet":"blue"}):
    """takes a ConTextDocument object and returns an HTML paragraph with marked phrases in the 
    object highlighted with the colors coded in colors
    
    doc: ConTextDocument
    colors: dictionary keyed by ConText category with values valid HTML colors
    
    """
    docScope=0
    print imageID
    annotatedStr=""
    for m in get_document_markups(doc):
        findingStr,docScope= mark_text(csvFile,eHOST, imageID, docScope, m.graph['__scope'], m.graph['__txt'],
                                                 __sort_by_span(m.nodes()),
                                                 colors=colors)
        annotatedStr+=findingStr#;raw_input()

    findingsStr= """ %s """%annotatedStr
    headerStr="""<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">\n\n"""
    
    documentString = u""; sentenceOffsets = {}
    sections = doc.getDocumentSections()
    for s in sections:
        markups = doc.getSectionMarkups(s)
        for m in markups:
            sentenceOffsets[m[0]] = len(documentString)
            documentString += m[1].getText()
    
    # current over past
    if "PAST SMOKER" in findingsStr: sevFlag="PAST SMOKER"
    elif "CURRENT SMOKER" in findingsStr: sevFlag="CURRENT SMOKER"
    elif "NON-SMOKER" in findingsStr: sevFlag="NON-SMOKER"
    else: sevFlag="UNKNOWN"
    
    findingsStr=findingsStr.replace("PAST SMOKER", "#ff0000")
    findingsStr=findingsStr.replace("CURRENT SMOKER", "#0000ff")
    findingsStr=findingsStr.replace("NON-SMOKER", "#00ff00")
    findingsStr=findingsStr.replace("UNKNOWN", "#000000")
    
    if sevFlag=="PAST SMOKER": c="#ff0000"
    elif sevFlag=="CURRENT SMOKER": c="#0000ff"
    elif sevFlag=="NON-SMOKER": c="#00ff00"
    elif sevFlag =="UNKNOWN": c="#000000"
    
    statusTag='<span style="color: %s">%s'%(c,sevFlag)+'</span>'
        
    docCSS="""<html>\n\n<head>\n<meta http-equiv="Content-Type" content="text/html; charset=utf-8">\n\n<meta http-equiv="Content-Style-Type" content="text/css">\n\n<style type="text/css">\n
    \t.PAST SMOKER {color: #ff0000}\n
    \t.CURRENT SMOKER {color: #0000ff}\n
    \t.NON-SMOKER {color: #00ff00}\n
    \t.UNKNOWN {color: #000000}\n</style>\n<title>\n</title>\n</head>\n<body>\n\n<p>Image ID: <imageid>%s</imageid></p>\n<p>SMOKING STATUS: <status>%s</status></p>\n"""%(imageID,statusTag)
    
    findingsStr=headerStr+docCSS+findingsStr#;raw_input()
    
    return imageID,sevFlag, findingsStr








