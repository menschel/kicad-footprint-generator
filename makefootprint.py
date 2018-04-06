#file: makefootprint.py 
#purpose:helper function script for kicad footprint generation 
#author: Patrick Menschel (C)2018

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


def get_center_dimensions_of_pads(pads):
    minxy = [0,0]
    maxxy = [0,0]
    for pad in pads:
        padxypos = pad.get_xypos()
        minxy = list(min(minxy[i],padxypos[i]) for i in range(2))
        maxxy = list(max(maxxy[i],padxypos[i]) for i in range(2))
    return minxy,maxxy

def format_courtyard_lines(pads,distance_to_pads=0.25):
    points = []
    courtyard_lines = []
    minxy,maxxy = get_outer_dimensions_of_pads(pads)
    spanx,spany = list(zip(minxy,maxxy))
    for x in spanx:
        for y in spany:
            if x < 0:
                thisx = x-distance_to_pads
            else:
                thisx = x+distance_to_pads
            if y < 0:
                thisy = y-distance_to_pads
            else:
                thisy = y+distance_to_pads
            points.append((thisx,thisy))
    #we have to swap points for this to draw correct
    newpoints = points.copy()
    newpoints[3] = points[2]
    newpoints[2] = points[3]
    
    points = newpoints
    
    for idx in range(len(points)-1):
        startpoint,endpoint = points[idx:idx+2]
        courtyard_lines.append(format_fpline(startpoint,endpoint,"F.CrtYd",0.05))
    startpoint = points[-1] 
    endpoint = points[0]
    courtyard_lines.append(format_fpline(startpoint,endpoint,"F.CrtYd",0.05))
    return courtyard_lines


def format_fab_lines(pads,distance_to_pad_center=0):
    points = []
    fab_lines = []
    minxy,maxxy = get_center_dimensions_of_pads(pads)
    spanx,spany = list(zip(minxy,maxxy))
    
    for x in spanx:
        for y in spany:
            if x < 0:
                thisx = x-distance_to_pad_center
            else:
                thisx = x+distance_to_pad_center
            if y < 0:
                thisy = y-distance_to_pad_center
            else:
                thisy = y+distance_to_pad_center
            points.append((thisx,thisy))

    maxx = 0
    maxy = 0
    for point in points:
        maxx = max(abs(point[0]),maxx)
        maxy = max(abs(point[1]),maxy)
                
    #print(sizexy)
    bevel = min(1,min(maxx,maxy)*0.25)
    
    #alter first and last point to bevel
    points.append((points[0][0],points[0][1]+bevel))
    points[0] = (points[0][0]+bevel,points[0][1])
    
    #we have to swap points for this to draw correct
    newpoints = points.copy()
    newpoints[1] = points[2]
    newpoints[2] = points[3]
    newpoints[3] = points[1]
    points = newpoints
    
    for idx in range(len(points)-1):
        startpoint,endpoint = points[idx:idx+2]
        fab_lines.append(format_fpline(startpoint,endpoint,"F.Fab",0.1))
    startpoint = points[-1] 
    endpoint = points[0]
    fab_lines.append(format_fpline(startpoint,endpoint,"F.Fab",0.1))
    return fab_lines


def format_silks_lines(pads,distance_to_pads=0.1):
    silks_lines = []
    points = []
    minxy,maxxy = get_outer_dimensions_of_pads(pads)
    cminxy,cmaxxy = get_center_dimensions_of_pads(pads)
    
    startpoint = minxy[0]-distance_to_pads,minxy[1]-distance_to_pads
    endpoint = cmaxxy[0],minxy[1]-distance_to_pads
    silks_lines.append(format_fpline(startpoint,endpoint,"F.SilkS",0.12))
    
    startpoint = cminxy[0],maxxy[1]+distance_to_pads
    endpoint = cmaxxy[0],maxxy[1]+distance_to_pads
    silks_lines.append(format_fpline(startpoint,endpoint,"F.SilkS",0.12))
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
    sublines.append("(effects (font (size {0}) (thickness {1})))".format(" ".join(["{:.2f}".format(I) for I in fontsize]),thickness))
    lines.append("(fp_text {0} {1} (at {2}) (layer {3})".format(texttype,text," ".join(["{:.2f}".format(I) for I in poscontents]),layer))
    lines.extend("  {0}".format(subline) for subline in sublines)
    lines.append(")")
    return lines


def calc_text_scaline(text,sizexy,charsize=(1,1)):
    minxy,maxx = sizexy
    spanxy = list(zip(maxx,minxy))
    calcxy = list([abs(dim[1])+abs(dim[0]) for dim in spanxy])
    textdim = (charsize[0]*len(text),charsize[1])
    scalingxy = [min(abs(calcxy[I]/textdim[I]),1) for I in range(len(sizexy))] 
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
        
        



