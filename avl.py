import subprocess as sp
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import os
import shutil

from geometry import Plane

def avl_cmd(cmd_str:str)->None:
    avl_subprocess=sp.Popen(
        ['avl.exe'],
        stdin=sp.PIPE,
        stdout=sp.PIPE,
        stderr=sp.PIPE
    )

    avl_subprocess.communicate(input=cmd_str.encode())

    return None

class Case():
    def __init__(self,Xcg,Ycg,Zcg,mass,Ixx=None,Iyy=None,Izz=None,velocity=None,alpha=None,modes=False,polars=False,id=False):
        self.Xcg=Xcg
        self.Ycg=Ycg
        self.Zcg=Zcg
        self.Ixx=Ixx
        self.Iyy=Iyy
        self.Izz=Izz
        self.mass=mass
        self.velocity=velocity
        self.alpha=alpha
        self.case_file=None
        self.Cl=None
        self.Cd=None
        self.modes_results_file=None
        self.polars_results_file=None
        self.modes=modes
        self.polars=polars
        self.id=id
        self.Clb=None
        self.Clp=None
        self.spiral=None

    def write_aero_case(self):
        case_str =  "\n---------------------------------------------\n"
        case_str += f"Run case  1:\n\n"
        case_str += f"alpha -> alpha = {self.alpha}\n"
        case_str += f"X_cg={self.Xcg} Lunit\n"
        case_str += f"Y_cg={self.Ycg} Lunit\n"
        case_str += f"Z_cg={self.Zcg} Lunit\n"
        case_str += f"mass={self.mass} kg\n"
        case_str += f"Ixx={self.Ixx} kg-m^2\n"
        case_str += f"Iyy={self.Iyy} kg-m^2\n"
        case_str += f"Izz={self.Izz} kg-m^2\n"
        case_str += f"velocity={self.velocity} m/s\n"
        case_str += "density=1.225 kg-m^3\n"
        case_str += "grav.acc.=0.98 m/s^2\n"

        path=f"cases/{str(self.alpha)}deg.case"

        with open(path,'w') as f:
            f.write(case_str)

        self.case_file=path

        return None

    def write_stab_case(self)->None:
        """
        Creates case string & writes to file
        """
        case_str =  "\n---------------------------------------------\n"
        case_str += "Run case  1:\n\n"
        case_str += f"X_cg={self.Xcg} Lunit\n"
        case_str += f"Y_cg={self.Ycg} Lunit\n"
        case_str += f"Z_cg={self.Zcg} Lunit\n"
        case_str += f"mass={self.mass} kg\n"

        path="cases/tail.case"
        with open(path,'w') as file:    #   Saves case file
            file.write(case_str)

        self.case_file=path

        return None 

