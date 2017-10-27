'''
Created on Jun 23, 2014

@author: Danielle Mowery
'''
import re, sys, os, random, glob, shutil, sqlite3
import sys
reload(sys)
sys.setdefaultencoding("utf-8")


def createSqliteDB(qDB):
    conn=sqlite3.connect(qDB)
    curs=conn.cursor()
    curs.execute('''
    CREATE TABLE reports(   id text not null,
                            reportid text,
                            report text)''');
                            
    field_count=3
    markers = ', '.join(['?']*field_count)
    query = 'INSERT INTO reports VALUES (%s)'%markers
    print "Table is created"
    
    conn.commit()
    conn.close()
    
def queryDB(qDB, fileRefDict):
    conn=sqlite3.connect(qDB)
    curs=conn.cursor();ids=0
    
    createSqliteDB(qDB)
    
    for key in fileRefDict.keys():
        ids+=1; print "DB", ids
        txt=fileRefDict[key]
        

        curs.execute("""INSERT INTO reports VALUES (?,?,?)""", (unicode(ids), unicode(key), unicode(txt)) )
    conn.commit()
    conn.close()
if __name__ == "__main__":
    
    #path="<point to your directory containing your individual text files e.g.,/USER/YOU/DESKTOP/DIRECTORY_OF_FILES/*.txt>"
    radTxts=glob.glob(path)
    print radTxts
    fileRefDict={};ids=0
    for txtPath in radTxts:
        txt=open(txtPath).read()
        txt=txt.decode("ISO-8859-1").strip()
        txtName=os.path.split(txtPath)[-1]

        ids+=1
        fileRefDict[txtName]=txt
            
            
        
        
    queryDB(os.getcwd()+"/pyConTextNLP-0.5.1.3/src/patient_corpus.db", fileRefDict)


