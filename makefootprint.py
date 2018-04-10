#file: makefootprint.py 
#purpose:helper function script for kicad footprint generation 
#author: Patrick Menschel (C)2018

#import re
#import math

import matplotlib.pyplot as plt
def plot_points(points,figname):
    pts = points.copy()
    pts.append(points[0])
    fig = plt.figure()
    ax = fig.add_subplot(111)
    line, = ax.plot([pt[0] for pt in pts],[pt[1] for pt in pts],lw=2,marker='o')
    for i in range(len(pts)-1):
        ax.annotate("PT{0} ({1},{2})".format(i,pts[i][0],pts[i][1]),xy=pts[i])
    ax.set_title(figname)    
    plt.show()
    return

def format_pad(padnum,padtype,padshape,posx,posy,sizex,sizey,layers):
    ret = "(pad {0} {1} {2} (at {3} {4}) (size {5} {6}) (layers {7}))".format(padnum, padtype, padshape,posx,posy,sizex,sizey," ".join(layers) )
    return ret

def get_posxy_for_span(pinnum,spanx,spany):
#dual in line method, first col downwards, second col upwards
    xpts = [-((((pinnum/2)-1) * spanx) / 2) + pin*spanx for pin in range(int(pinnum/2))]
    ypts = [(-0.5*spany) + spany*pin for pin in range(2)]
    pts = [(posx,posy) for posy in ypts for posx in xpts]#reversed dim loops
    return pts


def format_pads(pinnum,spanx,spany,padtype,padshape,sizex,sizey,layers):
    ret = ""
    for padnum,(posx,posy) in enumerate(get_posxy_for_span(pinnum,spanx,spany)):
        ret += "{0}\n".format(format_pad(padnum+1,padtype,padshape,posx,posy,sizex,sizey,layers))
    return ret

def get_outer_dimensions_of_pads(pads):
    minxy = [0,0]
    maxxy = [0,0]
    for pad in pads:
        padminxy,padmaxxy = pad.get_outer_dimensions()
#         print(padminxy,padmaxxy)
        minxy = list(min(minxy[i],padminxy[i]) for i in range(2))
        maxxy = list(max(maxxy[i],padmaxxy[i]) for i in range(2))
    return minxy,maxxy

def get_points_from_dimensions(dims):
    minxy,maxxy = dims
    pts = []
    pts.append((minxy[0],minxy[1]))
    pts.append((minxy[0],maxxy[1]))
    pts.append((maxxy[0],maxxy[1]))
    pts.append((maxxy[0],minxy[1]))
    return pts

def get_center_dimensions_of_pads(pads):
    minxy = [0,0]
    maxxy = [0,0]
    for pad in pads:
        padxypos = pad.get_xypos()
        minxy = list(min(minxy[i],padxypos[i]) for i in range(2))
        maxxy = list(max(maxxy[i],padxypos[i]) for i in range(2))
    return minxy,maxxy

def format_courtyard_lines(pads,package_dimensions,package_offset=0.25,linewidth=0.05,grid=0.01):
    points = []
    courtyard_lines = []
    grid_decimals = 2
    outer_pad_points = get_points_from_dimensions(get_outer_dimensions_of_pads(pads))
#     plot_points(outer_pad_points,"outer_pad_points")
    package_points = get_package_points(package_dimensions)
    
    outerpoints = []
    for i in range(4):
        thispt = [0,0]
        for j in range(2):
            if abs(outer_pad_points[i][j]) > abs(package_points[i][j]):#we know the points are aranged in the same manner/sector, so we check abs()
                thispt[j] = outer_pad_points[i][j]
#                 print("Pads win at Point {0} dim {1}".format(i,j))
            else:
                thispt[j] = package_points[i][j]
#                 print("Package wins at Point {0} dim {1}".format(i,j))
        outerpoints.append(thispt)
            
    for point in outerpoints:
        x,y = point
        if x < 0:
            thisx = round(x-package_offset-(grid/2),grid_decimals)
        else:
            thisx = round(x+package_offset+(grid/2),grid_decimals)
        if y < 0:
            thisy = round(y-package_offset-(grid/2),grid_decimals)
        else:
            thisy = round(y+package_offset+(grid/2),grid_decimals)
            
        points.append((thisx,thisy))
    