class Aero():
    def __init__(self,config_file:str):
        path=os.path.abspath(os.getcwd())
        if os.path.isdir(path+"/cases")==True:
            shutil.rmtree(path+"/cases")
        os.mkdir(path+"/cases")
        if os.path.isdir(path+"/results")==True:
            shutil.rmtree(path+"/results")
        os.mkdir(path+"/results")

        self.read_config(config_file)

        alpha_range=np.linspace(
            self.alpha0,
            self.alpha1,
            int(1+(self.alpha1-self.alpha0)/self.increment)
        )

        self.cases=[]
        for alpha in alpha_range:
            self.cases.append(Case(
                Xcg=self.Xcg,
                Ycg=self.Ycg,
                Zcg=self.Zcg,
                Ixx=self.Ixx,
                Iyy=self.Iyy,
                Izz=self.Izz,
                mass=self.mass,
                velocity=self.velocity,
                alpha=alpha,
                modes=self.modes,
                polars=self.polars
            ))
        
        return None

    def read_config(self,file:str)->None:
        """
        Reads aero config file.
        """
        str_to_bool=lambda x:True if (x=="Y") else False

        with open(file,'r') as f:
            lines=f.readlines()
        lines=[line for line in lines if line[0]!="#" and line!="\n"]

        try:
            self.mass       = float(lines[0].split()[1])
            self.Xcg        = float(lines[1].split()[1])
            self.Ycg        = float(lines[2].split()[1])
            self.Zcg        = float(lines[3].split()[1])
            self.Ixx        = float(lines[4].split()[1])
            self.Iyy        = float(lines[5].split()[1])
            self.Izz        = float(lines[6].split()[1])
            self.velocity   = float(lines[7].split()[1])
            self.alpha0     = float(lines[8].split()[1])
            self.alpha1     = float(lines[9].split()[1])
            self.increment  = float(lines[10].split()[1])
            self.threads    = int(lines[11].split()[1])
            self.units      = lines[12].split()[1]
            self.polars     = str_to_bool(lines[13].split()[1])
            self.modes      = str_to_bool(lines[14].split()[1])
        except IndexError:
            print("Parameters must have a value assigned. (AERO_CONFIG.txt)")
            exit()

        return None

    def run(self,plane):
        #   Writes case files & adds filepath to case obj
        with ThreadPoolExecutor(max_workers=self.threads) as pool:
            pool.map(self.create_cases,self.cases)

        plane.cases=self.cases

        tasks=[(case,plane) for case in self.cases]
        with ThreadPoolExecutor(max_workers=self.threads) as pool:
            pool.map(self.analysis,tasks)

        if self.modes==True:
            plane.modes=self.read_modes()
        if self.polars==True:
            plane.polars=self.read_aero()

        return None

    def create_cases(self,case):
        case.write_aero_case()

        return None

    def analysis(self,tasks):
        case,plane=tasks

        cmd_str=f"load {plane.geom_file}\n"
        cmd_str+=f"case {case.case_file}\n"
        cmd_str+=f"mass {self.units}\n"
        cmd_str+="oper\no\nv\n\nx\n"

        results_file=f"results/{plane.name}-{str(case.alpha)}deg"
        
        if case.modes==False and case.polars==False:
            raise ValueError("No analysis type defined.")

        if case.modes==True:
            case.modes_results_file=f"{results_file}.eig"

            cmd_str+="\nmode\nN\nW\n"
            cmd_str+=f"{case.modes_results_file}\n\n"
        if case.polars==True:
            case.polars_results_file=f"{results_file}.polars"

            cmd_str+="oper\nx\nst\n"
            cmd_str+=f"{case.polars_results_file}\n"

        avl_cmd(cmd_str)

        return None

    def read_aero(self):
        polars=[]
        for case in self.cases:
            with open(case.polars_results_file,'r') as file:
                lines=file.readlines()

                case.Cl=float(lines[23].split()[2])
                case.Cd=float(lines[24].split()[2])
                case.Clb=float(lines[38].split()[8])
                case.Clp=float(lines[46].split()[5])
                case.spiral=float(lines[52].split()[6])
                
            polars.append((case.alpha,case.Cl,case.Cd,case.Clb,case.Clp,case.spiral))

        polars_df=pd.DataFrame(polars,columns=["Alpha (deg)","Cl","Cd","Clb","Clp","spiral"])

        return polars_df

    def read_modes(self):
        modes=[]
        for case in self.cases:
            with open(case.modes_results_file,'r') as file:
                lines=file.readlines()

                try:
                    case.dutch=tuple(map(float,lines[3].split()[1:]))
                    #case.ndutch=tuple(map(float,lines[4].split()[1:]))
                    case.roll=tuple(map(float,lines[5].split()[1:]))
                    #case.short=tuple(map(float,lines[6].split()[1:]))
                    #case.nshort=tuple(map(float,lines[7].split()[1:]))
                    #case.lateral=tuple(map(float,lines[8].split()[1:]))
                    #case.phugoid=tuple(map(float,lines[9].split()[1:]))
                    #case.nphugoid=tuple(map(float,lines[10].split()[1:]))
                except IndexError as e:
                    print(f"Eigenmode analysis/read failed: Case {case.modes_results_file}")
                    print(f"\n{e}")
                    exit()

            modes.append((
                case.alpha,
                case.dutch,
                #case.ndutch,
                case.roll
                #case.short,
                #case.nshort,
                #case.lateral,
                #case.phugoid,
                #case.nphugoid
                ))
            
        modes_df=pd.DataFrame(modes,columns=[
            "alpha",
            "dutch",
            #"-dutch",
            "roll"
            #"short",
            #"-short",
            #"lateral",
            #"phugoid",
            #"-phugoid"
            ])

        return modes_df

if __name__=="__main__":
    plane=Plane('aria3',geom_file='aria3.avl')

    aero=Aero("aero.config")
    aero.run(plane)

    print(plane.polars)
    print(plane.modes)