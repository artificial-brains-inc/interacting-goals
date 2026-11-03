#!/usr/bin/env python3
from __future__ import annotations
import math, os, random
from controller import Supervisor

def ef(n,d):
    try:return float(os.getenv(n,str(d)))
    except ValueError:return float(d)

def clamp(v,lo,hi): return max(lo,min(hi,float(v)))

def world_point(origin,R,local):
    x,y,z=local
    return [origin[0]+R[0]*x+R[1]*y+R[2]*z,origin[1]+R[3]*x+R[4]*y+R[5]*z,origin[2]+R[6]*x+R[7]*y+R[8]*z]

def update_wedge(field,length,cutoff):
    near=0.016; far=max(0.026,float(length)*math.tan(float(cutoff)))
    pts=[[0.030,-near,0],[0.030,near,0],[float(length),far,0],[float(length),-far,0]]
    for i,p in enumerate(pts):field.setMFVec3f(i,p)

def angle_deg(ax,ay,bx,by):
    an=math.hypot(ax,ay);bn=math.hypot(bx,by)
    if an<1e-9 or bn<1e-9:return 180.0
    c=max(-1.0,min(1.0,(ax*bx+ay*by)/(an*bn)))
    return math.degrees(math.acos(c))

def robot_heading(R):
    # World heading of the robot's local +X axis.
    return math.atan2(R[3],R[0])

r=Supervisor();dt=int(r.getBasicTimeStep());dt_s=max(1e-6,dt/1000.0)
robot=r.getFromDef('EPUCK_ROBOT');lure=r.getFromDef('PRECISION_LIGHT');spot=r.getFromDef('PRECISION_SPOT');coord=r.getFromDef('PRECISION_BEAM_COORD')
if None in (robot,lure,spot,coord):raise RuntimeError('precision DEF nodes missing')
rt=robot.getField('translation');lt=lure.getField('translation');lr=lure.getField('rotation');dirf=spot.getField('direction');ptsf=coord.getField('point')
INT=ef('AB_LURE_LIGHT_INTENSITY',8.5);BW=ef('AB_LURE_BEAM_WIDTH_RAD',0.045);CO=ef('AB_LURE_CUTOFF_RAD',0.070)
ALIGN=ef('AB_LURE_ALIGN_DEG',14.0);HOLD=ef('AB_LURE_ALIGN_HOLD_S',0.35);MIN_APPROACH=ef('AB_LURE_MIN_APPROACH_MPS',0.010);DWELL=ef('AB_LURE_MIN_DWELL_S',0.70);BLACKOUT=ef('AB_LURE_SWITCH_BLACKOUT_S',0.12);DEBUG=ef('AB_LURE_DEBUG_EVERY_S',0.50)
DIST=ef('AB_LURE_TARGET_DISTANCE_M',0.70)
# Mild front-biased turns plus true perpendicular 90-degree targets.
ANGLE_DEGS=[35.0,-35.0,90.0,-90.0]
SAFE_X=ef('AB_LURE_SAFE_X_M',1.45);SAFE_Y=ef('AB_LURE_SAFE_Y_M',1.05)
seed=os.getenv('AB_LURE_SEED','').strip();rng=random.Random(int(seed)) if seed else random.SystemRandom()
spot.getField('intensity').setSFFloat(INT);spot.getField('beamWidth').setSFFloat(BW);spot.getField('cutOffAngle').setSFFloat(CO)

def candidate_for(offset_deg):
    p=rt.getSFVec3f();R=robot.getOrientation();h=robot_heading(R)+math.radians(offset_deg)
    rawx=float(p[0])+DIST*math.cos(h);rawy=float(p[1])+DIST*math.sin(h)
    x=clamp(rawx,-SAFE_X,SAFE_X);y=clamp(rawy,-SAFE_Y,SAFE_Y)
    return x,y,math.hypot(x-float(p[0]),y-float(p[1]))

def choose_target(prev_offset=None):
    opts=[a for a in ANGLE_DEGS if prev_offset is None or abs(a-prev_offset)>1e-9]
    rng.shuffle(opts)
    # Prefer a target that remains at least 0.48 m away after arena clamping.
    for a in opts:
        x,y,d=candidate_for(a)
        if d>=0.48:return a,x,y,d
    a=opts[0];x,y,d=candidate_for(a);return a,x,y,d

