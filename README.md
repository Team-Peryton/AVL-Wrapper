# AVL-automation
Surrey Team Peryton Heron IMechE UAS 2022 AVL automation program. Enables automatic tail sizing based on input aircraft geometry, and investigation of dihedral angle effects on stability and aerodynamic performance. 

A lose wrapping of the vortex lattice method [AVL](https://web.mit.edu/drela/Public/web/avl/) provides a means of scripting these tools.

The tail sizing segment has been validated against 2 flying UAVs and, given the CG is in the right place, suggests perfectly stable tail configurations.

## Usage
1. Install python (tested on 3.9.5)
2. Install packages in requirements.txt
   >pip install -r requirements.txt
3. Run avl-automation.py from the command line. For help:
   >py avl-automation.py -h
   
The following are required in the same directory as avl-automation.py:
- avl.exe (https://web.mit.edu/drela/Public/web/avl/)
- Config files (aero, dihedral, and tail).
- Input plane .avl file (see https://web.mit.edu/drela/Public/web/avl/avl_doc.txt for info; xflr5 can export AVL compatible files).
- aerofoil .dat files
   
If you get a seemingly random error it's likely because your input .avl plane file is formatted incorrectly. Raise an issue containing the .avl file and your config file(s) and I'll either fix the code or tell you how to fix your inputs :)

## Tail Sizing
- Suggests tail configurations based on input geometry to achieve a desired static margin.
- Works for convensional & V-tail configurations.
- Can be run in reverse i.e. input tail dimensions & output optimal CG location
- Anslysis considers only the horizontal tail plane (if convensional tail is selected). Vertical tail plane should be sized independently based on rudder and yaw stability requirements.

The program will generate tail configurations between limits given in the .config file and use AVL to calculate the neutral point of each. It then gives you a nice graph like the one below and prints possible tail configurations.

![image](https://user-images.githubusercontent.com/79290428/179372168-712e726d-9805-4b63-bebe-51a15cef5054.png)

**Fig. 1 - Static margins for tail areas and moment arms of tail configurations assessed**
```
Plane ID  Static Margin  Xnp (mm)  Xt (mm)  Span (mm)  Chord (mm)
     80           0.30     493.1   1000.0      801.0       150.0
     91           0.29     491.0   1062.0      731.0       137.0
     92           0.31     496.0   1124.0      731.0       137.0
```
The main 3 variables to consider when sizing the horizontal tail for longitudinal static stability are: tail moment arm, tail plane area, and CG position. In short, increasing the moment arm and area increase the longitudinal stability of the aircraft for a given CG because it moves the neutral point away from the CG. The neutral point is the point where, if the CG was placed on it, $C_M/\alpha=0$. Static margin $SM=x_{np}-x_{cg}$ and should be around 0.1 to 0.3.

![image](https://user-images.githubusercontent.com/79290428/179372590-fcfc5e14-8e66-4287-8e49-efd22b70ba7f.png)

**Fig. 2 - $C_M/\alpha$ curves for stable, neutral and unstable aircraft.**

The tail moment arm is likely restricted in some way because of structural constraints so there is a balance between the tail area and moment arm. Something that would be nice to add to the tail sizing program is calculating the required angle of incidence on the horizontal tail for a desired trim angle, but this can be done fairly easily within AVL itself given a bit of setup in the plane.avl file.

## Dihedral
- Generates wing configurations with varying dihedral angle with a set spanwise dihedral location. 
- Runs aero analysis, generating Cl and Cd polars, and relevant stability derivatives.
- AVL solution becomes very unstable as dihedral span location approaches tail sections in y.
- It would be nice to show the effect on dutch roll and roll subsidence modes but AVL is difficult to get to work with dynamic stability analyses.

![image](https://user-images.githubusercontent.com/79290428/179610350-5d2b92fd-5ed4-42a4-81e1-4591e40f4666.png)

**Fig. 3 - Dihedral angle effect on $C_L$, $C_D$, and stability derivatives.**

## Aero:
- Generate some quick aerodynamic coefficient polars, stability derivatives, and eigenmode frequencies and dampings for a range of angles of attack.
- Used in dihedral.py for calculating aerodynamic effect of dihedral angle.

## Limitations:
AVL is a vortex lattice method meaning it's good for early conceptual design and sizing but is not reliable for complete aerodynamic profiling and design because of the limitations of potential flow theory: 
- Flow seperation and stall are not predicted;
- No wake rollup is applied so tip losses are not well predicted;
- Wing/fuselage interactions are not captured;
- Solution is adversely affected if surfaces are placed directly downstream of the other due to trailing vortices influencing control points.