#     plot_points(package_points,"package_points")
#     
#     plot_points(points,"courtard after rounding")
#     
    for idx in range(len(points)-1):
        startpoint,endpoint = points[idx:idx+2]
        courtyard_lines.append(format_fpline(startpoint,endpoint,"F.CrtYd",linewidth))
    startpoint = points[-1] 
    endpoint = points[0]
    courtyard_lines.append(format_fpline(startpoint,endpoint,"F.CrtYd",linewidth))
    return courtyard_lines


def get_package_points(package_dimensions):
    points = []
    for x in [-0.5,0.5]:
        for y in [-0.5,0.5]:
            points.append((x*package_dimensions[0],y*package_dimensions[1]))
    rearrangedpoints = points.copy()
    rearrangedpoints[3] = points[2]
    rearrangedpoints[2] = points[3]
    return rearrangedpoints

def format_fab_lines(package_dimensions,linewidth=0.1):
    """ return the lines (as in newline ) for the fabrication layer (geometrical) lines
        @param package_dimensions: size of the component (x,y)
        @return: lines for the fabrication layer rectangle with cutted edge as pin 1 indicator
    """
    fab_lines = []
    # 4 points package rectangle
    
    points = get_package_points(package_dimensions) 
                    
    bevel = max(0.1,min(package_dimensions)*0.25)
    
    #alter first and last point to bevel
    points.append((points[0][0]+bevel,points[0][1]))
    points[0] = (points[0][0],points[0][1]+bevel)
    
#     plot_points(points,"fab lines")
    for idx in range(len(points)-1):
        startpoint,endpoint = points[idx:idx+2]
        fab_lines.append(format_fpline(startpoint,endpoint,"F.Fab",linewidth))
    startpoint = points[-1] 
    endpoint = points[0]
    fab_lines.append(format_fpline(startpoint,endpoint,"F.Fab",linewidth))
    return fab_lines


def format_silks_lines(pads,package_dimensions,distance_to_fablines=0.12,distance_to_pads=0.2,linewidth=0.12):
    silks_lines = []
    minxy,maxxy = get_outer_dimensions_of_pads(pads)
    cminxy,cmaxxy = get_center_dimensions_of_pads(pads)
    
    faby = [p[1] for p in get_package_points(package_dimensions)]
    fabminy = min(faby) 
    fabmaxy = max(faby)
#     print(minxy,fabminy,fabmaxy)
        
    startpoint = minxy[0]+(linewidth/2),min(minxy[1]-distance_to_pads,fabminy-distance_to_fablines)
    endpoint = cmaxxy[0],min(minxy[1]-distance_to_pads,fabminy-distance_to_fablines)
#     print(startpoint,endpoint)
    silks_lines.append(format_fpline(startpoint,endpoint,"F.SilkS",linewidth))
    
    startpoint = cminxy[0],max(maxxy[1]+distance_to_pads,fabmaxy+distance_to_fablines)
    endpoint = cmaxxy[0],max(maxxy[1]+distance_to_pads,fabmaxy+distance_to_fablines)
#     print(startpoint,endpoint)
    silks_lines.append(format_fpline(startpoint,endpoint,"F.SilkS",linewidth))
    return silks_lines

def format_3dmodel_lines(model3dname):
    lines = []
    sublines = []
    sublines.append("(at (xyz 0 0 0))")
    sublines.append("(scale (xyz 1 1 1))")
    sublines.append("(rotate (xyz 0 0 0))")
    lines.append(r"(model ${{KISYS3DMOD}}/{0}".format(model3dname))
    lines.extend("  {0}".format(subline) for subline in sublines)
    lines.append(")")
    return lines
    
    
def format_fpline(startpoint,endpoint,layer,width):
    ret =  "(fp_line (start {0}) (end {1}) (layer {2}) (width {3}))".format(" ".join("{:.2f}".format(dim) for dim in startpoint),
                                                                            " ".join("{:.2f}".format(dim) for dim in endpoint),
                                                                            layer,
                                                                            width)
    return ret        