current_offset,x0,y0,d0=choose_target(None);lt.setSFVec3f([x0,y0,0.085])
lastlog=-1e9;last_switch=-1e9;stable=0.0;switches=0;prev_d=None;pending=None;blackout_until=-1e9;next_offset=None
print(f'[AB-OBSTACLE-PRECISION] multi-angle switch mode | angles={ANGLE_DEGS} | first_offset={current_offset:+.0f}deg | align<={ALIGN:.1f}deg for {HOLD:.2f}s | target_distance={DIST:.2f}m | seed={seed or "system"}',flush=True)
while r.step(dt)!=-1:
    t=r.getTime();p=rt.getSFVec3f();R=robot.getOrientation()
    if pending is not None and t>=blackout_until:
        nx,ny=pending;lt.setSFVec3f([nx,ny,0.085]);spot.getField('intensity').setSFFloat(INT);pending=None;prev_d=None
        current_offset=float(next_offset);next_offset=None
        print(f'[AB-OBSTACLE-PRECISION][ON] offset={current_offset:+.0f}deg at=({nx:.3f},{ny:.3f})',flush=True)
    if pending is not None:
        if t-lastlog>=DEBUG:
            lastlog=t;print(f'[AB-OBSTACLE-PRECISION][STATE] t={t:.1f}s blackout=1 switches={switches}',flush=True)
        continue

    lp=lt.getSFVec3f();lx,ly,lz=float(lp[0]),float(lp[1]),float(lp[2])
    left=world_point(p,R,[0.015,0.031,0.020]);right=world_point(p,R,[0.015,-0.031,0.020])
    dl=math.dist(left,[lx,ly,lz]);dr=math.dist(right,[lx,ly,lz]);target=left if dl<=dr else right;which='LEFT' if dl<=dr else 'RIGHT'
    dx,dy,dz=target[0]-lx,target[1]-ly,target[2]-lz;h=math.hypot(dx,dy);a=math.atan2(dy,dx);lr.setSFRotation([0,0,1,a])
    n=max(1e-9,math.sqrt(h*h+dz*dz));dirf.setSFVec3f([h/n,0,dz/n]);update_wedge(ptsf,max(0.08,h),CO)

    tx,ty=lx-float(p[0]),ly-float(p[1]);fx,fy=R[0],R[3]
    ang=angle_deg(fx,fy,tx,ty);d=math.hypot(tx,ty)
    approach=0.0 if prev_d is None else (prev_d-d)/dt_s;prev_d=d
    locked=(ang<=ALIGN and approach>=MIN_APPROACH and t-last_switch>=DWELL)
    stable=stable+dt_s if locked else 0.0
    if stable>=HOLD:
        old=current_offset;stable=0.0;last_switch=t;switches+=1
        no,nx,ny,nd=choose_target(old)
        spot.getField('intensity').setSFFloat(0.0);lt.setSFVec3f([0,0,-2.0]);pending=(nx,ny);next_offset=no;blackout_until=t+BLACKOUT
        print(f'[AB-OBSTACLE-PRECISION][SWITCH] switch={switches} heading_error={ang:.2f}deg approach={approach:.3f}m/s offset={old:+.0f}->{no:+.0f}deg blackout={BLACKOUT:.2f}s new=({nx:.3f},{ny:.3f}) dist={nd:.3f}',flush=True)
        continue
    if t-lastlog>=DEBUG:
        lastlog=t;radius=h*math.tan(CO);print(f'[AB-OBSTACLE-PRECISION][STATE] t={t:.1f}s robot=({p[0]:.3f},{p[1]:.3f}) lamp=({lx:.3f},{ly:.3f}) offset={current_offset:+.0f}deg beam_to={which} heading_error={ang:.1f}deg approach={approach:.3f}m/s lock_s={stable:.2f}/{HOLD:.2f} beam_radius_at_side={radius:.3f} dL={dl:.3f} dR={dr:.3f} switches={switches}',flush=True)
