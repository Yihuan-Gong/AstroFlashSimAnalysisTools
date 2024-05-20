from typing import Tuple, List
from astropy import units as u
import mirpyidl as idl
import numpy as np
import os

from ..model import (
    VelocityFilteringData3dReturnModel
)
from ......services import YtRawDataHelper
from ......utility import DataConverter


class CompSoleFilter3d:
    __velx: u.Quantity
    __vely: u.Quantity
    __velz: u.Quantity
    __dens: u.Quantity
    dx: u.Quantity
    velxComp: u.Quantity
    velyComp: u.Quantity
    velzComp: u.Quantity
    velxSole: u.Quantity
    velySole: u.Quantity
    velzSole: u.Quantity
    
    
    
    def __init__(self, velx: u.Quantity, vely: u.Quantity, velz: u.Quantity, dens: u.Quantity, dx: u.Quantity) -> None:
        self.__velx = velx.cgs
        self.__vely = vely.cgs
        self.__velz = velz.cgs
        self.__dens = dens.cgs
        self.dx = dx.cgs
    
    
    def filter(self):
        self.__setIdlVariables()
        for idlCommand in self.__getIdlFilteringScript():
            try:
                idl.execute(idlCommand)
            except idl.IdlArithmeticError:
                pass
        self.__retrieveResultFromIdl()
        
    
    def __setIdlVariables(self):
        velxIdl: np.ndarray = self.__velx.value
        velyIdl: np.ndarray = self.__vely.value
        velzIdl: np.ndarray = self.__velz.value
        densIdl: np.ndarray = self.__dens.value
        
        idl.setVariable("vx1", velxIdl)
        idl.setVariable("vx2", velyIdl)
        idl.setVariable("vx3", velzIdl)
        idl.setVariable("rho", densIdl)
        
        dims = densIdl.shape
        idl.setVariable("nx1", dims[0])
        idl.setVariable("nx2", dims[1])
        idl.setVariable("nx3", dims[2])
        
        dxIdl = float(self.dx.value)
        idl.setVariable("dx1", dxIdl)
        idl.setVariable("dx2", dxIdl)
        idl.setVariable("dx3", dxIdl)
    
    
    
    def __getIdlFilteringScript(self) -> List[str]:
        filePath = os.path.join(os.path.dirname(__file__), 'idl/decomposeVel.pro')
        with open(filePath, 'r', encoding='utf-8') as file:
            fileContent = file.read()
        return fileContent.split("\n")

    
    def __retrieveResultFromIdl(self):
        self.velxComp = self.__idlFormatToPythonFormat(idl.getVariable("vx1c")) * self.__velx.unit
        self.velyComp = self.__idlFormatToPythonFormat(idl.getVariable("vx2c")) * self.__vely.unit
        self.velzComp = self.__idlFormatToPythonFormat(idl.getVariable("vx3c")) * self.__velz.unit
        self.velxSole = self.__idlFormatToPythonFormat(idl.getVariable("vx1i")) * self.__velx.unit
        self.velySole = self.__idlFormatToPythonFormat(idl.getVariable("vx2i")) * self.__vely.unit
        self.velzSole = self.__idlFormatToPythonFormat(idl.getVariable("vx3i")) * self.__velz.unit
    
    
    def __idlFormatToPythonFormat(self, idlArr: np.ndarray):
        return idlArr.transpose()