def format_fp_text(text,posxy,layer,fontsize=(1,1),thickness=0.15,texttype="reference",angle=0):
    lines = []
    sublines = []
    poscontents = list(posxy)
    if angle:
        poscontents.append(angle)
    sublines.append("(effects (font (size {0}) (thickness {1:.2f})))".format(" ".join(["{:.2f}".format(I) for I in fontsize]),thickness))
    lines.append("(fp_text {0} {1} (at {2:}) (layer {3:})".format(texttype,text," ".join(["{:.2f}".format(I) for I in poscontents]),layer))
    lines.extend("  {0}".format(subline) for subline in sublines)
    lines.append(")")
    return lines


def calc_fab_ref_text_scaling(text,sizexy,charsize=(1,1)):
    textdim = (charsize[0]*len(text),charsize[1])
    scalingxy = [min(abs(sizexy[I]/textdim[I]),1) for I in range(len(sizexy))] 
    return scalingxy 
    

class footprint_pad():

    
    def __init__(self, padnum, xypos, sizexy, padtype, padshape,layers,drill=None):
        """ A class to represent a footprint and implement helper functions """
        self.padnum = padnum
        self.xypos = xypos
        self.sizexy = sizexy
        self.padtype = padtype
        self.padshape = padshape
        self.layers = layers       
        self.drill = drill
        
    def get_outer_dimensions(self):
        """ return the outer dimensions of a pad """
        minxy = list(self.xypos[I]-(self.sizexy[I]/2) for I in range(2))
        maxxy = list(self.xypos[I]+(self.sizexy[I]/2) for I in range(2))
        return minxy,maxxy
    
    def get_xypos(self):
        return self.xypos
    
    def format(self):
        #TODO make this nice later
        if self.padnum == None:
            padnum_str = "\"\""#escaped ""
        else:
            padnum_str = self.padnum
        if self.drill:
            ret = "(pad {0} {1} {2} (at {3}) (size {4}) (drill {5:.2f}) (layers {6}))".format(padnum_str,
                                                                                              self.padtype,
                                                                                              self.padshape,
                                                                                              " ".join("{0:.2f}".format(dim) for dim in self.xypos),
                                                                                              " ".join("{0:.2f}".format(dim) for dim in self.sizexy),
                                                                                              self.drill,
                                                                                              " ".join(self.layers) )
        else:
            ret = "(pad {0} {1} {2} (at {3}) (size {4}) (layers {5}))".format(padnum_str,
                                                                               self.padtype,
                                                                               self.padshape,
                                                                               " ".join("{0:.2f}".format(dim) for dim in self.xypos),
                                                                               " ".join("{0:.2f}".format(dim) for dim in self.sizexy),
                                                                               " ".join(self.layers) )
        return ret
    
    def get_area(self):
        if self.padshape == "rect":
            ret = self.sizexy[0]*self.sizexy[1]
        else:
            raise NotImplementedError("Shape not handled yet {0}".format(self.padshape))
        return ret 
        
        



class kicad_footprint:
    
     
    def __init__(self,name,desc,datasheet,pads,tedit="5AA01C76",layers=["F.Cu",],tags=["TDFN",],attr=["smd",],model3dname="Package_DFN_QFN.3dshapes/DFN-14-1EP_3x4.5mm_P0.65mm.wrl",package_dimensions=(1,1)):
        self.name = name
        self.desc = desc
        self.datasheet = datasheet
        self.pads = pads
        self.layers = layers
        self.tedit = tedit
        self.tags = tags
        self.attr = attr
        self.model3dname=model3dname
        self.package_dimensions = package_dimensions
        #self.pitch = re.compile("_P.*mm").findall(self.name)[0]#TODO: should we noc generate the name instead of RE the pitch out of it?!
        
    def format(self):
        fabrication_layer_value_distance_to_pads = 1#TODO: STUB - automate / calculate this value
        items = []#list of items to be placed in the format string
        items.append("module {0} (layer {1}) (tedit {2})".format(self.name," ".join(self.layers),self.tedit))#module definition line
        subitems = []
        subitems.append("(descr \"{0} ({1})\")".format(self.desc,self.datasheet))
        subitems.append("(tags \"{0}\")".format(" ".join(self.tags)))
        subitems.append("(attr {0})".format(" ".join(self.attr)))
        
        #Fab layer
        subitems.extend(format_fab_lines(package_dimensions=self.package_dimensions))        
        maxxy = get_outer_dimensions_of_pads(self.pads)[1]
        refpos = (0,maxxy[1]+fabrication_layer_value_distance_to_pads)
        subitems.extend(format_fp_text(text=self.name,posxy=refpos,layer="F.Fab",texttype="value"))
        #scaling = calc_text_scaling(text="REF**",sizexy=get_center_dimensions_of_pads(self.pads))#actually we're calculating %R but it translates to REF**
        scaling = calc_fab_ref_text_scaling(text="REF**",sizexy=self.package_dimensions)
