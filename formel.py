import math

def afstand(coordA, coordB):
    latA, lonA = coordA
    latB, lonB = coordB
    R = 6372800
    
    phi1, phi2 = math.radians(latA), math.radians(latB)
    dphi = math.radians(latB - latA)
    dlambda = math.radians(lonB - lonA)
    
    a = math.sin(dphi/2)**2 + \
        math.cos(phi1) *math.cos(phi2)*math.sin(dlambda/2)**2
                        
    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1-a))
    afstand(coordA, coordB)



