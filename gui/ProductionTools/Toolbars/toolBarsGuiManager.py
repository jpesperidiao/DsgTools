# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DsgTools
                                 A QGIS plugin
 Brazilian Army Cartographic Production Tools
                              -------------------
        begin                : 2018-04-12
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Philipe Borba - Cartographic Engineer @ Brazilian Army
        email                : borba.philipe@eb.mil.br
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

from __future__ import absolute_import
from builtins import object
import os.path
import sys

from .MinimumAreaTool.minimumAreaTool import MinimumAreaTool
from .InspectFeatures.inspectFeatures import InspectFeatures
from qgis.PyQt.QtCore import QObject

class ToolbarsGuiManager(QObject):

    def __init__(self, manager, iface, parentMenu = None, toolbar = None):
        """Constructor.
        """
        super(ToolbarsGuiManager, self).__init__()
        self.manager = manager
        self.iface = iface
        self.parentMenu = parentMenu
        self.toolbar = toolbar
        self.iconBasePath = ':/plugins/DsgTools/icons/'
    
    def initGui(self):
        #adding minimum area tool
        self.minimumAreaTool = MinimumAreaTool(self.iface, parent = self.parentMenu)
        self.toolbar.addWidget(self.minimumAreaTool)
        self.inspectFeaturesTool = InspectFeatures(self.iface, parent = self.parentMenu)
        self.toolbar.addWidget(self.inspectFeaturesTool)

    
    def unload(self):
        pass