#         print("Scaling {0}".format(scaling))
        angle=0
        if scaling[1] < scaling[0]:
            angle=90#use 90deg angle if the y dim is bigger than x, so we have more space
        fontsize=(min(scaling),)*2#keep aspect ratio
#         print("Fontsize {0}".format(fontsize))
        thickness = 0.15*fontsize[0]
#         thickness = 0.15*(self.package_dimensions[1]/self.package_dimensions[0])
#         print("package_dims {0} ratio {1}".format(self.package_dimensions,self.package_dimensions[1]/self.package_dimensions[0]))
#         print("Thickness {0}".format(thickness))
        subitems.extend(format_fp_text(text="%R",posxy=(0,0),layer="F.Fab",texttype="user",fontsize=fontsize,angle=angle,thickness=thickness))
        
        #SilkS layer
        minxy,maxxy = get_outer_dimensions_of_pads(self.pads)
        distance_to_pads = 1#TODO: write a function that returns the required distance to the pads, this is nasty
        refpos = (0,minxy[1]-distance_to_pads)
        subitems.extend(format_fp_text(text="REF**",posxy=refpos,layer="F.SilkS"))
        subitems.extend(format_silks_lines(self.pads,package_dimensions=self.package_dimensions))
        
        subitems.extend(format_courtyard_lines(self.pads,package_dimensions=self.package_dimensions))
#         subitems.extend(format_courtyard_lines(self.pads))#testing        
        subitems.extend([pad.format() for pad in self.pads])
        subitems.extend(format_3dmodel_lines(self.model3dname))
        [items.append("  {0}".format(subitem)) for subitem in subitems]
        ret = "({0}\n)".format("\n".join(items))
        return ret
    
    
    
def make_footprint_stmicro(N,E,X2,Y2,C,X,Y,V,EV,modulename,description,datasheet,centerpad,numthermalvias,package_dimensions,generate_thermalvias=True):
    """ make a kicad footprint from a st micro footprint description
        @param N: number of terminals(pads) in this footprint
        @param E: contact pitch
        @param X2: center pad width
        @param Y2: center pad length
        @param C: contact pad spacing
        @param X: contact pad width 
        @param Y: contact pad length
        @param V: thermal via diameter
        @param EV: thermal via pitch
        @param modulename: reference name that kicad uses
        @param description: description in datasheet
        @param datasheet: href to datasheet 
        @return:   a concated string that can be written to a footprint file
        
    """
    pads = []
    thermalvia_pads = []
    paste_pads = []    
    for idx,xypos in enumerate(get_posxy_for_span(pinnum=N,spanx=E,spany=C)):
        if idx >= N/2:
            padnum = N - idx + int(N/2) 
        else:
            padnum=idx+1        
        pads.append(footprint_pad(padnum,
                                  xypos=(xypos[1],xypos[0]),
                                  sizexy=(Y,X),
                                  padtype="smd", padshape="oval",layers = ["F.Cu","F.Paste","F.Mask"]))
    if centerpad and X2 and Y2:
        ep = footprint_pad(N+1,
                           xypos=(0,0),
                           sizexy=(Y2,X2),
                           padtype="smd", padshape="rect",layers = ["F.Cu","F.Mask"])
        pads.append(ep)
    if numthermalvias and V and EV:
        #TODO: calculate the number of thermal vias
        for padnum,xypos in enumerate(get_posxy_for_span(pinnum=numthermalvias,spanx=EV,spany=EV)):#TODO: how do we know the Number of thermalvias from spec sheet variables? 
            
            #add the thermal via
            diameter = min(Y2-EV,X2-EV)
            thermalvia_pads.append(footprint_pad(N+1,
                        xypos=(xypos[1],xypos[0]),
                        sizexy=(diameter,)*2,
                        padtype="thru_hole", padshape="circle",layers=["*.Cu",],drill=V))
            
        thermalvia_pads.append(footprint_pad(N+1,#FIXUP: one big thermal pad on the back.
                               xypos=(0,0),
                               sizexy=(Y2,X2),
                               padtype="smd", padshape="rect",layers = ["B.Cu",]))
        
        
        #shape the paste fields on the center pad around the thermalvias
        #we're forming a cross
        #1.calc a rect between all vias
        #    Y2 is the longest dim
        #    use the space X2 - 2V as shortest dim
        paste_pads.append(footprint_pad(
                          None,#No pad number
                          xypos=(0,0),
                          sizexy=(Y2,EV-V),#FIXME:not the diameter but the drill+margin, what is the margin?
                          padtype="smd",
                          padshape="rect",
                          layers = ["F.Paste",]))
        #add the other pads
        for padnum,xypos in enumerate(get_posxy_for_span(pinnum=numthermalvias/2,spanx=EV,spany=EV)):#TODO Check with higher pin count!
            paste_pads.append(footprint_pad(
                              None,#No pad number
                              xypos=xypos,#position is in between the vias
                              sizexy=(EV-V,X2-EV),
                              padtype="smd",
                              padshape="rect",
                              layers = ["F.Paste",]))
            
