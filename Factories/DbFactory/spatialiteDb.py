# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DsgTools
                                 A QGIS plugin
 Brazilian Army Cartographic Production Tools
                              -------------------
        begin                : 2015-10-21
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Philipe Borba - Cartographic Engineer @ Brazilian Army
        email                : borba@dsg.eb.mil.br
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from DsgTools.Factories.DbFactory.abstractDb import AbstractDb
from PyQt4.QtSql import QSqlQuery, QSqlDatabase
from PyQt4.QtGui import QFileDialog
from DsgTools.Factories.SqlFactory.sqlGeneratorFactory import SqlGeneratorFactory
from osgeo import ogr

class SpatialiteDb(AbstractDb):

    def __init__(self):
        super(SpatialiteDb,self).__init__()
        self.db = QSqlDatabase('QSQLITE')
        self.gen = SqlGeneratorFactory().createSqlGenerator(True)
    
    def connectDatabase(self,conn=None):
        if conn is None:
            self.connectDatabaseWithGui()
        else:
            self.db.setDatabaseName(conn)
    
    def connectDatabaseWithGui(self):
        fd = QFileDialog()
        filename = fd.getOpenFileName(filter='*.sqlite')
        self.db.databaseName(filename)
    
    def connectDatabaseWithQSettings(self,name):
        return None

    def connectDatabaseWithParameters(self,host,port,database,user,password):
        return None
    
    def listGeomClassesFromDatabase(self):
        self.checkAndOpenDb()
        classList = []
        sql = self.gen.getTablesFromDatabase()
        query = QSqlQuery(sql, self.db)
        while query.next():
            tableName = str(query.value(0))
            layerName = tableName
            classList.append(layerName)
        return classList
    
    def listComplexClassesFromDatabase(self):
        self.checkAndOpenDb()
        classList = []
        sql = self.gen.getTablesFromDatabase()
        query = QSqlQuery(sql, self.db)
        while query.next():
                tableName = str(query.value(0))
                layerName = tableName
                tableSchema = layerName.split('_')[0]
                classList.append(layerName)
        return classList    

    def getConnectionFromQSettings(self, conName):
        return None

    def storeConnection(self, server):
        return None
        
    def getServerConfiguration(self, name):
        return None


    def getStructureDict(self):
        self.checkAndOpenDb()
        classDict = dict()
        sql = self.gen.getStructure(self.getDatabaseVersion())        
        query = QSqlQuery(sql, self.db)
        while query.next():
            className = str(query.value(0))
            classSql = str(query.value(1))
            if className.split('_')[0] == 'complexos' or className.split('_')[-1] in ['p','l','a']:
                if className not in classDict.keys():
                    classDict[className]=dict()
                classSql = classSql.split(className)[1]
                sqlList = classSql.replace('(','').replace(')','').replace('\"','').replace('\'','').split(',')
                for s in sqlList:
                     fieldName = str(s.strip().split(' ')[0])
                     classDict[className][fieldName]=fieldName

        return classDict
    
    def makeOgrConn(self):
        constring = self.db.databaseName()
        return constring

    def buildOgrDatabase(self):
        con = self.makeOgrConn()
        return ogr.Open(con,update=1)

    def getNotNullDict(self):
        return None

    def getDomainDict(self):
        return None 

    def validateWithOutputDatabaseSchema(self,outputAbstractDb):
        invalidated = self.buildInvalidatedDict()
        outputdbStructure = outputAbstractDb.getStructureDict()
        domainDict = outputAbstractDb.getDomainDict()
        classes =  self.listClassesWithElementsFromDatabase()
        notNullDict = outputAbstractDb.getNotNullDict()
        
        for cl in classes.keys():
            if cl in outputdbStructure.keys():
                (schema,table) = self.getTableSchema(cl)
                outputClass = self.translateOGRLayerNameToOutputFormat(cl,outputAbstractDb)
                allAttrList = outputdbStructure[cl].keys()
                if schema == 'complexos':
                    attrList = ['id']
                else:
                    attrList = ['OGC_FID']
                for att in allAttrList:
                    if att not in attrList:
                        attrList.append(att)
                sql = self.gen.getFeaturesWithSQL(cl,attrList) 
                query = QSqlQuery(sql, spatialiteDB)
                
                if cl not in domainDict.keys():
                    invalidated['classNotFoundInOutput'].append(cl) 
                
                while query.next():
                    id = query.value(0)
                    #detects null lines
                    for i in range(len(attrList)):
                        nullLine = True
                        value = query.value(i)
                        if value <> None:
                            nullLine = False
                            break
                    if nullLine:
                        if cl not in invalidated['nullLine'].keys():
                            invalidated['nullLine'][cl]=0
                        invalidated['nullLine'][cl]+=1
                    
                    #validates pks
                    if id == None and (not nullLine):
                        if cl not in invalidated['nullPk'].keys():
                            invalidated['nullPk'][cl]=0
                        invalidated['nullPk'][cl]+=1
                    
                    for i in range(len(attrList)):
                        value = query.value(i)
                        #validates domain
                        if outputClass in domainDict.keys():    
                            if attrList[i] in domainDict[outputClass].keys():
                                if value not in domainDict[outputClass][attrList[i]] and (not nullLine):
                                    invalidated = self.utils.buildNestedDict(invalidated, ['notInDomain',cl,id,attrList[i]], value)
                        #validates not nulls
                        if outputClass in notNullDict.keys():
                            if outputClass in domainDict.keys():
                                if attrList[i] in notNullDict[outputClass] and attrList[i] not in domainDict[outputClass].keys():
                                    if (value == None) and (not nullLine) and (attrList[i] not in domainDict[outputClass].keys()):
                                        invalidated = self.utils.buildOneNestedDict(invalidated, ['nullAttribute',cl,id,attrList[i]], value)             
                            else:
                                if attrList[i] in notNullDict[outputClass]:
                                    if (value == None) and (not nullLine) and (attrList[i] not in domainDict[outputClass].keys()):
                                        invalidated = self.utils.buildOneNestedDict(invalidated, ['nullAttribute',cl,id,attrList[i]], value)
                        if outputClass in domainDict.keys():
                            if attrList[i] not in domainDict[outputClass].keys():
                                invalidated = self.utils.buildNestedDict(invalidated, ['attributeNotFoundInOutput',cl], [attrList[i]])
        return invalidated
    
    def translateOGRLayerNameToOutputFormat(self,lyr,ogrOutput):
        if ogrOutput.GetDriver().name == 'SQLite':
            return lyr
        if ogrOutput.GetDriver().name == 'PostgreSQL':
            return str(lyr.split('_')[0]+'.'+'_'.join(lyr.split('_')[1::]))
    
    def getTableSchema(self,lyr):
        schema = lyr.split('_')[0]
        className = lyr.split('_')[1::]
        return (schema,className)
    
    #TODO: treat each case (hammer time and don't touch my data)
    def convertToPostgis(self, outputAbstractDb,type=None):
        invalidated = self.validateWithOutputDatabaseSchema(outputAbstractDb)
        hasErrors = self.makeValidationSummary(invalidated)
        if type == 'untouchedData':
            if hasErrors:
                self.signals.updateLog.emit(self.tr('\n\n\nConversion not perfomed due to validation errors! Check log above for more information.'))
                return False
            else:
                (inputOgrDb, outputOgrDb, fieldMap, inputLayerList) = self.prepareForConversion(outputAbstractDb)
                status = self.translateDS(inputOgrDb, outputOgrDb, fieldMap, inputLayerList)
                return status
        if type == 'fixData':
            if hasErrors:
                (inputOgrDb, outputOgrDb, fieldMap, inputLayerList) = self.prepareForConversion(outputAbstractDb)
                status = self.translateDSWithDataFix(inputOgrDb, outputOgrDb, fieldMap, inputLayerList, invalidated)
                return status
            else:
                (inputOgrDb, outputOgrDb, fieldMap, inputLayerList) = self.prepareForConversion(outputAbstractDb)
                status = self.translateDS(inputOgrDb, outputOgrDb, fieldMap, inputLayerList)
                return status
        return None
    
    def convertToSpatialite(self, outputAbstractDb,type=None):
        return None   
    
    def translateDSWithDataFix(inputOgrDb, outputOgrDb, fieldMap, inputLayerList, invalidated):
        return None
    
    def getDatabaseVersion(self):
        self.checkAndOpenDb()
        version = '2.1.3'
        try:
            sqlVersion = self.gen.getEDGVVersion()
            queryVersion =  QSqlQuery(sqlVersion, self.db)
            while queryVersion.next():
                version = queryVersion.value(0)
        except:
            version = '2.1.3'
                    
        return version
    

    