class kicad_footprint:
    
     
    def __init__(self,name,desc,datasheet,pads,tedit="5AA01C76",layers=["F.Cu",],tags=["VDN",],attr=["smd",],model3dname="Package_DFN_QFN.3dshapes/DFN-14-1EP_3x4.5mm_P0.65mm.wrl"):
        self.name = name
        self.desc = desc
        self.datasheet = datasheet
        self.pads = pads
        self.layers = layers
        self.tedit = tedit
        self.tags = tags
        self.attr = attr
        self.model3dname=model3dname
        
    def format(self):
        items = []#list of items to be placed in the format string
        items.append("module {0} (layer {1}) (tedit {2})".format(self.name," ".join(self.layers),self.tedit))#module definition line
        subitems = []
        subitems.append("(descr \"{0} ({1})\")".format(self.desc,self.datasheet))
        subitems.append("(tags \"{0}\")".format(" ".join(self.tags)))
        subitems.append("(attr {0})".format(" ".join(self.attr)))
        subitems.extend(format_fab_lines(self.pads))
        
        #Fab layer
        minxy,maxxy = get_outer_dimensions_of_pads(self.pads)
        distance_to_pads = 1#TODO: write a function that returns the required distance to the pads
        refpos = (0,maxxy[1]+distance_to_pads)
        subitems.extend(format_fp_text(text=self.name,posxy=refpos,layer="F.Fab",texttype="value"))#why is this name not showing ?
        scaling = calc_text_scaline(text="REF**",sizexy=get_center_dimensions_of_pads(self.pads))#actually we're calculating %R but it translates to REF**
        angle=0
        if scaling[1] < scaling[0]:
            angle=90
        fontsize=(min(scaling),)*2
        subitems.extend(format_fp_text(text="%R",posxy=(0,0),layer="F.Fab",texttype="user",fontsize=fontsize,angle=angle))
        
        #SilkS layer
        minxy,maxxy = get_outer_dimensions_of_pads(self.pads)
        distance_to_pads = 1#TODO: write a function that returns the required distance to the pads, this is nasty
        refpos = (0,minxy[1]-distance_to_pads)
        subitems.extend(format_fp_text(text="REF**",posxy=refpos,layer="F.SilkS"))
        subitems.extend(format_silks_lines(self.pads))
        
        subitems.extend(format_courtyard_lines(self.pads))        
        subitems.extend([pad.format() for pad in self.pads])
        subitems.extend(format_3dmodel_lines(self.model3dname))
        [items.append("  {0}".format(subitem)) for subitem in subitems]
        ret = "({0}\n)".format("\n".join(items))
        return ret
    
    
    
def make_footprint_stmicro(N,E,X2,Y2,C,X,Y,V,EV,modulename,description,datasheet,centerpad,numthermalvias):
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
    for padnum,xypos in enumerate(get_posxy_for_span(pinnum=N,spanx=E,spany=C)):        
        pads.append(footprint_pad(padnum+1,
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
        #TODO: either calculate the number of thermal vias
        for padnum,xypos in enumerate(get_posxy_for_span(pinnum=numthermalvias,spanx=EV,spany=EV)):#TODO: how do we know the Number of thermalvias from spec sheet variables? 
            
            #add the thermal via
            diameter = min(Y2-EV,X2-EV)
            thermalvia_pads.append(footprint_pad(N+1,
                        xypos=(xypos[1],xypos[0]),
                        sizexy=(diameter,)*2,
                        padtype="thru_hole", padshape="circle",layers=["*.Cu","*.Mask"],drill=V))
            
            #add the thermal pad to the back
            thermalvia_pads.append(footprint_pad(N+1,
                        xypos=(xypos[1],xypos[0]),
                        sizexy=(diameter,)*2,
                        padtype="smd", padshape="rect",layers = ["B.Cu","B.Mask"]))#TODO: does this need to be rectangle?!
        
        
        #shape the paste fields on the center pad around the thermalvias
        #we're forming a cross
        #1.calc a rect between all vias
        #    Y2 is the longest dim
        #    use the space X2 - 2V as shortest dim
        paste_pads.append(footprint_pad(
                          None,#No pad number
                          xypos=(0,0),
                          sizexy=(Y2,EV-diameter),
                          padtype="smd",
                          padshape="rect",
                          layers = ["F.Paste",]))
        #add the other pads
        for padnum,xypos in enumerate(get_posxy_for_span(pinnum=numthermalvias/2,spanx=EV,spany=EV)):#TODO Check with higher pin count!
            paste_pads.append(footprint_pad(
                              None,#No pad number
                              xypos=xypos,#position is in between the vias
                              sizexy=(EV-diameter,X2-EV),
                              padtype="smd",
                              padshape="rect",
                              layers = ["F.Paste",]))
            
        
    else:
        pass
        #shape the paste fields on the center pad
    pads.extend(thermalvia_pads)
    pads.extend(paste_pads)    
    
    fp_obj = kicad_footprint(name=modulename,desc=description,datasheet=datasheet,pads=pads,tags=["VDFN","DFN","0.65mm"],
                             model3dname="Package_DFN_QFN.3dshapes/{0}.wrl".format(modulename))    
    return fp_obj.format()
        

if __name__ == "__main__":
    footprint = make_footprint_stmicro(N=8,
                                       E=0.5,
                                       X2=1.65,
                                       Y2=1.8,
                                       C=2.9,
                                       X=0.25,
                                       Y=0.85,
                                       V=0.3,
                                       EV=1.0,
                                       modulename="TDFN-8-1EP_3x2mm_Pitch0.5mm_EP1.80x1.65mm",
                                       description="8-lead plastic dual flat, 2x3x0.75mm size, 0.5mm pitch",
                                       datasheet="http://ww1.microchip.com/downloads/en/DeviceDoc/8L_TDFN_2x3_MN_C04-0129E-MN.pdf",
                                       centerpad=True,
                                       numthermalvias=4,
                                       )
    with open("TDFN-8-1EP_3x2mm_Pitch0.5mm_EP1.80x1.65mm_ThermalVias.kicad_mod","w") as f:
        f.write(footprint)