#         paste_coverage = sum([paste_pad.get_area() for paste_pad in paste_pads])/ep.get_area()
#         print("paste coverage {0:%}".format(paste_coverage))
    else:
        raise NotImplementedError("Not handling paste pad generation if there is no information about thermal vias")
        #shape the paste fields on the center pad without thermal vias
        
        
    if generate_thermalvias:        
        pads.extend(thermalvia_pads)
    pads.extend(paste_pads)    
    
    fp_obj = kicad_footprint(name=modulename,desc=description,datasheet=datasheet,pads=pads,tags=["TDFN","DFN","{0}mm".format(E)],
                             model3dname="Package_DFN_QFN.3dshapes/{0}.wrl".format(modulename.replace("_ThermalVias","")),
                             package_dimensions=package_dimensions)    
    return fp_obj.format()
        

if __name__ == "__main__":
    modulename = "TDFN-8-1EP_3x2mm_P0.5mm_EP1.80x1.65mm_ThermalVias"
    footprint = make_footprint_stmicro(N=8,
                                       E=0.5,
                                       X2=1.65,
                                       Y2=1.8,
                                       C=2.9,
                                       X=0.25,
                                       Y=0.85,
                                       V=0.3,
                                       EV=1.0,
                                       modulename=modulename,
                                       description="8-lead plastic dual flat, 2x3x0.75mm size, 0.5mm pitch",
                                       datasheet="http://ww1.microchip.com/downloads/en/DeviceDoc/8L_TDFN_2x3_MN_C04-0129E-MN.pdf",
                                       centerpad=True,
                                       numthermalvias=4,
                                       package_dimensions=(3,2),#swapped again portrait vs landscape
                                       )
    with open("{0}.kicad_mod".format(modulename),"w") as f:
        f.write(footprint)

    modulename = "TDFN-8-1EP_3x2mm_P0.5mm_EP1.80x1.65mm"
    footprint = make_footprint_stmicro(N=8,
                                       E=0.5,
                                       X2=1.65,
                                       Y2=1.8,
                                       C=2.9,
                                       X=0.25,
                                       Y=0.85,
                                       V=0.3,
                                       EV=1.0,
                                       modulename=modulename,
                                       description="8-lead plastic dual flat, 2x3x0.75mm size, 0.5mm pitch",
                                       datasheet="http://ww1.microchip.com/downloads/en/DeviceDoc/8L_TDFN_2x3_MN_C04-0129E-MN.pdf",
                                       centerpad=True,
                                       numthermalvias=4,
                                       package_dimensions=(3,2),
                                       generate_thermalvias=False,
                                       )
    with open("{0}.kicad_mod".format(modulename),"w") as f:
        f.write(footprint)



