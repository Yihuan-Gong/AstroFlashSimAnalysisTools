from astropy import units as u
from dacite import from_dict
import numpy as np


from .models import (
    SimonteSigmaRhoSigmaVReturnModel,
    SimonteSigmaRhoSigmaVCalculationInfoModel
)
from ....calculate_data3d import *
from ......models import SimFileModel
from ......services import YtRawDataHelper

class SimonteSigmaRhoSigmaV:
    __simFile: SimFileModel
    __calculationInfo: SimonteSigmaRhoSigmaVCalculationInfoModel
    
    
    def setInputs(self, simFile: SimFileModel, calculationInfo: SimonteSigmaRhoSigmaVCalculationInfoModel):
        self.__simFile = simFile
        self.__calculationInfo = calculationInfo
        return self
    
    
    def getResult(self):
        deltaRhoResult = self.__getDeltaRho()
        deltaVResult = self.__getDeltaV()
        ytDataCube, _ = self.__loadDataCube()
        
        deltaRho: u.Quantity = deltaRhoResult.deltaRho
        deltaV: u.Quantity = getattr(deltaVResult, f"{self.__calculationInfo.velocityField}".split(".")[-1])
        rho: u.Quantity = ytDataCube[self.__calculationInfo.densityFieldName].to_astropy()
        soundSpeed: u.Quantity = ytDataCube[self.__calculationInfo.soundSpeedFieldName].to_astropy()
        
        numberOfCubeEachSide = self.__calculationInfo.numberOfCubeEachSide
        sigmaRho = self.__computeRmsInCubes(deltaRho/rho, numberOfCubeEachSide)
        sigmaV = self.__computeRmsInCubes(deltaV/soundSpeed, numberOfCubeEachSide)
        return SimonteSigmaRhoSigmaVReturnModel(
            sigmaRho=sigmaRho,
            sigmaV=sigmaV
        )
        
        
    
    
    def __getDeltaRho(self):
        return Data3dAnalyzor().densityFiltering(
            simFile=self.__simFile,
            calculationInfo=from_dict(
                data_class=VelocityFilteringCalculationInfoModel,
                data=self.__calculationInfo.__dict__
            )
        )
    
    
    def __getDeltaV(self):
        return Data3dAnalyzor().velocityFilteringByField(
            field=self.__calculationInfo.velocityField,
            simFile=self.__simFile,
            calculationInfo=from_dict(
                data_class=VelocityFilteringCalculationInfoModel,
                data=self.__calculationInfo.__dict__
            )
        )
        
    
    def __loadDataCube(self):
        return YtRawDataHelper().loadRawData(
            simFile=self.__simFile,
            timeMyr=self.__calculationInfo.timeMyr,
            rBoxKpc=self.__calculationInfo.rBoxKpc,
            fields=[
                self.__calculationInfo.densityFieldName,
                self.__calculationInfo.soundSpeedFieldName
            ]
        )
    
    
    def __computeRmsInCubes(self, quantity3d, numberOfCubePerSide):
        n = quantity3d.shape[0]
        cubeDim = n // numberOfCubePerSide
        n_prime = cubeDim * numberOfCubePerSide
        
        # Find the starting and ending indices to crop the array to n_prime*n_prime*n_prime
        start_idx = (n - n_prime) // 2
        end_idx = start_idx + n_prime
        
        # Crop the array to n_prime*n_prime*n_prime
        cropped_array = quantity3d[start_idx:end_idx, start_idx:end_idx, start_idx:end_idx]
        
        # Initialize the list to store RMS values
        rms_values = []
        
        # Calculate RMS for each cube
        for i in range(numberOfCubePerSide):
            for j in range(numberOfCubePerSide):
                for k in range(numberOfCubePerSide):
                    cube = cropped_array[i*cubeDim:(i+1)*cubeDim,
                                        j*cubeDim:(j+1)*cubeDim,
                                        k*cubeDim:(k+1)*cubeDim]
                    # Check if the cube is empty
                    if cube.size == 0:
                        rms_value = np.nan * quantity3d.unit
                    else:
                        # Calculate the RMS value for the cube
                        rms_value = np.sqrt(np.mean(cube.value**2)) * cube.unit
                    rms_values.append(rms_value)
        
        # Convert the list of RMS values to a 1D Quantity array
        rms_array = u.Quantity(rms_values)
        return rms_array
    
    
    