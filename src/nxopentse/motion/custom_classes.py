
#Classes
#------------------------------------------------------------------------------------------------------------------------------------------------------
class MotionBodyProps:
    #static_elem = 123

    def __init__(self, object, name,mass,InertiaMoments, InertiaProducts, MassCenter,InertiaCSYS_Origin, InertiaCSYS_Vector_X, InertiaCSYS_Vector_Y):
        self.object = object                                #the object to create the motion body of
        self.name = name
        self.mass = mass
        self.InertiaMoments = InertiaMoments                #[Ixx, Iyy, Izz]
        self.InertiaProducts =  InertiaProducts             #[Ixy, Ixz, Iyz]
        self.MassCenter = MassCenter                        #[X_mass,Y_mass,Z_mass]
        self.InertiaCSYS_Origin = InertiaCSYS_Origin        #[X_inertia,Y_inertia,Z_inertia]
        self.InertiaCSYS_Vector_X = InertiaCSYS_Vector_X    #[X,Y,Z] - X vector components
        self.InertiaCSYS_Vector_Y = InertiaCSYS_Vector_Y    #[X,Y,Z] - Y vector components